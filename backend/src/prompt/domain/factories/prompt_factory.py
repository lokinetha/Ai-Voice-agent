"""
PromptFactory for Prompt Bounded Context.

Encapsulates construction of new Prompt Aggregate Roots.
"""

from __future__ import annotations

from shared.kernel.value_objects import PromptId, WorkspaceId

from prompt.domain.entities.prompt import Prompt
from prompt.domain.events.prompt_created import PromptCreated
from prompt.domain.value_objects.prompt_template import PromptTemplate


class PromptFactory:
    """Factory constructing new Prompt Aggregate Roots."""

    @classmethod
    def create(
        cls,
        workspace_id: WorkspaceId,
        name: str,
        description: str = "",
        template: PromptTemplate | None = None,
        prompt_id: PromptId | None = None,
    ) -> Prompt:
        """Create and initialize a new Prompt aggregate root.

        Args:
            workspace_id: Owning WorkspaceId.
            name: Prompt display title.
            description: Prompt description.
            template: Optional compilation PromptTemplate.
            prompt_id: Optional explicit PromptId.

        Returns:
            Initialized Prompt aggregate root.
        """
        id_val = prompt_id or PromptId()

        prompt = Prompt(
            id=id_val,
            workspace_id=workspace_id,
            name=name,
            description=description,
            template=template or PromptTemplate(),
        )

        prompt._raise_event(
            PromptCreated(
                prompt_id=str(id_val.value),
                workspace_id=str(workspace_id.value),
                name=prompt.name,
            )
        )

        return prompt
