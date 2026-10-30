"""
Conversation Aggregate Root for Conversation Bounded Context.

Central transactional boundary managing participants, messages, memory,
timeline, and lifecycle of a customer-agent conversation.
"""

from __future__ import annotations

from collections.abc import Sequence

from shared.kernel.aggregate_root import AggregateRoot
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import (
    AgentId,
    ConversationId,
    EntityId,
    Timestamp,
    WorkspaceId,
)

from conversation.domain.entities.conversation_memory import ConversationMemory
from conversation.domain.entities.conversation_timeline import (
    ConversationTimeline,
)
from conversation.domain.entities.message import Message
from conversation.domain.entities.participant import Participant
from conversation.domain.events.conversation_ended import ConversationEnded
from conversation.domain.events.conversation_paused import ConversationPaused
from conversation.domain.events.conversation_resumed import ConversationResumed
from conversation.domain.events.conversation_summarized import (
    ConversationSummarized,
)
from conversation.domain.events.message_added import MessageAdded
from conversation.domain.events.participant_joined import ParticipantJoined
from conversation.domain.events.participant_left import ParticipantLeft
from conversation.domain.value_objects.conversation_channel import (
    ConversationChannel,
)
from conversation.domain.value_objects.conversation_language import (
    ConversationLanguage,
)
from conversation.domain.value_objects.conversation_metrics import (
    ConversationMetrics,
)
from conversation.domain.value_objects.conversation_status import (
    ConversationStatus,
)
from conversation.domain.value_objects.conversation_summary import (
    ConversationSummary,
)


class Conversation(AggregateRoot[ConversationId]):
    """Conversation Aggregate Root.

    Invariants enforced:
    - Cannot add messages after conversation ends.
    - Every message must belong to an existing participant.
    - At least one participant must exist.
    - Conversation must always have one Agent participant.
    - Messages are append-only.
    - Timeline events are immutable.
    - Memory belongs only to one Conversation.
    """

    def __init__(
        self,
        id: ConversationId,
        workspace_id: WorkspaceId,
        agent_id: AgentId,
        channel: ConversationChannel,
        language: ConversationLanguage | None = None,
        status: ConversationStatus | None = None,
        summary: ConversationSummary | None = None,
        metrics: ConversationMetrics | None = None,
        participants: Sequence[Participant] = (),
        messages: Sequence[Message] = (),
        memory: ConversationMemory | None = None,
        timeline: ConversationTimeline | None = None,
        created_at: Timestamp | None = None,
        version: int = 1,
    ) -> None:
        super().__init__(id=id, created_at=created_at, version=version)

        self._workspace_id = workspace_id
        self._agent_id = agent_id
        self._channel = channel
        self._language = language or ConversationLanguage.default()
        self._status = status or ConversationStatus.active()
        self._summary = summary
        self._metrics = metrics or ConversationMetrics.empty()
        self._participants: dict[EntityId, Participant] = {p.id: p for p in participants}
        self._messages: list[Message] = list(messages)
        self._memory = memory or ConversationMemory(id=EntityId())
        self._timeline = timeline or ConversationTimeline(id=EntityId())

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def workspace_id(self) -> WorkspaceId:
        return self._workspace_id

    @property
    def agent_id(self) -> AgentId:
        return self._agent_id

    @property
    def channel(self) -> ConversationChannel:
        return self._channel

    @property
    def language(self) -> ConversationLanguage:
        return self._language

    @property
    def status(self) -> ConversationStatus:
        return self._status

    @property
    def summary(self) -> ConversationSummary | None:
        return self._summary

    @property
    def metrics(self) -> ConversationMetrics:
        return self._metrics

    @property
    def participants(self) -> tuple[Participant, ...]:
        return tuple(self._participants.values())

    @property
    def messages(self) -> tuple[Message, ...]:
        return tuple(self._messages)

    @property
    def memory(self) -> ConversationMemory:
        return self._memory

    @property
    def timeline(self) -> ConversationTimeline:
        return self._timeline

    @property
    def message_count(self) -> int:
        return len(self._messages)

    @property
    def participant_count(self) -> int:
        return len(self._participants)

    # ── Query ─────────────────────────────────────────────────────────────

    def get_participant(self, participant_id: EntityId) -> Participant | None:
        """Find a participant by ID."""
        return self._participants.get(participant_id)

    # ── Commands ──────────────────────────────────────────────────────────

    def add_participant(self, participant: Participant) -> Result[None]:
        """Add a Participant to the Conversation.

        Args:
            participant: Participant entity to add.

        Returns:
            Result indicating success or failure.
        """
        if self._status.is_ended:
            return Result.fail(Error("INVALID_STATE", "Cannot add participant to ended conversation"))

        if participant.id in self._participants:
            return Result.fail(Error("CONFLICT", f"Participant '{participant.id.value}' already in conversation"))

        self._participants[participant.id] = participant
        self._timeline.record("PARTICIPANT_JOINED", f"{participant.name} ({participant.role.value.value}) joined")
        self._raise_event(
            ParticipantJoined(
                conversation_id=str(self.id.value),
                participant_id=str(participant.id.value),
                role=participant.role.value.value,
                name=participant.name,
            )
        )
        return Result.ok(None)

    def remove_participant(self, participant_id: EntityId) -> Result[None]:
        """Remove a Participant from the Conversation.

        Cannot remove the last Agent participant.

        Args:
            participant_id: ID of the participant to remove.

        Returns:
            Result indicating success or failure.
        """
        if participant_id not in self._participants:
            return Result.fail(Error("NOT_FOUND", f"Participant '{participant_id.value}' not found"))

        participant = self._participants[participant_id]

        # Cannot remove the last agent
        if participant.role.is_agent:
            agent_count = sum(1 for p in self._participants.values() if p.role.is_agent and p.id != participant_id)
            if agent_count == 0:
                return Result.fail(Error("INVARIANT_VIOLATION", "Cannot remove the last Agent participant"))

        participant.deactivate()
        del self._participants[participant_id]
        self._timeline.record("PARTICIPANT_LEFT", f"{participant.name} left")
        self._raise_event(
            ParticipantLeft(
                conversation_id=str(self.id.value),
                participant_id=str(participant_id.value),
                role=participant.role.value.value,
            )
        )
        return Result.ok(None)

    def add_message(self, message: Message) -> Result[None]:
        """Append a Message to the Conversation.

        Enforces invariants:
        - Cannot add messages after conversation ends.
        - Message participant must exist in conversation.

        Args:
            message: Message entity to append.

        Returns:
            Result indicating success or failure.
        """
        if self._status.is_ended:
            return Result.fail(Error("INVALID_STATE", "Cannot add message to ended conversation"))

        if message.participant_id not in self._participants:
            return Result.fail(
                Error("INVARIANT_VIOLATION", f"Participant '{message.participant_id.value}' not found in conversation")
            )

        self._messages.append(message)
        self._memory.append_turn(
            role=message.role.value.value.lower(),
            content=message.content,
        )
        self._timeline.record("MESSAGE", f"Message #{message.sequence_number} from {message.role.value.value}")

        # Update metrics
        agent_msgs = self._metrics.agent_messages + (1 if message.role.is_agent else 0)
        customer_msgs = self._metrics.customer_messages + (1 if message.role.is_customer else 0)
        self._metrics = ConversationMetrics(
            duration_seconds=self._metrics.duration_seconds,
            total_messages=self._metrics.total_messages + 1,
            agent_messages=agent_msgs,
            customer_messages=customer_msgs,
            turn_count=self._metrics.turn_count + 1,
        )

        self._raise_event(
            MessageAdded(
                conversation_id=str(self.id.value),
                message_id=str(message.id.value),
                participant_id=str(message.participant_id.value),
                participant_role=message.role.value.value,
                sequence_number=message.sequence_number,
            )
        )
        return Result.ok(None)

    def pause(self, reason: str = "") -> Result[None]:
        """Pause an active Conversation.

        Args:
            reason: Human-readable reason for pausing.

        Returns:
            Result indicating success or failure.
        """
        if not self._status.is_active:
            return Result.fail(Error("INVALID_STATE", "Only active conversations can be paused"))

        self._status = ConversationStatus.paused()
        self._timeline.record("PAUSED", reason or "Conversation paused")
        self._raise_event(
            ConversationPaused(
                conversation_id=str(self.id.value),
                reason=reason,
            )
        )
        return Result.ok(None)

    def resume(self) -> Result[None]:
        """Resume a paused Conversation.

        Returns:
            Result indicating success or failure.
        """
        if not self._status.is_paused:
            return Result.fail(Error("INVALID_STATE", "Only paused conversations can be resumed"))

        self._status = ConversationStatus.active()
        self._timeline.record("RESUMED", "Conversation resumed")
        self._raise_event(
            ConversationResumed(conversation_id=str(self.id.value))
        )
        return Result.ok(None)

    def end(self, reason: str = "") -> Result[None]:
        """End the Conversation.

        Args:
            reason: Human-readable reason for ending.

        Returns:
            Result indicating success or failure.
        """
        if self._status.is_ended:
            return Result.fail(Error("INVALID_STATE", "Conversation is already ended"))

        self._status = ConversationStatus.ended()
        self._version += 1
        self._timeline.record("ENDED", reason or "Conversation ended")
        self._raise_event(
            ConversationEnded(
                conversation_id=str(self.id.value),
                reason=reason,
                total_messages=self.message_count,
            )
        )
        return Result.ok(None)

    def summarize(self, summary: ConversationSummary) -> Result[None]:
        """Attach a summary to an ended Conversation.

        Args:
            summary: ConversationSummary value object.

        Returns:
            Result indicating success or failure.
        """
        if not self._status.is_ended:
            return Result.fail(Error("INVALID_STATE", "Can only summarize ended conversations"))

        self._summary = summary
        self._timeline.record("SUMMARIZED", f"Summary: {summary.text[:100]}")
        self._raise_event(
            ConversationSummarized(
                conversation_id=str(self.id.value),
                summary_text=summary.text,
            )
        )
        return Result.ok(None)
