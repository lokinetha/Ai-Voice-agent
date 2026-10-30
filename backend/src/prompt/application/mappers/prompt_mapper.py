"""
PromptMapper for mapping between Domain Prompt aggregate and DTOs.
"""

from __future__ import annotations

from prompt.application.dto.prompt_dto import (
    PromptCompilationMetadataDTO,
    PromptConstraintDTO,
    PromptDTO,
    PromptExampleDTO,
    PromptInstructionDTO,
    PromptSectionDTO,
    PromptVersionDTO,
)
from prompt.domain.entities.prompt import Prompt
from prompt.domain.entities.prompt_constraint import PromptConstraint
from prompt.domain.entities.prompt_example import PromptExample
from prompt.domain.entities.prompt_instruction import PromptInstruction
from prompt.domain.entities.prompt_section import PromptSection


class PromptMapper:
    """Static mapper converting Prompt domain entities to DTOs."""

    @staticmethod
    def to_dto(prompt: Prompt) -> PromptDTO:
        """Map Prompt aggregate root to PromptDTO."""
        comp_dto = None
        if prompt.compilation_metadata is not None:
            comp_dto = PromptCompilationMetadataDTO(
                source_playbook_id=prompt.compilation_metadata.source_playbook_id,
                source_playbook_version=prompt.compilation_metadata.source_playbook_version,
                compiled_at=prompt.compilation_metadata.compiled_at,
                template_name=prompt.compilation_metadata.template_name,
                checksum=prompt.compilation_metadata.checksum,
            )

        ver_dto = PromptVersionDTO(
            version_number=prompt.version_info.version_number,
            label=prompt.version_info.label,
            changelog=prompt.version_info.changelog,
        )

        sec_dtos = tuple(PromptMapper.to_section_dto(s) for s in prompt.sections)
        con_dtos = tuple(PromptMapper.to_constraint_dto(c) for c in prompt.constraints)
        ex_dtos = tuple(PromptMapper.to_example_dto(e) for e in prompt.examples)

        return PromptDTO(
            id=str(prompt.id.value),
            workspace_id=str(prompt.workspace_id.value),
            name=prompt.name,
            description=prompt.description,
            status=prompt.status.value.value,
            compiled_prompt_text=prompt.compiled_prompt_text,
            version_info=ver_dto,
            compilation_metadata=comp_dto,
            sections=sec_dtos,
            constraints=con_dtos,
            examples=ex_dtos,
            version=prompt.version,
            created_at=prompt.created_at.value,
        )

    @staticmethod
    def to_section_dto(section: PromptSection) -> PromptSectionDTO:
        """Map PromptSection entity to PromptSectionDTO."""
        inst_dtos = tuple(PromptMapper.to_instruction_dto(i) for i in section.instructions)
        return PromptSectionDTO(
            id=str(section.id.value),
            section_type=section.section_type.category.value,
            title=section.title,
            content=section.content,
            order=section.order,
            instructions=inst_dtos,
        )

    @staticmethod
    def to_instruction_dto(instruction: PromptInstruction) -> PromptInstructionDTO:
        """Map PromptInstruction entity to PromptInstructionDTO."""
        return PromptInstructionDTO(
            id=str(instruction.id.value),
            text=instruction.text,
            order=instruction.order,
            is_mandatory=instruction.is_mandatory,
        )

    @staticmethod
    def to_constraint_dto(constraint: PromptConstraint) -> PromptConstraintDTO:
        """Map PromptConstraint entity to PromptConstraintDTO."""
        return PromptConstraintDTO(
            id=str(constraint.id.value),
            constraint_type=constraint.constraint_type,
            rule_text=constraint.rule_text,
        )

    @staticmethod
    def to_example_dto(example: PromptExample) -> PromptExampleDTO:
        """Map PromptExample entity to PromptExampleDTO."""
        return PromptExampleDTO(
            id=str(example.id.value),
            user_input=example.user_input,
            ideal_response=example.ideal_response,
            context=example.context,
        )
