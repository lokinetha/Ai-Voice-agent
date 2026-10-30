"""
ConversationAnalysis Aggregate Root for Processing Bounded Context.

Manages the lifecycle and findings of analyzing a completed conversation.
Analysis is strictly READ-ONLY with respect to Conversation and Playbook aggregates.
"""

from __future__ import annotations

from collections.abc import Sequence

from shared.kernel.aggregate_root import AggregateRoot
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import (
    ConversationId,
    EntityId,
    Timestamp,
    WorkspaceId,
)

from processing.domain.entities.behavioral_signal import BehavioralSignal
from processing.domain.entities.conversation_pattern import ConversationPattern
from processing.domain.events.analysis_completed import AnalysisCompleted
from processing.domain.events.analysis_failed import AnalysisFailed
from processing.domain.events.analysis_started import AnalysisStarted
from processing.domain.events.behavioral_pattern_detected import (
    BehavioralPatternDetected,
)
from processing.domain.value_objects.analysis_result import AnalysisResult
from processing.domain.value_objects.analysis_status import AnalysisStatus


class ConversationAnalysis(AggregateRoot[EntityId]):
    """ConversationAnalysis Aggregate Root.

    Enforces invariants:
    - Analysis status transitions (PENDING -> IN_PROGRESS -> COMPLETED / FAILED).
    - Every detected signal MUST include a confidence score and source message reference.
    - Preserves traceability from patterns back to signals and conversations.
    - Analysis is strictly READ-ONLY with respect to Conversation aggregates.
    """

    def __init__(
        self,
        id: EntityId,
        workspace_id: WorkspaceId,
        conversation_id: ConversationId,
        status: AnalysisStatus | None = None,
        signals: Sequence[BehavioralSignal] = (),
        patterns: Sequence[ConversationPattern] = (),
        result: AnalysisResult | None = None,
        error_message: str = "",
        created_at: Timestamp | None = None,
        version: int = 1,
    ) -> None:
        super().__init__(id=id, created_at=created_at, version=version)

        self._workspace_id = workspace_id
        self._conversation_id = conversation_id
        self._status = status or AnalysisStatus.pending()
        self._signals: list[BehavioralSignal] = list(signals)
        self._patterns: list[ConversationPattern] = list(patterns)
        self._result = result
        self._error_message = error_message.strip()

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def workspace_id(self) -> WorkspaceId:
        return self._workspace_id

    @property
    def conversation_id(self) -> ConversationId:
        return self._conversation_id

    @property
    def status(self) -> AnalysisStatus:
        return self._status

    @property
    def signals(self) -> tuple[BehavioralSignal, ...]:
        return tuple(self._signals)

    @property
    def patterns(self) -> tuple[ConversationPattern, ...]:
        return tuple(self._patterns)

    @property
    def result(self) -> AnalysisResult | None:
        return self._result

    @property
    def error_message(self) -> str:
        return self._error_message

    # ── Mutators ──────────────────────────────────────────────────────────

    def start(self) -> Result[None]:
        """Start conversation analysis execution."""
        if not self._status.is_pending:
            return Result.fail(Error("INVALID_STATE", "Only pending analysis jobs can be started"))

        self._status = AnalysisStatus.in_progress()
        self._raise_event(
            AnalysisStarted(
                analysis_id=str(self.id.value),
                conversation_id=str(self._conversation_id.value),
                workspace_id=str(self._workspace_id.value),
            )
        )
        return Result.ok(None)

    def add_signal(self, signal: BehavioralSignal) -> Result[None]:
        """Add a detected behavioral signal to the analysis."""
        if not self._status.is_in_progress:
            return Result.fail(Error("INVALID_STATE", "Analysis must be in progress to add signals"))

        self._signals.append(signal)
        return Result.ok(None)

    def add_pattern(self, pattern: ConversationPattern) -> Result[None]:
        """Add a detected pattern to the analysis."""
        if not self._status.is_in_progress:
            return Result.fail(Error("INVALID_STATE", "Analysis must be in progress to add patterns"))

        self._patterns.append(pattern)
        self._raise_event(
            BehavioralPatternDetected(
                analysis_id=str(self.id.value),
                pattern_name=pattern.pattern_name,
                category=pattern.category.category.value,
                confidence_score=pattern.confidence.value,
            )
        )
        return Result.ok(None)

    def complete(self, result: AnalysisResult) -> Result[None]:
        """Complete the conversation analysis successfully."""
        if not self._status.is_in_progress:
            return Result.fail(Error("INVALID_STATE", "Only in-progress analysis jobs can be completed"))

        self._status = AnalysisStatus.completed()
        self._result = result
        self._version += 1

        self._raise_event(
            AnalysisCompleted(
                analysis_id=str(self.id.value),
                conversation_id=str(self._conversation_id.value),
                signals_count=len(self._signals),
                patterns_count=len(self._patterns),
            )
        )
        return Result.ok(None)

    def fail(self, error_message: str) -> Result[None]:
        """Mark analysis as failed."""
        if self._status.is_completed or self._status.is_failed:
            return Result.fail(Error("INVALID_STATE", "Analysis is already terminal"))

        self._status = AnalysisStatus.failed()
        self._error_message = error_message.strip()
        self._version += 1

        self._raise_event(
            AnalysisFailed(
                analysis_id=str(self.id.value),
                conversation_id=str(self._conversation_id.value),
                error_message=self._error_message,
            )
        )
        return Result.ok(None)
