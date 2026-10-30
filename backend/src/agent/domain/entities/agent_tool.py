"""
AgentTool Entity for Agent Bounded Context.

Represents an executable function or external API tool assigned to an Agent.
"""

from __future__ import annotations

from typing import Any

from shared.kernel.entity import Entity
from shared.kernel.value_objects import EntityId, Timestamp


class AgentTool(Entity):
    """AgentTool Entity owned by Agent aggregate root."""

    def __init__(
        self,
        id: EntityId,
        name: str,
        tool_type: str,
        schema: dict[str, Any],
        config: dict[str, Any],
        enabled: bool = True,
        created_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)

        if not name or not isinstance(name, str) or not name.strip():
            raise ValueError("AgentTool name cannot be empty")
        if not tool_type or not isinstance(tool_type, str):
            raise ValueError("AgentTool tool_type cannot be empty")

        self._name = name.strip()
        self._tool_type = tool_type
        self._schema = schema
        self._config = config
        self._enabled = enabled

    @property
    def name(self) -> str:
        return self._name

    @property
    def tool_type(self) -> str:
        return self._tool_type

    @property
    def schema(self) -> dict[str, Any]:
        return dict(self._schema)

    @property
    def config(self) -> dict[str, Any]:
        return dict(self._config)

    @property
    def enabled(self) -> bool:
        return self._enabled

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False
