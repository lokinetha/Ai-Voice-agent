"""
CreatePlaybook Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import WorkspaceId

from playbook.application.dto.playbook_dto import PlaybookDTO
from playbook.application.mappers.playbook_mapper import PlaybookMapper
from playbook.domain.factories.playbook_factory import PlaybookFactory
from playbook.domain.repositories.playbook_repository import PlaybookRepository
from playbook.domain.value_objects.communication_style import (
    CommunicationStyle,
    FormalityLevel,
    PacingType,
    ToneType,
)
from playbook.domain.value_objects.persona import Persona
from playbook.domain.value_objects.success_criteria import SuccessCriteria


@dataclass(frozen=True)
class CreatePlaybookCommand(Command):
    """Command requesting Playbook creation."""

    workspace_id: str
    name: str
    description: str = ""
    persona_name: str = ""
    persona_role: str = ""
    persona_description: str = ""
    persona_industry: str = ""
    tone: str = "PROFESSIONAL"
    formality: str = "SEMI_FORMAL"
    pacing: str = "MODERATE"
    primary_metric: str = ""
    target_value: float = 0.0


class CreatePlaybookHandler(CommandHandler[CreatePlaybookCommand, PlaybookDTO]):
    """Handler executing CreatePlaybookCommand."""

    def __init__(
        self,
        playbook_repository: PlaybookRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repo = playbook_repository
        self._uow = unit_of_work

    async def handle(self, command: CreatePlaybookCommand) -> Result[PlaybookDTO]:
        """Execute Playbook creation."""
        if not command.workspace_id:
            return Result.fail(Error("VALIDATION_ERROR", "Workspace ID cannot be empty"))
        if not command.name or not command.name.strip():
            return Result.fail(Error("VALIDATION_ERROR", "Playbook name cannot be empty"))

        persona = None
        if command.persona_name and command.persona_role:
            try:
                persona = Persona(
                    name=command.persona_name,
                    role=command.persona_role,
                    description=command.persona_description,
                    industry=command.persona_industry,
                )
            except ValueError as err:
                return Result.fail(Error("VALIDATION_ERROR", str(err)))

        try:
            tone_enum = ToneType(command.tone.upper())
            formality_enum = FormalityLevel(command.formality.upper())
            pacing_enum = PacingType(command.pacing.upper())
            comm_style = CommunicationStyle(
                tone=tone_enum,
                formality=formality_enum,
                pacing=pacing_enum,
            )
        except ValueError:
            comm_style = CommunicationStyle.default()

        success_criteria = None
        if command.primary_metric:
            try:
                success_criteria = SuccessCriteria(
                    primary_metric=command.primary_metric,
                    target_value=command.target_value,
                )
            except ValueError as err:
                return Result.fail(Error("VALIDATION_ERROR", str(err)))

        pb = PlaybookFactory.create(
            workspace_id=WorkspaceId(command.workspace_id),
            name=command.name,
            description=command.description,
            persona=persona,
            communication_style=comm_style,
            success_criteria=success_criteria,
        )

        async with self._uow:
            await self._repo.save(pb)
            await self._uow.commit()

        return Result.ok(PlaybookMapper.to_dto(pb))
