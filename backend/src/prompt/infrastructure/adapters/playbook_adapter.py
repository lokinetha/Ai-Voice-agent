"""
PlaybookRepositoryAdapter implementing PlaybookQueryPort.

Adapts the PlaybookRepository interface into the PlaybookQueryPort
consumed by the Prompt compilation domain service.
"""

from __future__ import annotations

from playbook.domain.repositories.playbook_repository import PlaybookRepository
from shared.kernel.value_objects import PlaybookId

from prompt.domain.ports.playbook_port import (
    PlaybookDataDTO,
    PlaybookExampleData,
    PlaybookGoalData,
    PlaybookObjectionData,
    PlaybookQueryPort,
    PlaybookRuleData,
    PlaybookStageData,
)


class PlaybookRepositoryAdapter(PlaybookQueryPort):
    """Adapter bridging PlaybookRepository to PlaybookQueryPort."""

    def __init__(self, playbook_repository: PlaybookRepository) -> None:
        self._playbook_repo = playbook_repository

    async def get_published_playbook(
        self, playbook_id: str, version_number: int | None = None
    ) -> PlaybookDataDTO | None:
        """Fetch published Playbook and convert into read-only PlaybookDataDTO.

        Args:
            playbook_id: Playbook ID string.
            version_number: Optional version number.

        Returns:
            PlaybookDataDTO if found and published, else None.
        """
        pb_id = PlaybookId(playbook_id)

        if version_number is not None:
            pb = await self._playbook_repo.find_published_version(pb_id, version_number)
        else:
            pb = await self._playbook_repo.get_by_id(pb_id)

        if pb is None or not pb.status.is_published:
            return None

        persona_name = pb.persona.name if pb.persona else ""
        persona_role = pb.persona.role if pb.persona else ""
        persona_desc = pb.persona.description if pb.persona else ""

        goals_data = tuple(
            PlaybookGoalData(
                name=g.name,
                description=g.description,
                priority=g.priority,
                is_mandatory=g.is_mandatory,
            )
            for g in pb.goals
        )

        stages_data = tuple(
            PlaybookStageData(
                name=s.name,
                order=s.order,
                description=s.description,
                goals=tuple(
                    PlaybookGoalData(
                        name=g.name,
                        description=g.description,
                        priority=g.priority,
                        is_mandatory=g.is_mandatory,
                    )
                    for g in s.goals
                ),
            )
            for s in pb.stages
        )

        rules_data = tuple(
            PlaybookRuleData(
                name=r.name,
                condition=r.condition,
                action=r.action,
                is_strict=r.is_strict,
            )
            for r in pb.rules
        )

        objections_data = tuple(
            PlaybookObjectionData(
                trigger_phrase=o.trigger_phrase,
                objection_category=o.objection_category,
                response_strategy=o.response_strategy,
                recommended_response=o.recommended_response,
            )
            for o in pb.objections
        )

        examples_data = tuple(
            PlaybookExampleData(
                scenario=e.scenario,
                user_input=e.user_input,
                ideal_response=e.ideal_response,
                explanation=e.explanation,
            )
            for e in pb.examples
        )

        return PlaybookDataDTO(
            playbook_id=str(pb.id.value),
            version_number=pb.version_info.version_number,
            name=pb.name,
            description=pb.description,
            status=pb.status.value.value,
            persona_name=persona_name,
            persona_role=persona_role,
            persona_description=persona_desc,
            tone=pb.communication_style.tone.value,
            formality=pb.communication_style.formality.value,
            pacing=pb.communication_style.pacing.value,
            goals=goals_data,
            stages=stages_data,
            rules=rules_data,
            objections=objections_data,
            examples=examples_data,
        )
