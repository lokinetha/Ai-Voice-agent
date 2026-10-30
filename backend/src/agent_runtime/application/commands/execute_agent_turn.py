"""
ExecuteAgentTurn Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Result

from agent_runtime.application.dto.agent_runtime_dto import AgentResponse
from agent_runtime.application.services.agent_runtime_service import (
    AgentRuntimeService,
)


@dataclass(frozen=True)
class ExecuteAgentTurnCommand(Command):
    """Command requesting execution of an Agent conversational turn."""

    workspace_id: str
    agent_id: str
    conversation_id: str
    message_text: str
    correlation_id: str | None = None


class ExecuteAgentTurnHandler(CommandHandler[ExecuteAgentTurnCommand, AgentResponse]):
    """CQRS Handler executing ExecuteAgentTurnCommand via AgentRuntimeService."""

    def __init__(self, runtime_service: AgentRuntimeService) -> None:
        self._runtime_service = runtime_service

    async def handle(self, command: ExecuteAgentTurnCommand) -> Result[AgentResponse]:
        """Execute Agent turn orchestration."""
        return await self._runtime_service.execute_turn(
            workspace_id=command.workspace_id,
            agent_id=command.agent_id,
            conversation_id=command.conversation_id,
            message_text=command.message_text,
            correlation_id=command.correlation_id,
        )
