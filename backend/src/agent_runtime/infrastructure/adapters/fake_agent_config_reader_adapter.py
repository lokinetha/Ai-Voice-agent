"""
FakeAgentConfigReaderAdapter implementing AgentConfigReaderPort.

In-memory test double for loading active Agent configuration.
"""

from __future__ import annotations

from agent_runtime.application.dto.agent_runtime_dto import AgentConfigDTO
from agent_runtime.application.ports.agent_config_reader_port import (
    AgentConfigReaderPort,
)


class FakeAgentConfigReaderAdapter(AgentConfigReaderPort):
    """In-memory test double for AgentConfigReaderPort."""

    def __init__(self, configs: list[AgentConfigDTO] | None = None) -> None:
        self._configs: dict[tuple[str, str], AgentConfigDTO] = {}
        if configs:
            for cfg in configs:
                self.add_config(cfg)

    def add_config(self, config: AgentConfigDTO) -> None:
        """Register Agent config in memory."""
        self._configs[(config.workspace_id, config.agent_id)] = config

    async def get_agent_config(
        self, workspace_id: str, agent_id: str
    ) -> AgentConfigDTO | None:
        """Retrieve registered Agent configuration."""
        return self._configs.get((workspace_id, agent_id))
