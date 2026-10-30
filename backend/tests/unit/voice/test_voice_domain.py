"""
Unit tests for Voice Domain Layer — Aggregate Root, Entities, Value Objects,
Events, Factory, Specifications, and Domain Services.
"""

from __future__ import annotations

import unittest

from shared.kernel.value_objects import (
    AgentId,
    ConversationId,
    WorkspaceId,
)
from voice.domain.events.agent_response_generated import AgentResponseGenerated
from voice.domain.events.speech_synthesized import SpeechSynthesized
from voice.domain.events.speech_transcribed import SpeechTranscribed
from voice.domain.events.voice_session_ended import VoiceSessionEnded
from voice.domain.events.voice_session_paused import VoiceSessionPaused
from voice.domain.events.voice_session_started import VoiceSessionStarted
from voice.domain.factories.voice_session_factory import VoiceSessionFactory
from voice.domain.services.voice_session_lifecycle_service import (
    VoiceSessionLifecycleService,
)
from voice.domain.specifications.active_voice_session_spec import (
    ActiveVoiceSessionSpec,
)
from voice.domain.specifications.can_accept_audio_spec import CanAcceptAudioSpec
from voice.domain.value_objects.audio_format import AudioFormat
from voice.domain.value_objects.speech_confidence import SpeechConfidence
from voice.domain.value_objects.voice_session_status import (
    VoiceSessionStatusType,
)


class TestVoiceSessionFactory(unittest.TestCase):
    """Tests for VoiceSessionFactory."""

    def test_factory_creates_voice_session_with_defaults(self) -> None:
        session = VoiceSessionFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            agent_id=AgentId("ag-1"),
            conversation_id=ConversationId("conv-1"),
        )

        self.assertEqual(session.status.value, VoiceSessionStatusType.IDLE)
        self.assertEqual(len(session.participants), 2)
        self.assertEqual(len(session.streams), 2)

        stream_types = [s.stream_type for s in session.streams]
        self.assertIn("INBOUND", stream_types)
        self.assertIn("OUTBOUND", stream_types)


class TestVoiceSessionAggregate(unittest.TestCase):
    """Tests for VoiceSession Aggregate Root rules and state machine."""

    def _make_session(self) -> VoiceSessionFactory:
        return VoiceSessionFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            agent_id=AgentId("ag-1"),
            conversation_id=ConversationId("conv-1"),
        )

    def test_voice_session_lifecycle_and_turn_flow(self) -> None:
        session = self._make_session()
        session.clear_events()

        # Start session
        res = session.start()
        self.assertTrue(res.is_success)
        self.assertEqual(session.status.value, VoiceSessionStatusType.ACTIVE)
        self.assertTrue(any(isinstance(e, VoiceSessionStarted) for e in session.domain_events))

        # Start turn
        session.clear_events()
        turn_res = session.start_turn("USER")
        self.assertTrue(turn_res.is_success)
        turn = turn_res.value
        self.assertEqual(turn.speaker_role, "USER")

        # Record speech transcription
        stt_res = session.record_speech_transcribed(str(turn.id.value), "Hello agent", 0.95)
        self.assertTrue(stt_res.is_success)
        self.assertTrue(any(isinstance(e, SpeechTranscribed) for e in session.domain_events))

        # Start agent turn & record response
        session.clear_events()
        agent_turn_res = session.start_turn("AGENT")
        agent_turn = agent_turn_res.value

        resp_res = session.record_agent_response(str(agent_turn.id.value), "Hello customer")
        self.assertTrue(resp_res.is_success)
        self.assertTrue(any(isinstance(e, AgentResponseGenerated) for e in session.domain_events))

        # Record synthesis
        synth_res = session.record_speech_synthesized(str(agent_turn.id.value), 1024)
        self.assertTrue(synth_res.is_success)
        self.assertTrue(any(isinstance(e, SpeechSynthesized) for e in session.domain_events))

        # Pause and resume
        session.clear_events()
        self.assertTrue(session.pause().is_success)
        self.assertEqual(session.status.value, VoiceSessionStatusType.PAUSED)
        self.assertTrue(any(isinstance(e, VoiceSessionPaused) for e in session.domain_events))

        self.assertTrue(session.resume().is_success)
        self.assertEqual(session.status.value, VoiceSessionStatusType.ACTIVE)

        # End session
        session.clear_events()
        end_res = session.end("Call completed")
        self.assertTrue(end_res.is_success)
        self.assertEqual(session.status.value, VoiceSessionStatusType.ENDED)
        self.assertTrue(any(isinstance(e, VoiceSessionEnded) for e in session.domain_events))

    def test_value_object_validations(self) -> None:
        with self.assertRaises(ValueError):
            AudioFormat(sample_rate=-1)

        with self.assertRaises(ValueError):
            SpeechConfidence(value=1.5)


class TestSpecifications(unittest.TestCase):
    """Tests for Voice specifications."""

    def test_active_and_can_accept_specs(self) -> None:
        active_spec = ActiveVoiceSessionSpec()
        accept_spec = CanAcceptAudioSpec()

        session = VoiceSessionFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            agent_id=AgentId("ag-1"),
            conversation_id=ConversationId("conv-1"),
        )
        self.assertFalse(active_spec.is_satisfied_by(session))
        self.assertFalse(accept_spec.is_satisfied_by(session))

        session.start()
        self.assertTrue(active_spec.is_satisfied_by(session))
        self.assertTrue(accept_spec.is_satisfied_by(session))


class TestVoiceSessionLifecycleService(unittest.TestCase):
    """Tests for VoiceSessionLifecycleService."""

    def test_lifecycle_service_rules(self) -> None:
        svc = VoiceSessionLifecycleService()
        session = VoiceSessionFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            agent_id=AgentId("ag-1"),
            conversation_id=ConversationId("conv-1"),
        )

        self.assertTrue(svc.can_start_session(session).is_success)
        self.assertTrue(svc.can_pause_session(session).is_failure)

        session.start()
        self.assertTrue(svc.can_pause_session(session).is_success)
        self.assertTrue(svc.can_end_session(session).is_success)


if __name__ == "__main__":
    unittest.main()
