"""
PlaybookFactory for Playbook Bounded Context.

Encapsulates construction of new Playbook Aggregate Roots.
"""

from __future__ import annotations

from collections.abc import Sequence

from shared.kernel.value_objects import PlaybookId, WorkspaceId

from playbook.domain.entities.playbook import Playbook
from playbook.domain.entities.playbook_goal import PlaybookGoal
from playbook.domain.events.playbook_created import PlaybookCreated
from playbook.domain.value_objects.communication_style import CommunicationStyle
from playbook.domain.value_objects.persona import Persona
from playbook.domain.value_objects.success_criteria import SuccessCriteria


class PlaybookFactory:
    """Factory constructing new Playbook Aggregate Roots."""

    @classmethod
    def create(
        cls,
        workspace_id: WorkspaceId,
        name: str,
        description: str = "",
        persona: Persona | None = None,
        communication_style: CommunicationStyle | None = None,
        success_criteria: SuccessCriteria | None = None,
        initial_goals: Sequence[PlaybookGoal] = (),
        playbook_id: PlaybookId | None = None,
    ) -> Playbook:
        """Create and initialize a new Playbook aggregate root.

        Args:
            workspace_id: Owning WorkspaceId.
            name: Playbook title/name.
            description: Detailed playbook description.
            persona: Optional Persona value object.
            communication_style: Optional CommunicationStyle.
            success_criteria: Optional SuccessCriteria.
            initial_goals: Optional list of initial PlaybookGoal entities.
            playbook_id: Optional explicit PlaybookId.

        Returns:
            Initialized Playbook aggregate root.
        """
        id_val = playbook_id or PlaybookId()

        pb = Playbook(
            id=id_val,
            workspace_id=workspace_id,
            name=name,
            description=description,
            persona=persona,
            communication_style=communication_style,
            success_criteria=success_criteria,
            goals=initial_goals,
        )

        pb._raise_event(
            PlaybookCreated(
                playbook_id=str(id_val.value),
                workspace_id=str(workspace_id.value),
                name=pb.name,
            )
        )

        return pb
