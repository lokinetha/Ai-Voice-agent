"""
ConversationTimeline Entity for Conversation Bounded Context.

Maintains an immutable, append-only log of significant conversation events.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.entity import Entity
from shared.kernel.value_objects import EntityId, Timestamp


@dataclass(frozen=True)
class TimelineEntry:
    """Immutable record of a single timeline event."""

    event_type: str
    timestamp: Timestamp
    details: str


class ConversationTimeline(Entity[EntityId]):
    """ConversationTimeline Entity maintaining immutable event log."""

    def __init__(
        self,
        id: EntityId,
        entries: tuple[TimelineEntry, ...] = (),
        created_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)
        self._entries: list[TimelineEntry] = list(entries)

    @property
    def entries(self) -> tuple[TimelineEntry, ...]:
        """Return immutable view of timeline entries."""
        return tuple(self._entries)

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    def record(self, event_type: str, details: str) -> None:
        """Append an immutable timeline entry.

        Args:
            event_type: Category string of the event (e.g. 'STARTED', 'MESSAGE').
            details: Human-readable description of the event.
        """
        entry = TimelineEntry(
            event_type=event_type,
            timestamp=Timestamp.now(),
            details=details,
        )
        self._entries.append(entry)
