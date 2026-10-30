"""
DetectBehaviorPatterns Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result

from processing.application.dto.conversation_analysis_dto import (
    ConversationPatternDTO,
)
from processing.application.mappers.conversation_analysis_mapper import (
    ConversationAnalysisMapper,
)
from processing.domain.ports.behavior_analyzer_port import BehaviorAnalyzerPort


@dataclass(frozen=True)
class DetectBehaviorPatternsCommand(Command):
    """Command requesting direct behavior pattern detection over a set of message turns."""

    messages: tuple[dict[str, str], ...]
    conversation_id: str = ""


class DetectBehaviorPatternsHandler(CommandHandler[DetectBehaviorPatternsCommand, tuple[ConversationPatternDTO, ...]]):
    """Handler executing DetectBehaviorPatternsCommand."""

    def __init__(self, behavior_analyzer_port: BehaviorAnalyzerPort) -> None:
        self._analyzer = behavior_analyzer_port

    async def handle(self, command: DetectBehaviorPatternsCommand) -> Result[tuple[ConversationPatternDTO, ...]]:
        """Execute pattern detection over message list."""
        if not command.messages:
            return Result.fail(Error("VALIDATION_ERROR", "Messages list cannot be empty"))

        raw_msgs = [dict(m) for m in command.messages]
        _, patterns = await self._analyzer.analyze_messages(raw_msgs, conversation_id=command.conversation_id)
        pat_dtos = tuple(ConversationAnalysisMapper.to_pattern_dto(p) for p in patterns)

        return Result.ok(pat_dtos)
