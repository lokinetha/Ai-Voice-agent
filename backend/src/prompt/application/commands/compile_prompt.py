"""
CompilePrompt Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import PromptId

from prompt.application.dto.prompt_dto import PromptDTO
from prompt.application.mappers.prompt_mapper import PromptMapper
from prompt.domain.ports.playbook_port import PlaybookQueryPort
from prompt.domain.repositories.prompt_repository import PromptRepository
from prompt.domain.services.prompt_compilation_service import (
    PromptCompilationService,
)


@dataclass(frozen=True)
class CompilePromptCommand(Command):
    """Command requesting compilation of a published Playbook into a Prompt."""

    prompt_id: str
    playbook_id: str
    playbook_version: int | None = None


class CompilePromptHandler(CommandHandler[CompilePromptCommand, PromptDTO]):
    """Handler executing CompilePromptCommand."""

    def __init__(
        self,
        prompt_repository: PromptRepository,
        playbook_port: PlaybookQueryPort,
        compilation_service: PromptCompilationService,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repo = prompt_repository
        self._playbook_port = playbook_port
        self._comp_svc = compilation_service
        self._uow = unit_of_work

    async def handle(self, command: CompilePromptCommand) -> Result[PromptDTO]:
        """Execute Prompt compilation from published Playbook data."""
        prompt = await self._repo.get_by_id(PromptId(command.prompt_id))
        if prompt is None:
            return Result.fail(Error("NOT_FOUND", f"Prompt '{command.prompt_id}' not found"))

        playbook_data = await self._playbook_port.get_published_playbook(
            playbook_id=command.playbook_id,
            version_number=command.playbook_version,
        )
        if playbook_data is None:
            return Result.fail(
                Error(
                    "NOT_FOUND",
                    f"Published Playbook '{command.playbook_id}' (version={command.playbook_version}) not found or not published",
                )
            )

        comp_res = self._comp_svc.compile(playbook_data)
        if comp_res.is_failure:
            return Result.fail(comp_res.error)

        compiled_text, sections, metadata = comp_res.value
        set_res = prompt.set_compilation_result(
            compiled_text=compiled_text,
            sections=sections,
            metadata=metadata,
        )
        if set_res.is_failure:
            return Result.fail(set_res.error)

        async with self._uow:
            await self._repo.save(prompt)
            await self._uow.commit()

        return Result.ok(PromptMapper.to_dto(prompt))
