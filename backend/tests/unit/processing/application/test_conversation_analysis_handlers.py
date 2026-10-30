"""
Unit tests for ConversationAnalysis CQRS Handlers.
"""

from __future__ import annotations

import asyncio
import unittest
from typing import Self

from processing.application.commands.aggregate_behavior_patterns import (
    AggregateBehaviorPatternsCommand,
    AggregateBehaviorPatternsHandler,
)
from processing.application.commands.analyze_conversation import (
    AnalyzeConversationCommand,
    AnalyzeConversationHandler,
)
from processing.application.commands.detect_behavior_patterns import (
    DetectBehaviorPatternsCommand,
    DetectBehaviorPatternsHandler,
)
from processing.application.queries.get_behavior_patterns import (
    GetBehaviorPatternsHandler,
    GetBehaviorPatternsQuery,
)
from processing.application.queries.get_conversation_analysis import (
    GetConversationAnalysisHandler,
    GetConversationAnalysisQuery,
)
from processing.domain.entities.conversation_analysis import (
    ConversationAnalysis,
)
from processing.domain.ports.conversation_reader_port import (
    ConversationAnalysisDataDTO,
    ConversationMessageData,
    ConversationReaderPort,
)
from processing.domain.ports.transcript_provider_port import (
    TranscriptProviderPort,
)
from processing.domain.repositories.conversation_analysis_repository import (
    ConversationAnalysisRepository,
)
from processing.infrastructure.adapters.deterministic_behavior_analyzer_adapter import (
    DeterministicBehaviorAnalyzerAdapter,
)
from shared.kernel.domain_event import DomainEvent
from shared.kernel.specification import Specification
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import (
    ConversationId,
    EntityId,
    WorkspaceId,
)


class InMemoryConversationAnalysisRepository(ConversationAnalysisRepository):
    """In-memory test double for ConversationAnalysisRepository."""

    def __init__(self) -> None:
        self.store: dict[str, ConversationAnalysis] = {}

    async def get_by_id(self, id: EntityId) -> ConversationAnalysis | None:
        return self.store.get(str(id.value))

    async def find_by_workspace(self, workspace_id: WorkspaceId) -> list[ConversationAnalysis]:
        return [a for a in self.store.values() if a.workspace_id == workspace_id]

    async def find_by_conversation(self, conversation_id: ConversationId) -> list[ConversationAnalysis]:
        return [a for a in self.store.values() if a.conversation_id == conversation_id]

    async def save(self, aggregate: ConversationAnalysis) -> None:
        self.store[str(aggregate.id.value)] = aggregate

    async def delete(self, aggregate: ConversationAnalysis) -> None:
        self.store.pop(str(aggregate.id.value), None)

    async def find(self, spec: Specification[ConversationAnalysis]) -> list[ConversationAnalysis]:
        return [a for a in self.store.values() if spec.is_satisfied_by(a)]

    async def count(self, spec: Specification[ConversationAnalysis]) -> int:
        return len(await self.find(spec))


class MockConversationReader(ConversationReaderPort):
    """Test double for ConversationReaderPort."""

    def __init__(self, data_map: dict[str, ConversationAnalysisDataDTO] | None = None) -> None:
        self.data_map = data_map or {}

    async def get_completed_conversation(
        self, conversation_id: str
    ) -> ConversationAnalysisDataDTO | None:
        return self.data_map.get(conversation_id)


class MockTranscriptProvider(TranscriptProviderPort):
    """Test double for TranscriptProviderPort."""

    async def get_transcript_messages(self, conversation_id: str) -> list[dict]:
        return [
            {
                "id": "msg-1",
                "participant_id": "cust-1",
                "role": "CUSTOMER",
                "content": "Can you explain how this works?",
                "sequence_number": 1,
            },
            {
                "id": "msg-2",
                "participant_id": "cust-1",
                "role": "CUSTOMER",
                "content": "It is too expensive for our budget.",
                "sequence_number": 2,
            },
        ]


class DummyUnitOfWork(UnitOfWork):
    """Test double for UnitOfWork."""

    def __init__(self) -> None:
        self.committed = False

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        pass

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        pass

    def collect_events(self) -> list[DomainEvent]:
        return []


class TestConversationAnalysisHandlers(unittest.TestCase):
    """Tests for ConversationAnalysis CQRS Handlers."""

    def setUp(self) -> None:
        self.repo = InMemoryConversationAnalysisRepository()
        self.uow = DummyUnitOfWork()

        self.mock_reader = MockConversationReader(
            {
                "conv-1": ConversationAnalysisDataDTO(
                    conversation_id="conv-1",
                    workspace_id="ws-1",
                    agent_id="ag-1",
                    status="ENDED",
                    messages=(
                        ConversationMessageData(
                            id="msg-1",
                            participant_id="cust-1",
                            role="CUSTOMER",
                            content="Can you explain how this works?",
                            sequence_number=1,
                        ),
                        ConversationMessageData(
                            id="msg-2",
                            participant_id="cust-1",
                            role="CUSTOMER",
                            content="It is too expensive for our budget.",
                            sequence_number=2,
                        ),
                    ),
                )
            }
        )
        self.mock_transcript = MockTranscriptProvider()
        self.analyzer = DeterministicBehaviorAnalyzerAdapter()

    def test_analyze_conversation_handler(self) -> None:
        async def run() -> None:
            handler = AnalyzeConversationHandler(
                analysis_repository=self.repo,
                conversation_reader_port=self.mock_reader,
                transcript_provider_port=self.mock_transcript,
                behavior_analyzer_port=self.analyzer,
                unit_of_work=self.uow,
            )

            cmd = AnalyzeConversationCommand(workspace_id="ws-1", conversation_id="conv-1")
            res = await handler.handle(cmd)

            self.assertTrue(res.is_success)
            self.assertEqual(res.value.status, "COMPLETED")
            self.assertGreater(len(res.value.signals), 0)
            self.assertGreater(len(res.value.patterns), 0)

            # Query analysis
            get_h = GetConversationAnalysisHandler(self.repo)
            get_res = await get_h.handle(GetConversationAnalysisQuery(analysis_id=res.value.id))
            self.assertTrue(get_res.is_success)
            self.assertEqual(get_res.value.id, res.value.id)

        asyncio.run(run())

    def test_detect_behavior_patterns_handler(self) -> None:
        async def run() -> None:
            handler = DetectBehaviorPatternsHandler(self.analyzer)
            cmd = DetectBehaviorPatternsCommand(
                messages=(
                    {"id": "m1", "role": "CUSTOMER", "content": "How much does it cost?"},
                    {"id": "m2", "role": "CUSTOMER", "content": "Can we sign the contract now?"},
                ),
                conversation_id="conv-1",
            )
            res = await handler.handle(cmd)

            self.assertTrue(res.is_success)
            self.assertGreater(len(res.value), 0)

        asyncio.run(run())

    def test_aggregate_behavior_patterns_handler(self) -> None:
        async def run() -> None:
            analyze_h = AnalyzeConversationHandler(
                self.repo, self.mock_reader, self.mock_transcript, self.analyzer, self.uow
            )
            await analyze_h.handle(AnalyzeConversationCommand(workspace_id="ws-agg", conversation_id="conv-1"))

            agg_h = AggregateBehaviorPatternsHandler(self.repo)
            agg_res = await agg_h.handle(AggregateBehaviorPatternsCommand(workspace_id="ws-agg"))
            self.assertTrue(agg_res.is_success)
            self.assertGreater(len(agg_res.value), 0)

            pat_h = GetBehaviorPatternsHandler(self.repo)
            pat_res = await pat_h.handle(GetBehaviorPatternsQuery(workspace_id="ws-agg"))
            self.assertTrue(pat_res.is_success)
            self.assertGreater(len(pat_res.value), 0)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
