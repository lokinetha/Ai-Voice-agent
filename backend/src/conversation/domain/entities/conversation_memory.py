"""
ConversationMemory Entity for Conversation Bounded Context.

Maintains a sliding context window of conversation turns.
Memory belongs only to one Conversation.
"""

from __future__ import annotations

from shared.kernel.entity import Entity
from shared.kernel.value_objects import EntityId, Timestamp


class ConversationMemory(Entity[EntityId]):
    """ConversationMemory Entity managing turn-based context window."""

    MAX_CONTEXT_ENTRIES = 100

    def __init__(
        self,
        id: EntityId,
        context_window: list[dict[str, str]] | None = None,
        max_tokens: int = 4096,
        created_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)

        if max_tokens <= 0:
            raise ValueError("max_tokens must be positive")

        self._context_window: list[dict[str, str]] = list(context_window) if context_window else []
        self._max_tokens = max_tokens

    @property
    def context_window(self) -> list[dict[str, str]]:
        """Return copy of current context window."""
        return list(self._context_window)

    @property
    def max_tokens(self) -> int:
        return self._max_tokens

    def append_turn(self, role: str, content: str) -> None:
        """Append a conversation turn to memory.

        Truncates oldest entries when exceeding MAX_CONTEXT_ENTRIES.

        Args:
            role: Speaker role string (e.g. 'agent', 'customer').
            content: Message content text.
        """
        self._context_window.append({"role": role, "content": content})

        if len(self._context_window) > self.MAX_CONTEXT_ENTRIES:
            self._context_window = self._context_window[-self.MAX_CONTEXT_ENTRIES :]

    def get_context(self) -> list[dict[str, str]]:
        """Return current context window."""
        return list(self._context_window)
