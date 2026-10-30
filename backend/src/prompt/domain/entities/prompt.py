"""
Prompt Aggregate Root for Prompt Bounded Context.

Central transactional boundary managing compiled system prompt sections,
instructions, examples, constraints, compilation metadata, and versioning.
"""

from __future__ import annotations

from collections.abc import Sequence

from shared.kernel.aggregate_root import AggregateRoot
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import (
    PromptId,
    PromptVersion,
    Timestamp,
    WorkspaceId,
)

from prompt.domain.entities.prompt_constraint import PromptConstraint
from prompt.domain.entities.prompt_example import PromptExample
from prompt.domain.entities.prompt_instruction import PromptInstruction
from prompt.domain.entities.prompt_section import PromptSection
from prompt.domain.events.prompt_archived import PromptArchived
from prompt.domain.events.prompt_compiled import PromptCompiled
from prompt.domain.events.prompt_published import PromptPublished
from prompt.domain.events.prompt_version_created import PromptVersionCreated
from prompt.domain.value_objects.prompt_compilation_metadata import (
    PromptCompilationMetadata,
)
from prompt.domain.value_objects.prompt_status import PromptStatus
from prompt.domain.value_objects.prompt_template import PromptTemplate
from prompt.domain.value_objects.prompt_variable import PromptVariable
from prompt.domain.value_objects.prompt_version_info import PromptVersionInfo


class Prompt(AggregateRoot[PromptId]):
    """Prompt Aggregate Root.

    Invariants enforced:
    - Only compiled prompts satisfying PublishablePromptSpec can be published.
    - Published prompt versions are immutable.
    - Preserves Playbook source version metadata.
    - Compilation is deterministic for identical Playbook inputs.
    """

    def __init__(
        self,
        id: PromptId,
        workspace_id: WorkspaceId,
        name: str,
        description: str = "",
        status: PromptStatus | None = None,
        version_info: PromptVersionInfo | None = None,
        template: PromptTemplate | None = None,
        compiled_prompt_text: str = "",
        compilation_metadata: PromptCompilationMetadata | None = None,
        sections: Sequence[PromptSection] = (),
        instructions: Sequence[PromptInstruction] = (),
        examples: Sequence[PromptExample] = (),
        constraints: Sequence[PromptConstraint] = (),
        variables: Sequence[PromptVariable] = (),
        created_at: Timestamp | None = None,
        version: int = 1,
    ) -> None:
        super().__init__(id=id, created_at=created_at, version=version)

        if not name or not name.strip():
            raise ValueError("Prompt name cannot be empty")

        self._workspace_id = workspace_id
        self._name = name.strip()
        self._description = description.strip()
        self._status = status or PromptStatus.draft()
        self._version_info = version_info or PromptVersionInfo()
        self._template = template or PromptTemplate()
        self._compiled_prompt_text = compiled_prompt_text
        self._compilation_metadata = compilation_metadata
        self._sections: list[PromptSection] = list(sections)
        self._instructions: list[PromptInstruction] = list(instructions)
        self._examples: list[PromptExample] = list(examples)
        self._constraints: list[PromptConstraint] = list(constraints)
        self._variables: list[PromptVariable] = list(variables)

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def workspace_id(self) -> WorkspaceId:
        return self._workspace_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def status(self) -> PromptStatus:
        return self._status

    @property
    def version_info(self) -> PromptVersionInfo:
        return self._version_info

    @property
    def template(self) -> PromptTemplate:
        return self._template

    @property
    def compiled_prompt_text(self) -> str:
        return self._compiled_prompt_text

    @property
    def compilation_metadata(self) -> PromptCompilationMetadata | None:
        return self._compilation_metadata

    @property
    def sections(self) -> tuple[PromptSection, ...]:
        return tuple(self._sections)

    @property
    def instructions(self) -> tuple[PromptInstruction, ...]:
        return tuple(self._instructions)

    @property
    def examples(self) -> tuple[PromptExample, ...]:
        return tuple(self._examples)

    @property
    def constraints(self) -> tuple[PromptConstraint, ...]:
        return tuple(self._constraints)

    @property
    def variables(self) -> tuple[PromptVariable, ...]:
        return tuple(self._variables)

    # ── Mutators ──────────────────────────────────────────────────────────

    def update_metadata(self, name: str, description: str = "") -> Result[None]:
        """Update Prompt name and description."""
        if self._status.is_archived:
            return Result.fail(Error("INVALID_STATE", "Cannot update archived prompt"))

        if not name or not name.strip():
            return Result.fail(Error("VALIDATION_ERROR", "Prompt name cannot be empty"))

        self._name = name.strip()
        self._description = description.strip()
        return Result.ok(None)

    def set_compilation_result(
        self,
        compiled_text: str,
        sections: Sequence[PromptSection],
        metadata: PromptCompilationMetadata,
    ) -> Result[None]:
        """Set the outcome of compilation."""
        if self._status.is_archived:
            return Result.fail(Error("INVALID_STATE", "Cannot compile archived prompt"))

        self._compiled_prompt_text = compiled_text
        self._sections = list(sections)
        self._compilation_metadata = metadata
        self._status = PromptStatus.compiled()

        self._raise_event(
            PromptCompiled(
                prompt_id=str(self.id.value),
                source_playbook_id=metadata.source_playbook_id,
                source_playbook_version=metadata.source_playbook_version,
                checksum=metadata.checksum,
            )
        )
        return Result.ok(None)

    def publish(self, label: str = "", changelog: str = "") -> Result[PromptVersion]:
        """Publish the Prompt creating an immutable production version snapshot."""
        if self._status.is_archived:
            return Result.fail(Error("INVALID_STATE", "Cannot publish archived prompt"))

        if not self._status.is_compiled or not self._compiled_prompt_text:
            return Result.fail(
                Error("INVALID_STATE", "Only compiled prompts can be published")
            )

        self._status = PromptStatus.published()
        self._version_info = self._version_info.next(label=label, changelog=changelog)
        self._version += 1

        version_id = PromptVersion()

        self._raise_event(
            PromptPublished(
                prompt_id=str(self.id.value),
                version_number=self._version_info.version_number,
            )
        )
        self._raise_event(
            PromptVersionCreated(
                prompt_id=str(self.id.value),
                version_id=str(version_id.value),
                version_number=self._version_info.version_number,
            )
        )

        return Result.ok(version_id)

    def archive(self, reason: str = "") -> Result[None]:
        """Archive the Prompt."""
        if self._status.is_archived:
            return Result.fail(Error("INVALID_STATE", "Prompt is already archived"))

        self._status = PromptStatus.archived()
        self._raise_event(
            PromptArchived(
                prompt_id=str(self.id.value),
                reason=reason,
            )
        )
        return Result.ok(None)
