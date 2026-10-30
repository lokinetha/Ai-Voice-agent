"""
Data Transfer Objects for Voice Agent Pipeline Application Orchestration.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VoiceTurnInput:
    """Input payload for VoiceAgentPipeline execution turn."""

    workspace_id: str
    agent_id: str
    conversation_id: str
    audio_bytes: bytes = b""
    audio_file_path: str = ""
    output_audio_path: str = ""
    correlation_id: str | None = None
    voice_id: str = "default"
    language: str | None = None


@dataclass(frozen=True)
class VoiceTurnResult:
    """Provider-independent result returned by VoiceAgentPipeline."""

    transcript: str
    agent_response_text: str
    audio_bytes: bytes
    output_audio_path: str
    workspace_id: str
    agent_id: str
    conversation_id: str
    correlation_id: str
    detected_language: str = "en-IN"
    stt_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0
    tts_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
