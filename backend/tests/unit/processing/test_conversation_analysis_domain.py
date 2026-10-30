"""
Unit tests for ConversationAnalysis Domain Layer — Aggregate Root, Entities, Value Objects,
Events, Factory, and Invariants.
"""

from __future__ import annotations

import unittest

from processing.domain.entities.behavioral_signal import BehavioralSignal
from processing.domain.entities.conversation_pattern import ConversationPattern
from processing.domain.events.analysis_completed import AnalysisCompleted
from processing.domain.events.analysis_failed import AnalysisFailed
from processing.domain.events.analysis_started import AnalysisStarted
from processing.domain.events.behavioral_pattern_detected import (
    BehavioralPatternDetected,
)
from processing.domain.factories.conversation_analysis_factory import (
    ConversationAnalysisFactory,
)
from processing.domain.value_objects.analysis_result import AnalysisResult
from processing.domain.value_objects.analysis_status import AnalysisStatusType
from processing.domain.value_objects.behavioral_category import (
    BehavioralCategory,
)
from processing.domain.value_objects.confidence_score import ConfidenceScore
from shared.kernel.value_objects import ConversationId, EntityId, WorkspaceId


class TestConversationAnalysisDomain(unittest.TestCase):
    """Tests for ConversationAnalysis domain components and rules."""

    def test_factory_creates_analysis(self) -> None:
        analysis = ConversationAnalysisFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            conversation_id=ConversationId("conv-100"),
        )

        self.assertEqual(analysis.status.value, AnalysisStatusType.PENDING)
        self.assertEqual(len(analysis.signals), 0)
        self.assertEqual(len(analysis.patterns), 0)

    def test_analysis_lifecycle_start_add_signals_complete(self) -> None:
        analysis = ConversationAnalysisFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            conversation_id=ConversationId("conv-100"),
        )
        analysis.clear_events()

        # Start
        start_res = analysis.start()
        self.assertTrue(start_res.is_success)
        self.assertEqual(analysis.status.value, AnalysisStatusType.IN_PROGRESS)
        self.assertTrue(any(isinstance(e, AnalysisStarted) for e in analysis.domain_events))

        # Add signal
        signal = BehavioralSignal(
            id=EntityId(),
            category=BehavioralCategory.objection_handling(),
            signal_type="PRICE_OBJECTION",
            description="Client mentioned price is too high",
            confidence=ConfidenceScore(0.92),
            source_message_id="msg-1",
            evidence_text="It is too expensive",
        )
        sig_res = analysis.add_signal(signal)
        self.assertTrue(sig_res.is_success)
        self.assertEqual(len(analysis.signals), 1)

        # Add pattern
        pattern = ConversationPattern(
            id=EntityId(),
            pattern_name="Price Resistance",
            category=BehavioralCategory.objection_handling(),
            description="Recurrent price objection",
            frequency=2,
            confidence=ConfidenceScore(0.88),
            sample_signal_ids=(str(signal.id.value),),
            conversation_references=("conv-100",),
        )
        analysis.clear_events()
        pat_res = analysis.add_pattern(pattern)
        self.assertTrue(pat_res.is_success)
        self.assertEqual(len(analysis.patterns), 1)
        self.assertTrue(any(isinstance(e, BehavioralPatternDetected) for e in analysis.domain_events))

        # Complete
        analysis.clear_events()
        comp_res = analysis.complete(
            AnalysisResult(
                signals_count=1,
                patterns_count=1,
                execution_time_seconds=0.15,
                summary="Analysis successful",
            )
        )
        self.assertTrue(comp_res.is_success)
        self.assertEqual(analysis.status.value, AnalysisStatusType.COMPLETED)
        self.assertTrue(any(isinstance(e, AnalysisCompleted) for e in analysis.domain_events))

    def test_fail_analysis(self) -> None:
        analysis = ConversationAnalysisFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            conversation_id=ConversationId("conv-100"),
        )
        analysis.start()
        analysis.clear_events()

        fail_res = analysis.fail("Analysis error")
        self.assertTrue(fail_res.is_success)
        self.assertEqual(analysis.status.value, AnalysisStatusType.FAILED)
        self.assertTrue(any(isinstance(e, AnalysisFailed) for e in analysis.domain_events))

    def test_signal_traceability_and_confidence_invariants(self) -> None:
        with self.assertRaises(ValueError):
            BehavioralSignal(
                id=EntityId(),
                category=BehavioralCategory.general(),
                signal_type="TYPE",
                description="desc",
                confidence=ConfidenceScore(1.5),  # Invalid score > 1.0
                source_message_id="msg-1",
            )

        with self.assertRaises(ValueError):
            BehavioralSignal(
                id=EntityId(),
                category=BehavioralCategory.general(),
                signal_type="TYPE",
                description="desc",
                confidence=ConfidenceScore(0.9),
                source_message_id="",  # Empty source message ID violates traceability
            )


if __name__ == "__main__":
    unittest.main()
