"""
SQLAlchemy 2.x Repository Implementation for Prompt Aggregate Root.
"""

from __future__ import annotations

from datetime import UTC, datetime

from shared.kernel.specification import Specification
from shared.kernel.value_objects import EntityId, PromptId, Timestamp, WorkspaceId
from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from prompt.domain.entities.prompt import Prompt
from prompt.domain.entities.prompt_constraint import PromptConstraint
from prompt.domain.entities.prompt_example import PromptExample
from prompt.domain.entities.prompt_instruction import PromptInstruction
from prompt.domain.entities.prompt_section import PromptSection
from prompt.domain.repositories.prompt_repository import PromptRepository
from prompt.domain.value_objects.prompt_compilation_metadata import (
    PromptCompilationMetadata,
)
from prompt.domain.value_objects.prompt_section_type import (
    PromptSectionType,
    SectionCategory,
)
from prompt.domain.value_objects.prompt_status import (
    PromptStatus,
    PromptStatusType,
)
from prompt.domain.value_objects.prompt_template import PromptTemplate
from prompt.domain.value_objects.prompt_version_info import PromptVersionInfo
from prompt.infrastructure.persistence.models import (
    PromptConstraintModel,
    PromptExampleModel,
    PromptInstructionModel,
    PromptModel,
    PromptSectionModel,
)


class SqlAlchemyPromptRepository(PromptRepository):
    """SQLAlchemy implementation of PromptRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: PromptId) -> Prompt | None:
        """Retrieve Prompt aggregate by ID."""
        stmt = select(PromptModel).where(PromptModel.id == str(id.value))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_aggregate(model)

    async def find_by_workspace(self, workspace_id: WorkspaceId) -> list[Prompt]:
        """Find all Prompts in target Workspace."""
        stmt = select(PromptModel).where(
            PromptModel.workspace_id == str(workspace_id.value)
        )
        result = await self._session.execute(stmt)
        return [self._to_aggregate(m) for m in result.scalars().all()]

    async def find_published_version(
        self, prompt_id: PromptId, version_number: int
    ) -> Prompt | None:
        """Find a specific published version snapshot of a Prompt."""
        stmt = select(PromptModel).where(
            PromptModel.id == str(prompt_id.value),
            PromptModel.version_number == version_number,
            PromptModel.status == "PUBLISHED",
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_aggregate(model)

    async def save(self, aggregate: Prompt) -> None:
        """Persist or update Prompt aggregate root."""
        stmt = select(PromptModel).where(PromptModel.id == str(aggregate.id.value))
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            model = self._to_model(aggregate)
            self._session.add(model)
        else:
            existing.name = aggregate.name
            existing.description = aggregate.description
            existing.status = aggregate.status.value.value
            existing.compiled_prompt_text = aggregate.compiled_prompt_text
            existing.version_number = aggregate.version_info.version_number
            existing.version_label = aggregate.version_info.label
            existing.version_changelog = aggregate.version_info.changelog
            existing.version = aggregate.version

            if aggregate.compilation_metadata is not None:
                existing.compilation_metadata_json = {
                    "source_playbook_id": aggregate.compilation_metadata.source_playbook_id,
                    "source_playbook_version": aggregate.compilation_metadata.source_playbook_version,
                    "compiled_at": aggregate.compilation_metadata.compiled_at.isoformat(),
                    "template_name": aggregate.compilation_metadata.template_name,
                    "checksum": aggregate.compilation_metadata.checksum,
                }
            else:
                existing.compilation_metadata_json = None

    async def delete(self, aggregate: Prompt) -> None:
        """Delete Prompt aggregate from persistence."""
        stmt = sql_delete(PromptModel).where(PromptModel.id == str(aggregate.id.value))
        await self._session.execute(stmt)

    async def find(self, spec: Specification[Prompt]) -> list[Prompt]:
        """Find Prompt aggregates satisfying specification filter."""
        stmt = select(PromptModel)
        result = await self._session.execute(stmt)
        aggregates = [self._to_aggregate(m) for m in result.scalars().all()]
        return [a for a in aggregates if spec.is_satisfied_by(a)]

    async def count(self, spec: Specification[Prompt]) -> int:
        """Count Prompt aggregates satisfying specification filter."""
        return len(await self.find(spec))

    def _to_model(self, aggregate: Prompt) -> PromptModel:
        """Map domain Prompt to ORM PromptModel."""
        comp_json = None
        if aggregate.compilation_metadata is not None:
            comp_json = {
                "source_playbook_id": aggregate.compilation_metadata.source_playbook_id,
                "source_playbook_version": aggregate.compilation_metadata.source_playbook_version,
                "compiled_at": aggregate.compilation_metadata.compiled_at.isoformat(),
                "template_name": aggregate.compilation_metadata.template_name,
                "checksum": aggregate.compilation_metadata.checksum,
            }

        template_json = {
            "name": aggregate.template.name,
            "section_order": list(aggregate.template.section_order),
            "prefix": aggregate.template.prefix,
            "suffix": aggregate.template.suffix,
        }

        return PromptModel(
            id=str(aggregate.id.value),
            workspace_id=str(aggregate.workspace_id.value),
            name=aggregate.name,
            description=aggregate.description,
            status=aggregate.status.value.value,
            compiled_prompt_text=aggregate.compiled_prompt_text,
            version_number=aggregate.version_info.version_number,
            version_label=aggregate.version_info.label,
            version_changelog=aggregate.version_info.changelog,
            compilation_metadata_json=comp_json,
            template_json=template_json,
            version=aggregate.version,
            created_at=aggregate.created_at.value,
            sections=[
                PromptSectionModel(
                    id=str(s.id.value),
                    prompt_id=str(aggregate.id.value),
                    section_type=s.section_type.category.value,
                    title=s.title,
                    content=s.content,
                    order=s.order,
                    created_at=s.created_at.value,
                    instructions=[
                        PromptInstructionModel(
                            id=str(inst.id.value),
                            section_id=str(s.id.value),
                            text=inst.text,
                            order=inst.order,
                            is_mandatory=inst.is_mandatory,
                            created_at=inst.created_at.value,
                        )
                        for inst in s.instructions
                    ],
                )
                for s in aggregate.sections
            ],
            constraints=[
                PromptConstraintModel(
                    id=str(c.id.value),
                    prompt_id=str(aggregate.id.value),
                    constraint_type=c.constraint_type,
                    rule_text=c.rule_text,
                    created_at=c.created_at.value,
                )
                for c in aggregate.constraints
            ],
            examples=[
                PromptExampleModel(
                    id=str(e.id.value),
                    prompt_id=str(aggregate.id.value),
                    user_input=e.user_input,
                    ideal_response=e.ideal_response,
                    context=e.context,
                    created_at=e.created_at.value,
                )
                for e in aggregate.examples
            ],
        )

    @staticmethod
    def _to_aggregate(model: PromptModel) -> Prompt:
        """Map ORM PromptModel to domain Prompt aggregate root."""
        created_at_dt = model.created_at
        if created_at_dt and created_at_dt.tzinfo is None:
            created_at_dt = created_at_dt.replace(tzinfo=UTC)

        comp_meta = None
        if model.compilation_metadata_json:
            compiled_at_val = model.compilation_metadata_json.get("compiled_at")
            compiled_at_dt = (
                datetime.fromisoformat(compiled_at_val)
                if compiled_at_val
                else datetime.now(UTC)
            )
            comp_meta = PromptCompilationMetadata(
                source_playbook_id=model.compilation_metadata_json.get("source_playbook_id", ""),
                source_playbook_version=model.compilation_metadata_json.get(
                    "source_playbook_version", 1
                ),
                compiled_at=compiled_at_dt,
                template_name=model.compilation_metadata_json.get("template_name", ""),
                checksum=model.compilation_metadata_json.get("checksum", ""),
            )

        template = PromptTemplate()
        if model.template_json:
            template = PromptTemplate(
                name=model.template_json.get("name", "STANDARD_SYSTEM_PROMPT"),
                section_order=tuple(model.template_json.get("section_order", [])),
                prefix=model.template_json.get("prefix", ""),
                suffix=model.template_json.get("suffix", ""),
            )

        version_info = PromptVersionInfo(
            version_number=model.version_number,
            label=model.version_label,
            changelog=model.version_changelog,
        )

        sections = []
        for s in model.sections:
            s_created = s.created_at
            if s_created and s_created.tzinfo is None:
                s_created = s_created.replace(tzinfo=UTC)

            instructions = [
                PromptInstruction(
                    id=EntityId(inst.id),
                    text=inst.text,
                    order=inst.order,
                    is_mandatory=inst.is_mandatory,
                    created_at=Timestamp(
                        inst.created_at.replace(tzinfo=UTC)
                        if inst.created_at and inst.created_at.tzinfo is None
                        else inst.created_at
                    ),
                )
                for inst in s.instructions
            ]

            sections.append(
                PromptSection(
                    id=EntityId(s.id),
                    section_type=PromptSectionType(SectionCategory(s.section_type)),
                    title=s.title,
                    content=s.content,
                    order=s.order,
                    instructions=instructions,
                    created_at=Timestamp(s_created),
                )
            )

        constraints = [
            PromptConstraint(
                id=EntityId(c.id),
                constraint_type=c.constraint_type,
                rule_text=c.rule_text,
                created_at=Timestamp(
                    c.created_at.replace(tzinfo=UTC)
                    if c.created_at and c.created_at.tzinfo is None
                    else c.created_at
                ),
            )
            for c in model.constraints
        ]

        examples = [
            PromptExample(
                id=EntityId(e.id),
                user_input=e.user_input,
                ideal_response=e.ideal_response,
                context=e.context,
                created_at=Timestamp(
                    e.created_at.replace(tzinfo=UTC)
                    if e.created_at and e.created_at.tzinfo is None
                    else e.created_at
                ),
            )
            for e in model.examples
        ]

        return Prompt(
            id=PromptId(model.id),
            workspace_id=WorkspaceId(model.workspace_id),
            name=model.name,
            description=model.description,
            status=PromptStatus(PromptStatusType(model.status)),
            version_info=version_info,
            template=template,
            compiled_prompt_text=model.compiled_prompt_text,
            compilation_metadata=comp_meta,
            sections=sections,
            constraints=constraints,
            examples=examples,
            created_at=Timestamp(created_at_dt),
            version=model.version,
        )
