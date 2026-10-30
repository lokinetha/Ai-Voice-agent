"""
PromptCompilationService Domain Service for Prompt Bounded Context.

Transforms a published PlaybookDataDTO into ordered, structured PromptSection
entities and compiles a deterministic system prompt text string.
"""

from __future__ import annotations

from shared.kernel.domain_service import DomainService
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import EntityId

from prompt.domain.entities.prompt_instruction import PromptInstruction
from prompt.domain.entities.prompt_section import PromptSection
from prompt.domain.ports.playbook_port import PlaybookDataDTO
from prompt.domain.value_objects.prompt_compilation_metadata import (
    PromptCompilationMetadata,
)
from prompt.domain.value_objects.prompt_section_type import (
    PromptSectionType,
    SectionCategory,
)


class PromptCompilationService(DomainService):
    """Domain Service executing deterministic compilation of system prompts."""

    def compile(self, playbook_data: PlaybookDataDTO) -> Result[tuple[str, list[PromptSection], PromptCompilationMetadata]]:
        """Compile PlaybookDataDTO into deterministic system prompt text and sections.

        Requirements enforced:
        - Only published playbooks (status == "PUBLISHED") can be compiled.
        - Output text and SHA256 checksum are 100% deterministic for identical inputs.

        Args:
            playbook_data: Read-only Playbook data DTO from PlaybookQueryPort.

        Returns:
            Result wrapping (compiled_text, sections, metadata) or Error.
        """
        if playbook_data.status.upper() != "PUBLISHED":
            return Result.fail(
                Error(
                    "INVARIANT_VIOLATION",
                    f"Only published Playbooks can be compiled into system prompts. Current status: '{playbook_data.status}'",
                )
            )

        sections: list[PromptSection] = []
        text_parts: list[str] = []

        # 1. Header
        text_parts.append("=== SYSTEM PROMPT ===")
        text_parts.append(f"Playbook: {playbook_data.name} (v{playbook_data.version_number})")
        if playbook_data.description:
            text_parts.append(f"Description: {playbook_data.description}")
        text_parts.append("")

        order_counter = 1

        # 2. Persona Section
        if playbook_data.persona_name and playbook_data.persona_role:
            persona_content = (
                f"Identity: {playbook_data.persona_name}\n"
                f"Role: {playbook_data.persona_role}\n"
                f"Style: {playbook_data.tone} / {playbook_data.formality} / {playbook_data.pacing}\n"
                f"Description: {playbook_data.persona_description}"
            )
            sec_persona = PromptSection(
                id=EntityId(),
                section_type=PromptSectionType(SectionCategory.PERSONA),
                title="1. Persona & Tone",
                content=persona_content,
                order=order_counter,
            )
            sections.append(sec_persona)
            text_parts.append(f"## {sec_persona.title}")
            text_parts.append(persona_content)
            text_parts.append("")
            order_counter += 1

        # 3. Goals Section
        if playbook_data.goals:
            sorted_goals = sorted(playbook_data.goals, key=lambda g: (g.priority, g.name))
            goal_instructions = []
            for g_idx, g in enumerate(sorted_goals, start=1):
                mand_str = "[MANDATORY]" if g.is_mandatory else "[OPTIONAL]"
                goal_instructions.append(
                    PromptInstruction(
                        id=EntityId(),
                        text=f"{mand_str} Priority {g.priority}: {g.name} - {g.description}",
                        order=g_idx,
                        is_mandatory=g.is_mandatory,
                    )
                )

            goals_text = "\n".join(inst.text for inst in goal_instructions)
            sec_goals = PromptSection(
                id=EntityId(),
                section_type=PromptSectionType(SectionCategory.GOALS),
                title="2. Strategic Goals",
                content=goals_text,
                order=order_counter,
                instructions=goal_instructions,
            )
            sections.append(sec_goals)
            text_parts.append(f"## {sec_goals.title}")
            text_parts.append(goals_text)
            text_parts.append("")
            order_counter += 1

        # 4. Rules & Constraints Section
        if playbook_data.rules:
            sorted_rules = sorted(playbook_data.rules, key=lambda r: r.name)
            rule_instructions = []
            for r_idx, r in enumerate(sorted_rules, start=1):
                strict_str = "[STRICT]" if r.is_strict else "[GUIDELINE]"
                rule_instructions.append(
                    PromptInstruction(
                        id=EntityId(),
                        text=f"{strict_str} {r.name}: IF {r.condition} THEN {r.action}",
                        order=r_idx,
                        is_mandatory=r.is_strict,
                    )
                )

            rules_text = "\n".join(inst.text for inst in rule_instructions)
            sec_rules = PromptSection(
                id=EntityId(),
                section_type=PromptSectionType(SectionCategory.RULES),
                title="3. Behavioral Rules",
                content=rules_text,
                order=order_counter,
                instructions=rule_instructions,
            )
            sections.append(sec_rules)
            text_parts.append(f"## {sec_rules.title}")
            text_parts.append(rules_text)
            text_parts.append("")
            order_counter += 1

        # 5. Conversation Stages Section
        if playbook_data.stages:
            sorted_stages = sorted(playbook_data.stages, key=lambda s: (s.order, s.name))
            stage_lines = []
            for s in sorted_stages:
                stage_lines.append(f"Stage {s.order}: {s.name} - {s.description}")
            stages_text = "\n".join(stage_lines)
            sec_stages = PromptSection(
                id=EntityId(),
                section_type=PromptSectionType(SectionCategory.STAGES),
                title="4. Conversation Flow Stages",
                content=stages_text,
                order=order_counter,
            )
            sections.append(sec_stages)
            text_parts.append(f"## {sec_stages.title}")
            text_parts.append(stages_text)
            text_parts.append("")
            order_counter += 1

        # 6. Objection Handling Section
        if playbook_data.objections:
            sorted_obj = sorted(playbook_data.objections, key=lambda o: (o.objection_category, o.trigger_phrase))
            obj_lines = []
            for o in sorted_obj:
                obj_lines.append(
                    f"[{o.objection_category}] Trigger: \"{o.trigger_phrase}\" -> Strategy: {o.response_strategy}"
                )
            objections_text = "\n".join(obj_lines)
            sec_obj = PromptSection(
                id=EntityId(),
                section_type=PromptSectionType(SectionCategory.OBJECTIONS),
                title="5. Objection Handling",
                content=objections_text,
                order=order_counter,
            )
            sections.append(sec_obj)
            text_parts.append(f"## {sec_obj.title}")
            text_parts.append(objections_text)
            text_parts.append("")
            order_counter += 1

        # 7. Few-Shot Examples Section
        if playbook_data.examples:
            sorted_ex = sorted(playbook_data.examples, key=lambda e: e.scenario)
            ex_lines = []
            for e in sorted_ex:
                ex_lines.append(
                    f"Scenario: {e.scenario}\nUser: {e.user_input}\nAssistant: {e.ideal_response}"
                )
            examples_text = "\n\n".join(ex_lines)
            sec_ex = PromptSection(
                id=EntityId(),
                section_type=PromptSectionType(SectionCategory.EXAMPLES),
                title="6. Conversation Examples",
                content=examples_text,
                order=order_counter,
            )
            sections.append(sec_ex)
            text_parts.append(f"## {sec_ex.title}")
            text_parts.append(examples_text)
            text_parts.append("")
            order_counter += 1

        compiled_prompt_text = "\n".join(text_parts).strip()

        metadata = PromptCompilationMetadata.compute(
            source_playbook_id=playbook_data.playbook_id,
            source_playbook_version=playbook_data.version_number,
            compiled_text=compiled_prompt_text,
        )

        return Result.ok((compiled_prompt_text, sections, metadata))
