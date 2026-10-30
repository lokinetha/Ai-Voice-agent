"""
Unit tests for Conversation Domain Layer — Aggregate Root, Entities, Value Objects,
Factory, Specifications, and Domain Service.
"""

from __future__ import annotations

import unittest

from conversation.domain.entities.conversation import Conversation
from conversation.domain.entities.conversation_memory import ConversationMemory
from conversation.domain.entities.conversation_timeline import (
    ConversationTimeline,
)
from conversation.domain.entities.message import Message
from conversation.domain.entities.participant import Participant
from conversation.domain.events.conversation_ended import ConversationEnded
from conversation.domain.events.conversation_paused import ConversationPaused
from conversation.domain.events.conversation_resumed import ConversationResumed
from conversation.domain.events.conversation_started import ConversationStarted
from conversation.domain.events.conversation_summarized import (
    ConversationSummarized,
)
from conversation.domain.events.message_added import MessageAdded
from conversation.domain.events.participant_joined import ParticipantJoined
from conversation.domain.events.participant_left import ParticipantLeft
from conversation.domain.factories.conversation_factory import (
    ConversationFactory,
)
from conversation.domain.services.conversation_lifecycle_service import (
    ConversationLifecycleService,
)
from conversation.domain.specifications.active_conversation_spec import (
    ActiveConversationSpec,
)
from conversation.domain.specifications.can_accept_message_spec import (
    CanAcceptMessageSpec,
)
from conversation.domain.value_objects.conversation_channel import (
    ConversationChannel,
)
from conversation.domain.value_objects.conversation_status import (
    ConversationStatusType,
)
from conversation.domain.value_objects.conversation_summary import (
    ConversationSummary,
)
from conversation.domain.value_objects.participant_role import ParticipantRole
from shared.kernel.value_objects import AgentId, EntityId, MessageId, WorkspaceId


class TestConversationFactory(unittest.TestCase):
    """Tests for ConversationFactory."""

    def test_factory_creates_conversation_with_two_participants(self) -> None:
        conv = ConversationFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            agent_id=AgentId("agent-1"),
            channel=ConversationChannel.voice(),
            participant_name="John Doe",
            customer_external_id="cust-ext-123",
        )

        self.assertEqual(conv.participant_count, 2)
        self.assertEqual(conv.status.value, ConversationStatusType.ACTIVE)
        self.assertEqual(conv.message_count, 0)

        roles = {p.role.value.value for p in conv.participants}
        self.assertIn("AGENT", roles)
        self.assertIn("CUSTOMER", roles)

        events = conv.domain_events
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], ConversationStarted)

    def test_factory_records_timeline_entry(self) -> None:
        conv = ConversationFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            agent_id=AgentId("agent-1"),
            channel=ConversationChannel.webchat(),
            participant_name="Jane",
        )
        self.assertGreaterEqual(conv.timeline.entry_count, 1)


class TestConversationAggregate(unittest.TestCase):
    """Tests for Conversation Aggregate Root invariants."""

    def _make_conversation(self) -> Conversation:
        return ConversationFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            agent_id=AgentId("agent-1"),
            channel=ConversationChannel.voice(),
            participant_name="Customer",
        )

    def test_add_message_success(self) -> None:
        conv = self._make_conversation()
        conv.clear_events()

        customer = [p for p in conv.participants if p.role.is_customer][0]
        msg = Message(
            id=MessageId(),
            participant_id=customer.id,
            role=ParticipantRole.customer(),
            content="Hello, I need help.",
            sequence_number=0,
        )

        result = conv.add_message(msg)
        self.assertTrue(result.is_success)
        self.assertEqual(conv.message_count, 1)
        self.assertEqual(conv.metrics.total_messages, 1)
        self.assertEqual(conv.metrics.customer_messages, 1)
        self.assertTrue(any(isinstance(e, MessageAdded) for e in conv.domain_events))

    def test_cannot_add_message_after_ended(self) -> None:
        conv = self._make_conversation()
        conv.end("done")
        conv.clear_events()

        customer = [p for p in conv.participants if p.role.is_customer][0]
        msg = Message(
            id=MessageId(),
            participant_id=customer.id,
            role=ParticipantRole.customer(),
            content="Late message",
            sequence_number=0,
        )

        result = conv.add_message(msg)
        self.assertTrue(result.is_failure)
        self.assertEqual(result.error.code, "INVALID_STATE")

    def test_message_must_belong_to_existing_participant(self) -> None:
        conv = self._make_conversation()
        msg = Message(
            id=MessageId(),
            participant_id=EntityId("non-existent"),
            role=ParticipantRole.customer(),
            content="Hello",
            sequence_number=0,
        )

        result = conv.add_message(msg)
        self.assertTrue(result.is_failure)
        self.assertEqual(result.error.code, "INVARIANT_VIOLATION")

    def test_cannot_remove_last_agent(self) -> None:
        conv = self._make_conversation()
        agent = [p for p in conv.participants if p.role.is_agent][0]

        result = conv.remove_participant(agent.id)
        self.assertTrue(result.is_failure)
        self.assertEqual(result.error.code, "INVARIANT_VIOLATION")

    def test_add_and_remove_participant(self) -> None:
        conv = self._make_conversation()
        conv.clear_events()

        supervisor = Participant(
            id=EntityId(),
            name="Supervisor Jane",
            role=ParticipantRole.supervisor(),
        )
        add_res = conv.add_participant(supervisor)
        self.assertTrue(add_res.is_success)
        self.assertEqual(conv.participant_count, 3)
        self.assertTrue(any(isinstance(e, ParticipantJoined) for e in conv.domain_events))

        rem_res = conv.remove_participant(supervisor.id)
        self.assertTrue(rem_res.is_success)
        self.assertEqual(conv.participant_count, 2)
        self.assertTrue(any(isinstance(e, ParticipantLeft) for e in conv.domain_events))

    def test_pause_resume_lifecycle(self) -> None:
        conv = self._make_conversation()
        conv.clear_events()

        pause_res = conv.pause("customer on hold")
        self.assertTrue(pause_res.is_success)
        self.assertTrue(conv.status.is_paused)
        self.assertTrue(any(isinstance(e, ConversationPaused) for e in conv.domain_events))

        resume_res = conv.resume()
        self.assertTrue(resume_res.is_success)
        self.assertTrue(conv.status.is_active)
        self.assertTrue(any(isinstance(e, ConversationResumed) for e in conv.domain_events))

    def test_cannot_pause_non_active(self) -> None:
        conv = self._make_conversation()
        conv.pause("first pause")
        result = conv.pause("second pause")
        self.assertTrue(result.is_failure)

    def test_cannot_resume_non_paused(self) -> None:
        conv = self._make_conversation()
        result = conv.resume()
        self.assertTrue(result.is_failure)

    def test_end_conversation(self) -> None:
        conv = self._make_conversation()
        conv.clear_events()

        end_res = conv.end("call completed")
        self.assertTrue(end_res.is_success)
        self.assertTrue(conv.status.is_ended)
        self.assertTrue(any(isinstance(e, ConversationEnded) for e in conv.domain_events))

    def test_cannot_end_twice(self) -> None:
        conv = self._make_conversation()
        conv.end("first end")
        result = conv.end("second end")
        self.assertTrue(result.is_failure)

    def test_summarize_only_after_ended(self) -> None:
        conv = self._make_conversation()
        summary = ConversationSummary(text="Good call", sentiment="positive")

        # Cannot summarize active conversation
        result = conv.summarize(summary)
        self.assertTrue(result.is_failure)

        # End, then summarize
        conv.end("done")
        conv.clear_events()
        result = conv.summarize(summary)
        self.assertTrue(result.is_success)
        self.assertIsNotNone(conv.summary)
        self.assertTrue(any(isinstance(e, ConversationSummarized) for e in conv.domain_events))


class TestConversationMemory(unittest.TestCase):
    """Tests for ConversationMemory Entity."""

    def test_append_and_get_context(self) -> None:
        memory = ConversationMemory(id=EntityId())
        memory.append_turn("agent", "Hello!")
        memory.append_turn("customer", "Hi there")

        ctx = memory.get_context()
        self.assertEqual(len(ctx), 2)
        self.assertEqual(ctx[0]["role"], "agent")

    def test_truncation_at_max_entries(self) -> None:
        memory = ConversationMemory(id=EntityId())
        for i in range(120):
            memory.append_turn("agent", f"Message {i}")

        self.assertEqual(len(memory.context_window), 100)


class TestConversationTimeline(unittest.TestCase):
    """Tests for ConversationTimeline Entity."""

    def test_record_creates_immutable_entry(self) -> None:
        timeline = ConversationTimeline(id=EntityId())
        timeline.record("STARTED", "Conversation started")

        entries = timeline.entries
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].event_type, "STARTED")


class TestSpecifications(unittest.TestCase):
    """Tests for domain Specifications."""

    def _make_conv(self) -> Conversation:
        return ConversationFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            agent_id=AgentId("agent-1"),
            channel=ConversationChannel.voice(),
            participant_name="Customer",
        )

    def test_active_spec(self) -> None:
        spec = ActiveConversationSpec()
        conv = self._make_conv()
        self.assertTrue(spec.is_satisfied_by(conv))

        conv.end("done")
        self.assertFalse(spec.is_satisfied_by(conv))

    def test_can_accept_message_spec(self) -> None:
        spec = CanAcceptMessageSpec()
        conv = self._make_conv()
        self.assertTrue(spec.is_satisfied_by(conv))

        conv.pause("hold")
        self.assertTrue(spec.is_satisfied_by(conv))  # Paused can still accept

        conv.resume()
        conv.end("done")
        self.assertFalse(spec.is_satisfied_by(conv))


class TestConversationLifecycleService(unittest.TestCase):
    """Tests for ConversationLifecycleService."""

    def test_end_conversation_via_service(self) -> None:
        svc = ConversationLifecycleService()
        conv = ConversationFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            agent_id=AgentId("agent-1"),
            channel=ConversationChannel.voice(),
            participant_name="Customer",
        )

        result = svc.end_conversation(conv, "call done")
        self.assertTrue(result.is_success)
        self.assertTrue(conv.status.is_ended)

    def test_can_accept_message(self) -> None:
        svc = ConversationLifecycleService()
        conv = ConversationFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            agent_id=AgentId("agent-1"),
            channel=ConversationChannel.voice(),
            participant_name="Customer",
        )

        self.assertTrue(svc.can_accept_message(conv))
        conv.end("done")
        self.assertFalse(svc.can_accept_message(conv))


if __name__ == "__main__":
    unittest.main()
