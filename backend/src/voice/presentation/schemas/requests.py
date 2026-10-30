"""
Pydantic Request Schemas for Voice Presentation Layer.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class StartVoiceSessionRequest(BaseModel):
    """HTTP Request schema for starting a voice session."""

    workspace_id: str = Field(..., description="Workspace ID")
    agent_id: str = Field(..., description="Agent ID")
    conversation_id: str = Field(..., description="Conversation ID")
    stt_provider_name: str = Field(default="fake_stt", description="STT Provider identifier")
    tts_provider_name: str = Field(default="fake_tts", description="TTS Provider identifier")
    telephony_provider_name: str = Field(default="fake_telephony", description="Telephony Provider identifier")
    sample_rate: int = Field(default=16000, description="Audio sample rate in Hz")
    channels: int = Field(default=1, description="Channel count (1=mono, 2=stereo)")
    encoding: str = Field(default="pcm_s16le", description="Audio encoding codec")


class ProcessTranscriptRequest(BaseModel):
    """HTTP Request schema for processing user transcript."""

    transcript: str = Field(..., description="Transcribed speech text")
    confidence: float = Field(default=1.0, description="Transcription confidence score")


class GenerateAgentResponseRequest(BaseModel):
    """HTTP Request schema for generating AI Agent response."""

    user_prompt: str = Field(default="", description="Optional user prompt text override")


class SynthesizeResponseRequest(BaseModel):
    """HTTP Request schema for TTS audio synthesis."""

    voice_id: str = Field(default="default_agent_voice", description="TTS Voice ID model")


class EndVoiceSessionRequest(BaseModel):
    """HTTP Request schema for ending a voice session."""

    reason: str = Field(default="User hangup", description="Reason for session end")
