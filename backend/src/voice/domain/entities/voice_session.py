"""
VoiceSession Aggregate Root for Voice Bounded Context.

Manages real-time voice session lifecycle, stream state, and turn flow.

Rule enforced:
- VoiceSession owns voice-session lifecycle ONLY.
- Conversation remains the source of truth for conversational messages.
- Does NOT duplicate Conversation or Message entities.
- Interacts with Conversation strictly via application ports.
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

from voice.domain.entities.audio_stream import AudioStream
from voice.domain.entities.voice_participant import VoiceParticipant
from voice.domain.entities.voice_turn import VoiceTurn
from voice.domain.events.agent_response_generated import AgentResponseGenerated
from voice.domain.events.speech_synthesized import SpeechSynthesized
from voice.domain.events.speech_transcribed import SpeechTranscribed
from voice.domain.events.voice_session_ended import VoiceSessionEnded
from voice.domain.events.voice_session_paused import VoiceSessionPaused
from voice.domain.events.voice_session_started import VoiceSessionStarted
from voice.domain.events.voice_turn_started import VoiceTurnStarted
from voice.domain.value_objects.speech_confidence import SpeechConfidence
from voice.domain.value_objects.voice_provider import VoiceProvider
from voice.domain.value_objects.voice_session_metrics import (
    VoiceSessionMetrics,
)
from voice.domain.value_objects.voice_session_status import (
    VoiceSessionStatus,
)


class VoiceSession(AggregateRoot[EntityId]):
    """VoiceSession Aggregate Root.

    Enforces invariants:
    - State machine transitions (IDLE -> CONNECTING -> ACTIVE <-> PAUSED -> ENDED / FAILED).
    - Audio streams and turns belong strictly to active/paused voice sessions.
    - Interacts with external systems (Conversation, STT, TTS, Telephony) strictly via ports.
    """

    def __init__(
        self,
        id: EntityId,
        workspace_id: WorkspaceId,
        agent_id: AgentId,
        conversation_id: ConversationId,
        status: VoiceSessionStatus | None = None,
        stt_provider: VoiceProvider | None = None,
        tts_provider: VoiceProvider | None = None,
        telephony_provider: VoiceProvider | None = None,
        participants: Sequence[VoiceParticipant] = (),
        streams: Sequence[AudioStream] = (),
        turns: Sequence[VoiceTurn] = (),
        metrics: VoiceSessionMetrics | None = None,
        error_message: str = "",
        created_at: Timestamp | None = None,
        version: int = 1,
    ) -> None:
        super().__init__(id=id, created_at=created_at, version=version)

        self._workspace_id = workspace_id
        self._agent_id = agent_id
        self._conversation_id = conversation_id
        self._status = status or VoiceSessionStatus.idle()
        self._stt_provider = stt_provider or VoiceProvider("fake_stt")
        self._tts_provider = tts_provider or VoiceProvider("fake_tts")
        self._telephony_provider = telephony_provider or VoiceProvider("fake_telephony")
        self._participants: list[VoiceParticipant] = list(participants)
        self._streams: list[AudioStream] = list(streams)
        self._turns: list[VoiceTurn] = list(turns)
        self._metrics = metrics or VoiceSessionMetrics()
        self._error_message = error_message.strip()

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def workspace_id(self) -> WorkspaceId:
        return self._workspace_id

    @property
    def agent_id(self) -> AgentId:
        return self._agent_id

    @property
    def conversation_id(self) -> ConversationId:
        return self._conversation_id

    @property
    def status(self) -> VoiceSessionStatus:
        return self._status

    @property
    def stt_provider(self) -> VoiceProvider:
        return self._stt_provider

    @property
    def tts_provider(self) -> VoiceProvider:
        return self._tts_provider

    @property
    def telephony_provider(self) -> VoiceProvider:
        return self._telephony_provider

    @property
    def participants(self) -> tuple[VoiceParticipant, ...]:
        return tuple(self._participants)

    @property
    def streams(self) -> tuple[AudioStream, ...]:
        return tuple(self._streams)

    @property
    def turns(self) -> tuple[VoiceTurn, ...]:
        return tuple(self._turns)

    @property
    def metrics(self) -> VoiceSessionMetrics:
        return self._metrics

    @property
    def error_message(self) -> str:
        return self._error_message

    # ── Mutators ──────────────────────────────────────────────────────────

    def start(self) -> Result[None]:
        """Start the VoiceSession."""
        if not (self._status.is_idle or self._status.value.name == "CONNECTING"):
            return Result.fail(Error("INVALID_STATE", f"Cannot start session in status {self._status.value.value}"))

        self._status = VoiceSessionStatus.active()
        self._raise_event(
            VoiceSessionStarted(
                session_id=str(self.id.value),
                workspace_id=str(self._workspace_id.value),
                agent_id=str(self._agent_id.value),
                conversation_id=str(self._conversation_id.value),
            )
        )
        return Result.ok(None)

    def pause(self) -> Result[None]:
        """Pause active VoiceSession."""
        if not self._status.is_active:
            return Result.fail(Error("INVALID_STATE", "Only active sessions can be paused"))

        self._status = VoiceSessionStatus.paused()
        self._raise_event(VoiceSessionPaused(session_id=str(self.id.value)))
        return Result.ok(None)

    def resume(self) -> Result[None]:
        """Resume paused VoiceSession."""
        if not self._status.is_paused:
            return Result.fail(Error("INVALID_STATE", "Only paused sessions can be resumed"))

        self._status = VoiceSessionStatus.active()
        return Result.ok(None)

    def end(self, reason: str = "User hangup") -> Result[None]:
        """End VoiceSession."""
        if self._status.is_ended or self._status.is_failed:
            return Result.fail(Error("INVALID_STATE", "Session is already terminal"))

        self._status = VoiceSessionStatus.ended()
        for s in self._streams:
            s.close()

        self._metrics = VoiceSessionMetrics(
            total_turns=len(self._turns),
            audio_duration_seconds=self._metrics.audio_duration_seconds,
            average_latency_ms=self._metrics.average_latency_ms,
        )

        self._raise_event(
            VoiceSessionEnded(
                session_id=str(self.id.value),
                reason=reason,
                total_turns=len(self._turns),
            )
        )
        return Result.ok(None)

    def fail(self, error_message: str) -> Result[None]:
        """Fail VoiceSession."""
        if self._status.is_ended or self._status.is_failed:
            return Result.fail(Error("INVALID_STATE", "Session is already terminal"))

        self._status = VoiceSessionStatus.failed()
        self._error_message = error_message.strip()
        for s in self._streams:
            s.close()
        return Result.ok(None)

    def add_participant(self, participant: VoiceParticipant) -> Result[None]:
        """Add a participant to the session."""
        if self._status.is_ended or self._status.is_failed:
            return Result.fail(Error("INVALID_STATE", "Cannot add participants to terminal session"))

        self._participants.append(participant)
        return Result.ok(None)

    def add_stream(self, stream: AudioStream) -> Result[None]:
        """Add an AudioStream to the session."""
        if self._status.is_ended or self._status.is_failed:
            return Result.fail(Error("INVALID_STATE", "Cannot add streams to terminal session"))

        self._streams.append(stream)
        return Result.ok(None)

    def start_turn(self, speaker_role: str) -> Result[VoiceTurn]:
        """Start a new voice turn in the session."""
        if not self._status.is_active:
            return Result.fail(Error("INVALID_STATE", "Session must be active to start turns"))

        turn_num = len(self._turns) + 1
        turn = VoiceTurn(
            id=EntityId(),
            speaker_role=speaker_role,
            turn_number=turn_num,
        )
        self._turns.append(turn)

        self._raise_event(
            VoiceTurnStarted(
                session_id=str(self.id.value),
                turn_id=str(turn.id.value),
                speaker_role=speaker_role,
            )
        )
        return Result.ok(turn)

    def record_speech_transcribed(
        self, turn_id: str, transcript: str, confidence: float
    ) -> Result[None]:
        """Record STT output for a turn."""
        turn = self._find_turn(turn_id)
        if turn is None:
            return Result.fail(Error("NOT_FOUND", f"Turn '{turn_id}' not found"))

        turn.set_transcript(transcript, SpeechConfidence(confidence))
        self._raise_event(
            SpeechTranscribed(
                session_id=str(self.id.value),
                turn_id=turn_id,
                transcript=transcript,
                confidence=confidence,
            )
        )
        return Result.ok(None)

    def record_agent_response(self, turn_id: str, response_text: str) -> Result[None]:
        """Record generated agent response text for a turn."""
        turn = self._find_turn(turn_id)
        if turn is None:
            return Result.fail(Error("NOT_FOUND", f"Turn '{turn_id}' not found"))

        turn.set_agent_response(response_text)
        self._raise_event(
            AgentResponseGenerated(
                session_id=str(self.id.value),
                turn_id=turn_id,
                response_text=response_text,
            )
        )
        return Result.ok(None)

    def record_speech_synthesized(self, turn_id: str, audio_bytes_len: int) -> Result[None]:
        """Record TTS audio synthesis for a turn."""
        turn = self._find_turn(turn_id)
        if turn is None:
            return Result.fail(Error("NOT_FOUND", f"Turn '{turn_id}' not found"))

        turn.mark_synthesized()
        turn.complete()
        self._raise_event(
            SpeechSynthesized(
                session_id=str(self.id.value),
                turn_id=turn_id,
                audio_bytes_length=audio_bytes_len,
            )
        )
        return Result.ok(None)

    def _find_turn(self, turn_id: str) -> VoiceTurn | None:
        for t in self._turns:
            if str(t.id.value) == turn_id:
                return t
        return None
