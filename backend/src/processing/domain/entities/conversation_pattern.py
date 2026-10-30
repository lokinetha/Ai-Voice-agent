"""
ConversationPattern Entity for Processing Bounded Context.

Represents an aggregated pattern synthesized from multiple behavioral signals.
Rule enforced: Preserves traceability back to signal and conversation references.
"""

from __future__ import annotations

from collections.abc import Sequence

from shared.kernel.entity import Entity
from shared.kernel.value_objects import EntityId, Timestamp

from processing.domain.value_objects.behavioral_category import (
    BehavioralCategory,
)
from processing.domain.value_objects.confidence_score import ConfidenceScore


class ConversationPattern(Entity[EntityId]):
    """ConversationPattern entity capturing recurrent behavior across conversations."""

    def __init__(
        self,
        id: EntityId,
        pattern_name: str,
        category: BehavioralCategory,
        description: str,
        frequency: int,
        confidence: ConfidenceScore,
        sample_signal_ids: Sequence[str] = (),
        conversation_references: Sequence[str] = (),
        created_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)

        if not pattern_name or not pattern_name.strip():
            raise ValueError("ConversationPattern pattern_name cannot be empty")
        if frequency < 1:
            raise ValueError("ConversationPattern frequency must be >= 1")

        self._pattern_name = pattern_name.strip()
        self._category = category
        self._description = description.strip()
        self._frequency = frequency
        self._confidence = confidence
        self._sample_signal_ids: list[str] = list(sample_signal_ids)
        self._conversation_references: list[str] = list(conversation_references)

    @property
    def pattern_name(self) -> str:
        return self._pattern_name

    @property
    def category(self) -> BehavioralCategory:
        return self._category

    @property
    def description(self) -> str:
        return self._description

    @property
    def frequency(self) -> int:
        return self._frequency

    @property
    def confidence(self) -> ConfidenceScore:
        return self._confidence

    @property
    def sample_signal_ids(self) -> tuple[str, ...]:
        return tuple(self._sample_signal_ids)

    @property
    def conversation_references(self) -> tuple[str, ...]:
        return tuple(self._conversation_references)
