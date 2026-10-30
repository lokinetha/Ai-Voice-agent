"""
AnalyzeConversation Command and CommandHandler.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import ConversationId, WorkspaceId

from processing.application.dto.conversation_analysis_dto import (
    ConversationAnalysisDTO,
)
from processing.application.mappers.conversation_analysis_mapper import (
    ConversationAnalysisMapper,
)
from processing.domain.factories.conversation_analysis_factory import (
    ConversationAnalysisFactory,
)
from processing.domain.ports.behavior_analyzer_port import BehaviorAnalyzerPort
from processing.domain.ports.conversation_reader_port import ConversationReaderPort
from processing.domain.ports.transcript_provider_port import TranscriptProviderPort
from processing.domain.repositories.conversation_analysis_repository import (
    ConversationAnalysisRepository,
)
from processing.domain.value_objects.analysis_result import AnalysisResult


@dataclass(frozen=True)
class AnalyzeConversationCommand(Command):
    """Command requesting behavioral analysis of a completed conversation."""

    workspace_id: str
    conversation_id: str


class AnalyzeConversationHandler(CommandHandler[AnalyzeConversationCommand, ConversationAnalysisDTO]):
    """Handler executing AnalyzeConversationCommand using ports and rule-based behavior analyzer."""

    def __init__(
        self,
        analysis_repository: ConversationAnalysisRepository,
        conversation_reader_port: ConversationReaderPort,
        transcript_provider_port: TranscriptProviderPort,
        behavior_analyzer_port: BehaviorAnalyzerPort,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repo = analysis_repository
        self._reader = conversation_reader_port
        self._transcript = transcript_provider_port
        self._analyzer = behavior_analyzer_port
        self._uow = unit_of_work

    async def handle(self, command: AnalyzeConversationCommand) -> Result[ConversationAnalysisDTO]:
        """Execute conversation analysis pipeline."""
        if not command.workspace_id or not command.conversation_id:
            return Result.fail(Error("VALIDATION_ERROR", "workspace_id and conversation_id required"))

        conv_data = await self._reader.get_completed_conversation(command.conversation_id)
        if conv_data is None:
            return Result.fail(
                Error("NOT_FOUND", f"Completed conversation '{command.conversation_id}' not found")
            )

        messages = await self._transcript.get_transcript_messages(command.conversation_id)
        if not messages:
            messages = [
                {
                    "id": m.id,
                    "participant_id": m.participant_id,
                    "role": m.role,
                    "content": m.content,
                    "sequence_number": m.sequence_number,
                }
                for m in conv_data.messages
            ]

        analysis = ConversationAnalysisFactory.create(
            workspace_id=WorkspaceId(command.workspace_id),
            conversation_id=ConversationId(command.conversation_id),
        )

        analysis.start()

        t0 = time.time()
        try:
            signals, patterns = await self._analyzer.analyze_messages(
                messages, conversation_id=command.conversation_id
            )

            for sig in signals:
                analysis.add_signal(sig)

            for pat in patterns:
                analysis.add_pattern(pat)

            exec_time = time.time() - t0

            analysis.complete(
                AnalysisResult(
                    signals_count=len(signals),
                    patterns_count=len(patterns),
                    execution_time_seconds=exec_time,
                    summary=f"Extracted {len(signals)} behavioral signals and {len(patterns)} patterns",
                )
            )
        except Exception as err:
            analysis.fail(str(err))

        async with self._uow:
            await self._repo.save(analysis)
            await self._uow.commit()

        return Result.ok(ConversationAnalysisMapper.to_dto(analysis))
