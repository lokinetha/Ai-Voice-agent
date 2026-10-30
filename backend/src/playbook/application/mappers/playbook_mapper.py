"""
PlaybookMapper for mapping between Domain Playbook aggregate and DTOs.
"""

from __future__ import annotations

from playbook.application.dto.playbook_dto import (
    CommunicationStyleDTO,
    ExampleDTO,
    GoalDTO,
    ObjectionDTO,
    PersonaDTO,
    PlaybookDTO,
    PlaybookVersionDTO,
    RuleDTO,
    StageDTO,
    SuccessCriteriaDTO,
    TransitionDTO,
)
from playbook.domain.entities.playbook import Playbook
from playbook.domain.entities.playbook_example import PlaybookExample
from playbook.domain.entities.playbook_goal import PlaybookGoal
from playbook.domain.entities.playbook_objection import PlaybookObjection
from playbook.domain.entities.playbook_rule import PlaybookRule
from playbook.domain.entities.playbook_stage import PlaybookStage
from playbook.domain.entities.playbook_transition import PlaybookTransition


class PlaybookMapper:
    """Static mapper converting Playbook domain entities to DTOs."""

    @staticmethod
    def to_dto(playbook: Playbook) -> PlaybookDTO:
        """Map Playbook aggregate root to PlaybookDTO."""
        persona_dto = None
        if playbook.persona is not None:
            persona_dto = PersonaDTO(
                name=playbook.persona.name,
                role=playbook.persona.role,
                description=playbook.persona.description,
                industry=playbook.persona.industry,
            )

        style_dto = CommunicationStyleDTO(
            tone=playbook.communication_style.tone.value,
            formality=playbook.communication_style.formality.value,
            pacing=playbook.communication_style.pacing.value,
            vocabulary_level=playbook.communication_style.vocabulary_level,
            use_filler_words=playbook.communication_style.use_filler_words,
        )

        criteria_dto = None
        if playbook.success_criteria is not None:
            criteria_dto = SuccessCriteriaDTO(
                primary_metric=playbook.success_criteria.primary_metric,
                target_value=playbook.success_criteria.target_value,
                secondary_metrics=playbook.success_criteria.secondary_metrics,
                description=playbook.success_criteria.description,
            )

        version_dto = PlaybookVersionDTO(
            version_number=playbook.version_info.version_number,
            label=playbook.version_info.label,
            changelog=playbook.version_info.changelog,
        )

        goals_dtos = tuple(PlaybookMapper.to_goal_dto(g) for g in playbook.goals)
        stages_dtos = tuple(PlaybookMapper.to_stage_dto(s) for s in playbook.stages)
        rules_dtos = tuple(PlaybookMapper.to_rule_dto(r) for r in playbook.rules)
        objections_dtos = tuple(PlaybookMapper.to_objection_dto(o) for o in playbook.objections)
        examples_dtos = tuple(PlaybookMapper.to_example_dto(e) for e in playbook.examples)
        transitions_dtos = tuple(PlaybookMapper.to_transition_dto(t) for t in playbook.transitions)

        return PlaybookDTO(
            id=str(playbook.id.value),
            workspace_id=str(playbook.workspace_id.value),
            name=playbook.name,
            description=playbook.description,
            status=playbook.status.value.value,
            version_info=version_dto,
            persona=persona_dto,
            communication_style=style_dto,
            success_criteria=criteria_dto,
            goals=goals_dtos,
            stages=stages_dtos,
            rules=rules_dtos,
            objections=objections_dtos,
            examples=examples_dtos,
            transitions=transitions_dtos,
            version=playbook.version,
            created_at=playbook.created_at.value,
        )

    @staticmethod
    def to_goal_dto(goal: PlaybookGoal) -> GoalDTO:
        """Map PlaybookGoal entity to GoalDTO."""
        return GoalDTO(
            id=str(goal.id.value),
            name=goal.name,
            description=goal.description,
            priority=goal.priority,
            is_mandatory=goal.is_mandatory,
        )

    @staticmethod
    def to_stage_dto(stage: PlaybookStage) -> StageDTO:
        """Map PlaybookStage entity to StageDTO."""
        goals_dtos = tuple(PlaybookMapper.to_goal_dto(g) for g in stage.goals)
        return StageDTO(
            id=str(stage.id.value),
            name=stage.name,
            order=stage.order,
            description=stage.description,
            goals=goals_dtos,
        )

    @staticmethod
    def to_rule_dto(rule: PlaybookRule) -> RuleDTO:
        """Map PlaybookRule entity to RuleDTO."""
        return RuleDTO(
            id=str(rule.id.value),
            name=rule.name,
            condition=rule.condition,
            action=rule.action,
            is_strict=rule.is_strict,
        )

    @staticmethod
    def to_objection_dto(objection: PlaybookObjection) -> ObjectionDTO:
        """Map PlaybookObjection entity to ObjectionDTO."""
        return ObjectionDTO(
            id=str(objection.id.value),
            trigger_phrase=objection.trigger_phrase,
            objection_category=objection.objection_category,
            response_strategy=objection.response_strategy,
            recommended_response=objection.recommended_response,
        )

    @staticmethod
    def to_example_dto(example: PlaybookExample) -> ExampleDTO:
        """Map PlaybookExample entity to ExampleDTO."""
        return ExampleDTO(
            id=str(example.id.value),
            scenario=example.scenario,
            user_input=example.user_input,
            ideal_response=example.ideal_response,
            explanation=example.explanation,
        )

    @staticmethod
    def to_transition_dto(transition: PlaybookTransition) -> TransitionDTO:
        """Map PlaybookTransition entity to TransitionDTO."""
        return TransitionDTO(
            id=str(transition.id.value),
            from_stage_id=str(transition.from_stage_id.value),
            to_stage_id=str(transition.to_stage_id.value),
            condition=transition.condition,
        )
