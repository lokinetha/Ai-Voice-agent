"""
BehavioralSignal Entity for Processing Bounded Context.

Represents an individual behavioral signal detected in a conversation turn/message.
Rule enforced: Every signal MUST include a confidence score and source message reference.
"""

from __future__ import annotations

from shared.kernel.entity import Entity
from shared.kernel.value_objects import EntityId, Timestamp

from processing.domain.value_objects.behavioral_category import (
    BehavioralCategory,
)
from processing.domain.value_objects.confidence_score import ConfidenceScore


class BehavioralSignal(Entity[EntityId]):
    """BehavioralSignal entity capturing specific behavior extracted from conversation messages."""

    def __init__(
        self,
        id: EntityId,
        category: BehavioralCategory,
        signal_type: str,
        description: str,
        confidence: ConfidenceScore,
        source_message_id: str,
        evidence_text: str = "",
        created_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)

        if not signal_type or not signal_type.strip():
            raise ValueError("BehavioralSignal signal_type cannot be empty")
        if not source_message_id or not source_message_id.strip():
            raise ValueError("BehavioralSignal source_message_id cannot be empty for traceability")

        self._category = category
        self._signal_type = signal_type.strip()
        self._description = description.strip()
        self._confidence = confidence
        self._source_message_id = source_message_id.strip()
        self._evidence_text = evidence_text.strip()

    @property
    def category(self) -> BehavioralCategory:
        return self._category

    @property
    def signal_type(self) -> str:
        return self._signal_type

    @property
    def description(self) -> str:
        return self._description

    @property
    def confidence(self) -> ConfidenceScore:
        return self._confidence

    @property
    def source_message_id(self) -> str:
        return self._source_message_id

    @property
    def evidence_text(self) -> str:
        return self._evidence_text
