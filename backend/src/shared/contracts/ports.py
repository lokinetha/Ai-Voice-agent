"""
Hexagonal Architecture Port Interfaces.

Primary ports defining infrastructure requirements for speech processing, LLM inference,
vector stores, object storage, caching, events, and telephony.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from shared.kernel.domain_event import DomainEvent

# ── Port Return Type Contracts ────────────────────────────────────────────────


@dataclass(frozen=True)
class TranscriptResult:
    """Result payload from full audio transcription."""

    text: str
    confidence: float
    duration_seconds: float
    word_count: int


@dataclass(frozen=True)
class PartialTranscript:
    """Streaming transcript chunk."""

    text: str
    is_final: bool
    confidence: float
    start_time: float
    end_time: float


@dataclass(frozen=True)
class ToolCallResult:
    """Structured response from LLM tool/function invocation."""

    tool_name: str
    arguments: dict[str, Any]
    content: str | None = None


# ── Primary Port Interfaces ───────────────────────────────────────────────────


class STTPort(ABC):
    """Speech-to-Text Port Interface."""

    @abstractmethod
    async def transcribe(self, audio: bytes, language: str) -> TranscriptResult:
        """Synchronously transcribe full audio payload."""
        ...

    @abstractmethod
    async def stream_transcribe(
        self, audio_stream: AsyncGenerator[bytes], language: str
    ) -> AsyncGenerator[PartialTranscript]:
        """Stream transcription chunks from audio byte generator."""
        ...


class TTSPort(ABC):
    """Text-to-Speech Port Interface."""

    @abstractmethod
    async def synthesize(self, text: str, voice_id: str) -> bytes:
        """Synthesize text into full audio payload."""
        ...

    @abstractmethod
    async def stream_synthesize(
        self, text: str, voice_id: str
    ) -> AsyncGenerator[bytes]:
        """Stream synthesized audio chunks from text input."""
        ...


class LLMPort(ABC):
    """Large Language Model Inference Port Interface."""

    @abstractmethod
    async def generate(self, messages: list[dict[str, Any]], config: dict[str, Any]) -> str:
        """Generate single text response from chat messages."""
        ...

    @abstractmethod
    async def stream_generate(
        self, messages: list[dict[str, Any]], config: dict[str, Any]
    ) -> AsyncGenerator[str]:
        """Stream token chunks from chat messages."""
        ...

    @abstractmethod
    async def function_call(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        config: dict[str, Any],
    ) -> ToolCallResult:
        """Execute LLM completion requesting structured tool call."""
        ...


class EmbeddingPort(ABC):
    """Vector Embedding Generation Port Interface."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for text list."""
        ...

    @abstractmethod
    def dimension(self) -> int:
        """Get output embedding vector dimensionality."""
        ...


class VectorStorePort(ABC):
    """Vector Database Storage and Search Port Interface."""

    @abstractmethod
    async def upsert(self, collection: str, vectors: list[dict[str, Any]]) -> None:
        """Upsert records with vectors and payloads into target collection."""
        ...

    @abstractmethod
    async def search(
        self,
        collection: str,
        vector: list[float],
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Perform nearest-neighbor vector similarity search."""
        ...

    @abstractmethod
    async def delete(self, collection: str, ids: list[str]) -> None:
        """Delete records by ID from target collection."""
        ...


class ObjectStoragePort(ABC):
    """Blob/Object Storage Port Interface."""

    @abstractmethod
    async def upload(self, key: str, data: bytes, content_type: str) -> str:
        """Upload raw data to target key path."""
        ...

    @abstractmethod
    async def download(self, key: str) -> bytes:
        """Download raw data bytes from target key path."""
        ...

    @abstractmethod
    async def get_presigned_url(self, key: str, ttl: int) -> str:
        """Generate temporary presigned access URL for target key."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete object at key path."""
        ...


class EventBusPort(ABC):
    """Domain Event Bus Port Interface."""

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event to event broker."""
        ...

    @abstractmethod
    async def subscribe(
        self, event_type: str, handler: Callable[[DomainEvent], Awaitable[None]]
    ) -> None:
        """Register handler for specific event type string."""
        ...


class CachePort(ABC):
    """Distributed Key-Value Caching Port Interface."""

    @abstractmethod
    async def get(self, key: str) -> str | None:
        """Get string value by cache key."""
        ...

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        """Set string value for cache key with optional TTL in seconds."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete entry by cache key."""
        ...


class TelephonyPort(ABC):
    """Telephony Control Port Interface."""

    @abstractmethod
    async def create_call(self, to: str, from_: str, webhook_url: str) -> str:
        """Initiate outbound phone call and return call SID."""
        ...

    @abstractmethod
    async def end_call(self, call_sid: str) -> None:
        """Terminate active call by SID."""
        ...

    @abstractmethod
    async def transfer_call(self, call_sid: str, to: str) -> None:
        """Transfer active call SID to new recipient phone number."""
        ...
