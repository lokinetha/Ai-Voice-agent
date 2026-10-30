"""
SQLAlchemy 2.x Repository Implementation for Playbook Aggregate Root.
"""

from __future__ import annotations

from datetime import UTC

from shared.kernel.specification import Specification
from shared.kernel.value_objects import EntityId, PlaybookId, Timestamp, WorkspaceId
from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from playbook.domain.entities.playbook import Playbook
from playbook.domain.entities.playbook_example import PlaybookExample
from playbook.domain.entities.playbook_goal import PlaybookGoal
from playbook.domain.entities.playbook_objection import PlaybookObjection
from playbook.domain.entities.playbook_rule import PlaybookRule
from playbook.domain.entities.playbook_stage import PlaybookStage
from playbook.domain.entities.playbook_transition import PlaybookTransition
from playbook.domain.repositories.playbook_repository import PlaybookRepository
from playbook.domain.value_objects.communication_style import (
    CommunicationStyle,
    FormalityLevel,
    PacingType,
    ToneType,
)
from playbook.domain.value_objects.persona import Persona
from playbook.domain.value_objects.playbook_status import (
    PlaybookStatus,
    PlaybookStatusType,
)
from playbook.domain.value_objects.playbook_version_info import PlaybookVersionInfo
from playbook.domain.value_objects.success_criteria import SuccessCriteria
from playbook.infrastructure.persistence.models import (
    PlaybookExampleModel,
    PlaybookGoalModel,
    PlaybookModel,
    PlaybookObjectionModel,
    PlaybookRuleModel,
    PlaybookStageModel,
    PlaybookTransitionModel,
)


class SqlAlchemyPlaybookRepository(PlaybookRepository):
    """SQLAlchemy implementation of PlaybookRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: PlaybookId) -> Playbook | None:
        """Retrieve Playbook aggregate by ID."""
        stmt = select(PlaybookModel).where(PlaybookModel.id == str(id.value))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_aggregate(model)

    async def find_by_workspace(self, workspace_id: WorkspaceId) -> list[Playbook]:
        """Find all Playbooks in target Workspace."""
        stmt = select(PlaybookModel).where(
            PlaybookModel.workspace_id == str(workspace_id.value)
        )
        result = await self._session.execute(stmt)
        return [self._to_aggregate(m) for m in result.scalars().all()]

    async def find_published_version(
        self, playbook_id: PlaybookId, version_number: int
    ) -> Playbook | None:
        """Find a specific published version snapshot of a Playbook."""
        stmt = select(PlaybookModel).where(
            PlaybookModel.id == str(playbook_id.value),
            PlaybookModel.version_number == version_number,
            PlaybookModel.status == "PUBLISHED",
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_aggregate(model)

    async def save(self, aggregate: Playbook) -> None:
        """Persist or update Playbook aggregate root."""
        stmt = select(PlaybookModel).where(PlaybookModel.id == str(aggregate.id.value))
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            model = self._to_model(aggregate)
            self._session.add(model)
        else:
            existing.name = aggregate.name
            existing.description = aggregate.description
            existing.status = aggregate.status.value.value
            existing.version_number = aggregate.version_info.version_number
            existing.version_label = aggregate.version_info.label
            existing.version_changelog = aggregate.version_info.changelog
            existing.version = aggregate.version

            if aggregate.persona is not None:
                existing.persona_json = {
                    "name": aggregate.persona.name,
                    "role": aggregate.persona.role,
                    "description": aggregate.persona.description,
                    "industry": aggregate.persona.industry,
                }
            else:
                existing.persona_json = None

            existing.communication_style_json = {
                "tone": aggregate.communication_style.tone.value,
                "formality": aggregate.communication_style.formality.value,
                "pacing": aggregate.communication_style.pacing.value,
                "vocabulary_level": aggregate.communication_style.vocabulary_level,
                "use_filler_words": aggregate.communication_style.use_filler_words,
            }

            if aggregate.success_criteria is not None:
                existing.success_criteria_json = {
                    "primary_metric": aggregate.success_criteria.primary_metric,
                    "target_value": aggregate.success_criteria.target_value,
                    "secondary_metrics": list(aggregate.success_criteria.secondary_metrics),
                    "description": aggregate.success_criteria.description,
                }
            else:
                existing.success_criteria_json = None

    async def delete(self, aggregate: Playbook) -> None:
        """Delete Playbook aggregate from persistence."""
        stmt = sql_delete(PlaybookModel).where(PlaybookModel.id == str(aggregate.id.value))
        await self._session.execute(stmt)

    async def find(self, spec: Specification[Playbook]) -> list[Playbook]:
        """Find Playbook aggregates satisfying specification filter."""
        stmt = select(PlaybookModel)
        result = await self._session.execute(stmt)
        aggregates = [self._to_aggregate(m) for m in result.scalars().all()]
        return [a for a in aggregates if spec.is_satisfied_by(a)]

    async def count(self, spec: Specification[Playbook]) -> int:
        """Count Playbook aggregates satisfying specification filter."""
        return len(await self.find(spec))

    def _to_model(self, aggregate: Playbook) -> PlaybookModel:
        """Map domain Playbook to ORM PlaybookModel."""
        persona_json = None
        if aggregate.persona is not None:
            persona_json = {
                "name": aggregate.persona.name,
                "role": aggregate.persona.role,
                "description": aggregate.persona.description,
                "industry": aggregate.persona.industry,
            }

        style_json = {
            "tone": aggregate.communication_style.tone.value,
            "formality": aggregate.communication_style.formality.value,
            "pacing": aggregate.communication_style.pacing.value,
            "vocabulary_level": aggregate.communication_style.vocabulary_level,
            "use_filler_words": aggregate.communication_style.use_filler_words,
        }

        criteria_json = None
        if aggregate.success_criteria is not None:
            criteria_json = {
                "primary_metric": aggregate.success_criteria.primary_metric,
                "target_value": aggregate.success_criteria.target_value,
                "secondary_metrics": list(aggregate.success_criteria.secondary_metrics),
                "description": aggregate.success_criteria.description,
            }

        return PlaybookModel(
            id=str(aggregate.id.value),
            workspace_id=str(aggregate.workspace_id.value),
            name=aggregate.name,
            description=aggregate.description,
            status=aggregate.status.value.value,
            version_number=aggregate.version_info.version_number,
            version_label=aggregate.version_info.label,
            version_changelog=aggregate.version_info.changelog,
            persona_json=persona_json,
            communication_style_json=style_json,
            success_criteria_json=criteria_json,
            version=aggregate.version,
            created_at=aggregate.created_at.value,
            goals=[
                PlaybookGoalModel(
                    id=str(g.id.value),
                    playbook_id=str(aggregate.id.value),
                    name=g.name,
                    description=g.description,
                    priority=g.priority,
                    is_mandatory=g.is_mandatory,
                    created_at=g.created_at.value,
                )
                for g in aggregate.goals
            ],
            stages=[
                PlaybookStageModel(
                    id=str(s.id.value),
                    playbook_id=str(aggregate.id.value),
                    name=s.name,
                    order=s.order,
                    description=s.description,
                    created_at=s.created_at.value,
                )
                for s in aggregate.stages
            ],
            rules=[
                PlaybookRuleModel(
                    id=str(r.id.value),
                    playbook_id=str(aggregate.id.value),
                    name=r.name,
                    condition=r.condition,
                    action=r.action,
                    is_strict=r.is_strict,
                    created_at=r.created_at.value,
                )
                for r in aggregate.rules
            ],
            objections=[
                PlaybookObjectionModel(
                    id=str(o.id.value),
                    playbook_id=str(aggregate.id.value),
                    trigger_phrase=o.trigger_phrase,
                    objection_category=o.objection_category,
                    response_strategy=o.response_strategy,
                    recommended_response=o.recommended_response,
                    created_at=o.created_at.value,
                )
                for o in aggregate.objections
            ],
            examples=[
                PlaybookExampleModel(
                    id=str(e.id.value),
                    playbook_id=str(aggregate.id.value),
                    scenario=e.scenario,
                    user_input=e.user_input,
                    ideal_response=e.ideal_response,
                    explanation=e.explanation,
                    created_at=e.created_at.value,
                )
                for e in aggregate.examples
            ],
            transitions=[
                PlaybookTransitionModel(
                    id=str(t.id.value),
                    playbook_id=str(aggregate.id.value),
                    from_stage_id=str(t.from_stage_id.value),
                    to_stage_id=str(t.to_stage_id.value),
                    condition=t.condition,
                    created_at=t.created_at.value,
                )
                for t in aggregate.transitions
            ],
        )

    @staticmethod
    def _to_aggregate(model: PlaybookModel) -> Playbook:
        """Map ORM PlaybookModel to domain Playbook aggregate root."""
        created_at_dt = model.created_at
        if created_at_dt and created_at_dt.tzinfo is None:
            created_at_dt = created_at_dt.replace(tzinfo=UTC)

        persona = None
        if model.persona_json:
            persona = Persona(
                name=model.persona_json.get("name", ""),
                role=model.persona_json.get("role", ""),
                description=model.persona_json.get("description", ""),
                industry=model.persona_json.get("industry", ""),
            )

        comm_style = CommunicationStyle.default()
        if model.communication_style_json:
            try:
                comm_style = CommunicationStyle(
                    tone=ToneType(model.communication_style_json.get("tone", "PROFESSIONAL")),
                    formality=FormalityLevel(
                        model.communication_style_json.get("formality", "SEMI_FORMAL")
                    ),
                    pacing=PacingType(model.communication_style_json.get("pacing", "MODERATE")),
                    vocabulary_level=model.communication_style_json.get("vocabulary_level", 3),
                    use_filler_words=model.communication_style_json.get("use_filler_words", False),
                )
            except ValueError:
                pass

        criteria = None
        if model.success_criteria_json:
            criteria = SuccessCriteria(
                primary_metric=model.success_criteria_json.get("primary_metric", ""),
                target_value=model.success_criteria_json.get("target_value", 0.0),
                secondary_metrics=tuple(
                    model.success_criteria_json.get("secondary_metrics", [])
                ),
                description=model.success_criteria_json.get("description", ""),
            )

        version_info = PlaybookVersionInfo(
            version_number=model.version_number,
            label=model.version_label,
            changelog=model.version_changelog,
        )

        goals = [
            PlaybookGoal(
                id=EntityId(g.id),
                name=g.name,
                description=g.description,
                priority=g.priority,
                is_mandatory=g.is_mandatory,
                created_at=Timestamp(
                    g.created_at.replace(tzinfo=UTC)
                    if g.created_at and g.created_at.tzinfo is None
                    else g.created_at
                ),
            )
            for g in model.goals
        ]

        stages = [
            PlaybookStage(
                id=EntityId(s.id),
                name=s.name,
                order=s.order,
                description=s.description,
                created_at=Timestamp(
                    s.created_at.replace(tzinfo=UTC)
                    if s.created_at and s.created_at.tzinfo is None
                    else s.created_at
                ),
            )
            for s in model.stages
        ]

        rules = [
            PlaybookRule(
                id=EntityId(r.id),
                name=r.name,
                condition=r.condition,
                action=r.action,
                is_strict=r.is_strict,
                created_at=Timestamp(
                    r.created_at.replace(tzinfo=UTC)
                    if r.created_at and r.created_at.tzinfo is None
                    else r.created_at
                ),
            )
            for r in model.rules
        ]

        objections = [
            PlaybookObjection(
                id=EntityId(o.id),
                trigger_phrase=o.trigger_phrase,
                objection_category=o.objection_category,
                response_strategy=o.response_strategy,
                recommended_response=o.recommended_response,
                created_at=Timestamp(
                    o.created_at.replace(tzinfo=UTC)
                    if o.created_at and o.created_at.tzinfo is None
                    else o.created_at
                ),
            )
            for o in model.objections
        ]

        examples = [
            PlaybookExample(
                id=EntityId(e.id),
                scenario=e.scenario,
                user_input=e.user_input,
                ideal_response=e.ideal_response,
                explanation=e.explanation,
                created_at=Timestamp(
                    e.created_at.replace(tzinfo=UTC)
                    if e.created_at and e.created_at.tzinfo is None
                    else e.created_at
                ),
            )
            for e in model.examples
        ]

        transitions = [
            PlaybookTransition(
                id=EntityId(t.id),
                from_stage_id=EntityId(t.from_stage_id),
                to_stage_id=EntityId(t.to_stage_id),
                condition=t.condition,
                created_at=Timestamp(
                    t.created_at.replace(tzinfo=UTC)
                    if t.created_at and t.created_at.tzinfo is None
                    else t.created_at
                ),
            )
            for t in model.transitions
        ]

        return Playbook(
            id=PlaybookId(model.id),
            workspace_id=WorkspaceId(model.workspace_id),
            name=model.name,
            description=model.description,
            status=PlaybookStatus(PlaybookStatusType(model.status)),
            version_info=version_info,
            persona=persona,
            communication_style=comm_style,
            success_criteria=criteria,
            goals=goals,
            stages=stages,
            rules=rules,
            objections=objections,
            examples=examples,
            transitions=transitions,
            created_at=Timestamp(created_at_dt),
            version=model.version,
        )
