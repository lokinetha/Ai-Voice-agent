"""
Voice Infrastructure Adapters package init.
"""

from voice.infrastructure.adapters.conversation_adapter import ConversationAdapter
from voice.infrastructure.adapters.fake_audio_stream_adapter import (
    FakeAudioStreamAdapter,
)
from voice.infrastructure.adapters.fake_llm_runtime_adapter import (
    FakeLLMRuntimeAdapter,
)
from voice.infrastructure.adapters.fake_stt_adapter import FakeSTTAdapter
from voice.infrastructure.adapters.fake_telephony_adapter import (
    FakeTelephonyAdapter,
)
from voice.infrastructure.adapters.fake_tts_adapter import FakeTTSAdapter
from voice.infrastructure.adapters.faster_whisper_stt_adapter import (
    FasterWhisperSTTAdapter,
)
from voice.infrastructure.adapters.gemini_llm_adapter import (
    GeminiLLMAdapter,
    LLMProviderError,
    LLMTimeoutError,
)
from voice.infrastructure.adapters.in_memory_conversation_adapter import (
    InMemoryConversationAdapter,
    InMemoryConversationStore,
)
from voice.infrastructure.adapters.llm_dto import LLMResponseDTO
from voice.infrastructure.adapters.local_tts_adapter import (
    LocalTTSAdapter,
    LocalTTSSynthesisResult,
    TTSProviderError,
)
from voice.infrastructure.adapters.local_whisper_stt_adapter import (
    LocalWhisperSTTAdapter,
    STTProviderError,
    WhisperTranscriptionResult,
)
from voice.infrastructure.adapters.piper_tts_adapter import PiperTTSAdapter

__all__ = [
    "ConversationAdapter",
    "FakeAudioStreamAdapter",
    "FakeLLMRuntimeAdapter",
    "FakeSTTAdapter",
    "FakeTelephonyAdapter",
    "FakeTTSAdapter",
    "FasterWhisperSTTAdapter",
    "GeminiLLMAdapter",
    "InMemoryConversationAdapter",
    "InMemoryConversationStore",
    "LLMProviderError",
    "LLMResponseDTO",
    "LLMTimeoutError",
    "LocalTTSAdapter",
    "LocalTTSSynthesisResult",
    "LocalWhisperSTTAdapter",
    "PiperTTSAdapter",
    "STTProviderError",
    "TTSProviderError",
    "WhisperTranscriptionResult",
]
