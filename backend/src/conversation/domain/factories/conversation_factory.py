"""
ConversationFactory for Conversation Bounded Context.

Encapsulates construction of new Conversation Aggregate Roots with
mandatory Agent and Customer participants, Memory, and Timeline.
"""

from __future__ import annotations

from shared.kernel.value_objects import AgentId, ConversationId, EntityId, WorkspaceId

from conversation.domain.entities.conversation import Conversation
from conversation.domain.entities.conversation_memory import ConversationMemory
from conversation.domain.entities.conversation_timeline import (
    ConversationTimeline,
)
from conversation.domain.entities.participant import Participant
from conversation.domain.events.conversation_started import ConversationStarted
from conversation.domain.value_objects.conversation_channel import (
    ConversationChannel,
)
from conversation.domain.value_objects.conversation_language import (
    ConversationLanguage,
)
from conversation.domain.value_objects.participant_role import ParticipantRole


class ConversationFactory:
    """Factory constructing new Conversation Aggregate Roots."""

    @classmethod
    def create(
        cls,
        workspace_id: WorkspaceId,
        agent_id: AgentId,
        channel: ConversationChannel,
        participant_name: str,
        customer_external_id: str = "",
        language: ConversationLanguage | None = None,
        conv_id: ConversationId | None = None,
    ) -> Conversation:
        """Create and initialize a new Conversation aggregate root.

        Automatically creates:
        - Agent participant
        - Customer participant
        - ConversationMemory entity
        - ConversationTimeline entity
        - ConversationStarted domain event

        Args:
            workspace_id: Owning WorkspaceId.
            agent_id: AgentId of the handling agent.
            channel: Communication channel.
            participant_name: Customer participant display name.
            customer_external_id: Optional external customer identifier.
            language: Optional conversation language.
            conv_id: Optional explicit ConversationId.

        Returns:
            Initialized Conversation aggregate root.
        """
        id_val = conv_id or ConversationId()

        agent_participant = Participant(
            id=EntityId(),
            name="AI Agent",
            role=ParticipantRole.agent(),
            external_id=str(agent_id.value),
        )
        customer_participant = Participant(
            id=EntityId(),
            name=participant_name,
            role=ParticipantRole.customer(),
            external_id=customer_external_id,
        )

        memory = ConversationMemory(id=EntityId())
        timeline = ConversationTimeline(id=EntityId())

        conv = Conversation(
            id=id_val,
            workspace_id=workspace_id,
            agent_id=agent_id,
            channel=channel,
            language=language,
            participants=[agent_participant, customer_participant],
            memory=memory,
            timeline=timeline,
        )

        timeline.record("STARTED", f"Conversation started on {channel.value.value} channel")

        conv._raise_event(
            ConversationStarted(
                conversation_id=str(id_val.value),
                workspace_id=str(workspace_id.value),
                agent_id=str(agent_id.value),
                channel=channel.value.value,
            )
        )

        return conv
