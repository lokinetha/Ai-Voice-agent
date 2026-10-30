# 00. Shared Kernel & Base Abstractions

> **Enterprise Architecture Review — New Foundation Document**
>
> This document defines the Shared Kernel: base classes, interfaces, and primitives used across
> all bounded contexts. No bounded context may define its own base types.

---

## Dependency Rule (Inviolable)

```
Presentation → Application → Domain ← Infrastructure
                                ↑
                          Shared Kernel
```

- **Domain depends on NOTHING** except Shared Kernel.
- **Application depends on** Domain.
- **Infrastructure depends on** Domain (implements its interfaces).
- **Presentation depends on** Application.
- **Frameworks** live in Infrastructure and Presentation only.

---

## 1. Base Entity

```python
# shared/kernel/entity.py
from __future__ import annotations
from shared.kernel.value_objects import EntityId, Timestamp

class Entity:
    """Base class for all domain entities. Identity-based equality."""

    def __init__(self, id: EntityId, created_at: Timestamp | None = None):
        self._id = id
        self._created_at = created_at or Timestamp.now()

    @property
    def id(self) -> EntityId:
        return self._id

    @property
    def created_at(self) -> Timestamp:
        return self._created_at

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)
```

## 2. Aggregate Root

```python
# shared/kernel/aggregate_root.py
from shared.kernel.entity import Entity
from shared.kernel.domain_event import DomainEvent

class AggregateRoot(Entity):
    """
    Base class for aggregate roots.
    Owns domain events. Only aggregate roots may be persisted directly.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._domain_events: list[DomainEvent] = []
        self._version: int = 0           # Optimistic concurrency

    @property
    def domain_events(self) -> list[DomainEvent]:
        return list(self._domain_events)

    @property
    def version(self) -> int:
        return self._version

    def _raise_event(self, event: DomainEvent) -> None:
        """Register a domain event. Dispatched after persistence."""
        self._domain_events.append(event)

    def clear_events(self) -> list[DomainEvent]:
        """Flush events after unit-of-work commit."""
        events = list(self._domain_events)
        self._domain_events.clear()
        return events
```

## 3. Value Object

```python
# shared/kernel/value_object.py
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ValueObject:
    """
    Base class for value objects. Value-based equality, immutable.
    Subclasses must be frozen dataclasses.
    """

    def __post_init__(self):
        self._validate()

    def _validate(self) -> None:
        """Override in subclasses to enforce invariants."""
        pass
```

## 4. Typed Identifiers (Eliminate Primitive Obsession)

```python
# shared/kernel/value_objects.py
from __future__ import annotations
import uuid
import re
from datetime import datetime, timezone
from dataclasses import dataclass, field
from shared.kernel.value_object import ValueObject

# ── Identity ────────────────────────────────────────────

@dataclass(frozen=True)
class EntityId(ValueObject):
    value: str = field(default_factory=lambda: str(uuid.uuid4()))

    def _validate(self) -> None:
        if not self.value:
            raise ValueError("EntityId cannot be empty")

@dataclass(frozen=True)
class TenantId(EntityId): pass

@dataclass(frozen=True)
class AgentId(EntityId): pass

@dataclass(frozen=True)
class ConversationId(EntityId): pass

@dataclass(frozen=True)
class PlaybookId(EntityId): pass

@dataclass(frozen=True)
class PromptId(EntityId): pass

@dataclass(frozen=True)
class KnowledgeBaseId(EntityId): pass

@dataclass(frozen=True)
class RecordingId(EntityId): pass

@dataclass(frozen=True)
class UserId(EntityId): pass

@dataclass(frozen=True)
class CustomerId(EntityId): pass

@dataclass(frozen=True)
class SessionId(EntityId): pass

@dataclass(frozen=True)
class EvaluationId(EntityId): pass

@dataclass(frozen=True)
class WorkspaceId(EntityId): pass

@dataclass(frozen=True)
class OrganizationId(EntityId): pass

@dataclass(frozen=True)
class DocumentId(EntityId): pass

@dataclass(frozen=True)
class MessageId(EntityId): pass

# ── Domain-Specific Value Objects ───────────────────────

@dataclass(frozen=True)
class Email(ValueObject):
    value: str

    def _validate(self) -> None:
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', self.value):
            raise ValueError(f"Invalid email: {self.value}")

@dataclass(frozen=True)
class PhoneNumber(ValueObject):
    value: str
    country_code: str = "+1"

    def _validate(self) -> None:
        cleaned = re.sub(r'[^\d+]', '', self.value)
        if len(cleaned) < 7:
            raise ValueError(f"Invalid phone: {self.value}")

@dataclass(frozen=True)
class Timestamp(ValueObject):
    value: datetime

    @classmethod
    def now(cls) -> Timestamp:
        return cls(value=datetime.now(timezone.utc))

@dataclass(frozen=True)
class Version(ValueObject):
    """Monotonically increasing version number."""
    value: int

    def _validate(self) -> None:
        if self.value < 1:
            raise ValueError("Version must be >= 1")

    def next(self) -> Version:
        return Version(value=self.value + 1)

@dataclass(frozen=True)
class PromptVersion(Version): pass

@dataclass(frozen=True)
class PlaybookVersion(Version): pass

@dataclass(frozen=True)
class Language(ValueObject):
    code: str  # e.g., "en-US"

    def _validate(self) -> None:
        if not re.match(r'^[a-z]{2}(-[A-Z]{2})?$', self.code):
            raise ValueError(f"Invalid language code: {self.code}")

@dataclass(frozen=True)
class Region(ValueObject):
    value: str  # e.g., "us-east-1"

@dataclass(frozen=True)
class Score(ValueObject):
    """Score between 0.0 and 1.0."""
    value: float

    def _validate(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"Score must be 0.0-1.0, got {self.value}")

    def to_percentage(self) -> float:
        return round(self.value * 100, 2)

@dataclass(frozen=True)
class EmbeddingVector(ValueObject):
    values: tuple[float, ...]
    dimension: int

    def _validate(self) -> None:
        if len(self.values) != self.dimension:
            raise ValueError(
                f"Expected {self.dimension} dims, got {len(self.values)}"
            )

@dataclass(frozen=True)
class Transcript(ValueObject):
    full_text: str
    segments: tuple  # tuple of TranscriptSegment
    confidence: float
    duration_seconds: float

@dataclass(frozen=True)
class MoneyAmount(ValueObject):
    amount: int        # In smallest unit (cents)
    currency: str      # ISO 4217

    def _validate(self) -> None:
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
```

## 5. Domain Event

```python
# shared/kernel/domain_event.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid

@dataclass(frozen=True)
class DomainEvent:
    """
    Base domain event. Immutable, serializable, routable.
    All events carry tenant context for multi-tenant isolation.
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tenant_id: str = ""
    correlation_id: str = ""       # Trace across event chains
    causation_id: str = ""         # The event that caused this event

    @property
    def event_type(self) -> str:
        return self.__class__.__qualname__
```

## 6. Repository Interface

```python
# shared/kernel/repository.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TypeVar, Generic
from shared.kernel.aggregate_root import AggregateRoot
from shared.kernel.value_objects import EntityId
from shared.kernel.specification import Specification

T = TypeVar("T", bound=AggregateRoot)

class Repository(ABC, Generic[T]):
    """
    Base repository interface. Lives in Domain layer.
    Implementation in Infrastructure layer.
    Operates only on aggregate roots.
    """

    @abstractmethod
    async def get_by_id(self, id: EntityId) -> T | None: ...

    @abstractmethod
    async def save(self, aggregate: T) -> None: ...

    @abstractmethod
    async def delete(self, aggregate: T) -> None: ...

    @abstractmethod
    async def find(self, spec: Specification[T]) -> list[T]: ...

    @abstractmethod
    async def count(self, spec: Specification[T]) -> int: ...
```

## 7. Unit of Work

```python
# shared/kernel/unit_of_work.py
from __future__ import annotations
from abc import ABC, abstractmethod
from shared.kernel.domain_event import DomainEvent

class UnitOfWork(ABC):
    """
    Transaction boundary. Collects events from aggregates,
    commits to database, then dispatches events.
    """

    @abstractmethod
    async def __aenter__(self) -> UnitOfWork: ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...

    @abstractmethod
    def collect_events(self) -> list[DomainEvent]: ...
```

## 8. Specification Pattern

```python
# shared/kernel/specification.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar("T")

class Specification(ABC, Generic[T]):
    """
    Encapsulates query/filter logic as composable, testable objects.
    Replaces ad-hoc query filters scattered across services.
    """

    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool: ...

    def and_(self, other: Specification[T]) -> Specification[T]:
        return _AndSpecification(self, other)

    def or_(self, other: Specification[T]) -> Specification[T]:
        return _OrSpecification(self, other)

    def not_(self) -> Specification[T]:
        return _NotSpecification(self)


class _AndSpecification(Specification[T]):
    def __init__(self, left: Specification[T], right: Specification[T]):
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        return (self._left.is_satisfied_by(candidate)
                and self._right.is_satisfied_by(candidate))


class _OrSpecification(Specification[T]):
    def __init__(self, left: Specification[T], right: Specification[T]):
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        return (self._left.is_satisfied_by(candidate)
                or self._right.is_satisfied_by(candidate))


class _NotSpecification(Specification[T]):
    def __init__(self, spec: Specification[T]):
        self._spec = spec

    def is_satisfied_by(self, candidate: T) -> bool:
        return not self._spec.is_satisfied_by(candidate)
```

## 9. Result Monad

```python
# shared/kernel/result.py
from __future__ import annotations
from dataclasses import dataclass
from typing import TypeVar, Generic

T = TypeVar("T")

@dataclass(frozen=True)
class Error:
    code: str
    message: str
    details: dict | None = None

@dataclass
class Result(Generic[T]):
    """
    Railway-oriented programming. All use cases return Result[T]
    instead of raising exceptions for expected failures.
    """
    _value: T | None
    _error: Error | None

    @classmethod
    def ok(cls, value: T) -> Result[T]:
        return cls(_value=value, _error=None)

    @classmethod
    def fail(cls, error: Error) -> Result[T]:
        return cls(_value=None, _error=error)

    @property
    def is_success(self) -> bool:
        return self._error is None

    @property
    def is_failure(self) -> bool:
        return self._error is not None

    @property
    def value(self) -> T:
        if self._error is not None:
            raise ValueError(f"Cannot access value of failed result: {self._error}")
        return self._value  # type: ignore

    @property
    def error(self) -> Error:
        if self._error is None:
            raise ValueError("Cannot access error of successful result")
        return self._error
```

## 10. CQRS Primitives

```python
# shared/kernel/cqrs.py
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeVar, Generic
from shared.kernel.result import Result

# ── Messages ────────────────────────────────────────────

@dataclass(frozen=True)
class Command:
    """Base class for all commands. Commands mutate state."""
    pass

@dataclass(frozen=True)
class Query:
    """Base class for all queries. Queries are side-effect-free."""
    pass

# ── Handlers ────────────────────────────────────────────

TResult = TypeVar("TResult")
TCommand = TypeVar("TCommand", bound=Command)
TQuery = TypeVar("TQuery", bound=Query)

class CommandHandler(ABC, Generic[TCommand, TResult]):
    @abstractmethod
    async def handle(self, command: TCommand) -> Result[TResult]: ...

class QueryHandler(ABC, Generic[TQuery, TResult]):
    @abstractmethod
    async def handle(self, query: TQuery) -> Result[TResult]: ...
```

## 11. Domain Service Interface

```python
# shared/kernel/domain_service.py
from abc import ABC

class DomainService(ABC):
    """
    Marker for domain services.
    Domain services encapsulate logic that doesn't belong to a single entity
    but requires coordination across multiple entities/value objects.
    Lives in Domain layer.
    """
    pass
```

## 12. Port Interfaces (Hexagonal)

```python
# shared/contracts/ports.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import AsyncGenerator

class STTPort(ABC):
    """Primary port for Speech-to-Text. Implemented by adapters."""
    @abstractmethod
    async def transcribe(self, audio: bytes, language: str) -> "TranscriptResult": ...

    @abstractmethod
    async def stream_transcribe(
        self, audio_stream: AsyncGenerator[bytes, None], language: str
    ) -> AsyncGenerator["PartialTranscript", None]: ...

class TTSPort(ABC):
    """Primary port for Text-to-Speech."""
    @abstractmethod
    async def synthesize(self, text: str, voice_id: str) -> bytes: ...

    @abstractmethod
    async def stream_synthesize(
        self, text: str, voice_id: str
    ) -> AsyncGenerator[bytes, None]: ...

class LLMPort(ABC):
    """Primary port for Large Language Model inference."""
    @abstractmethod
    async def generate(self, messages: list[dict], config: dict) -> str: ...

    @abstractmethod
    async def stream_generate(
        self, messages: list[dict], config: dict
    ) -> AsyncGenerator[str, None]: ...

    @abstractmethod
    async def function_call(
        self, messages: list[dict], tools: list[dict], config: dict
    ) -> "ToolCallResult": ...

class EmbeddingPort(ABC):
    """Primary port for text embedding generation."""
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]: ...

    @abstractmethod
    def dimension(self) -> int: ...

class VectorStorePort(ABC):
    """Primary port for vector storage and retrieval."""
    @abstractmethod
    async def upsert(self, collection: str, vectors: list[dict]) -> None: ...

    @abstractmethod
    async def search(
        self, collection: str, vector: list[float],
        top_k: int, filters: dict | None
    ) -> list[dict]: ...

    @abstractmethod
    async def delete(self, collection: str, ids: list[str]) -> None: ...

class ObjectStoragePort(ABC):
    """Primary port for blob/object storage."""
    @abstractmethod
    async def upload(self, key: str, data: bytes, content_type: str) -> str: ...

    @abstractmethod
    async def download(self, key: str) -> bytes: ...

    @abstractmethod
    async def get_presigned_url(self, key: str, ttl: int) -> str: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

class EventBusPort(ABC):
    """Primary port for publishing domain events."""
    @abstractmethod
    async def publish(self, event: "DomainEvent") -> None: ...

    @abstractmethod
    async def subscribe(self, event_type: str, handler: callable) -> None: ...

class CachePort(ABC):
    """Primary port for caching layer."""
    @abstractmethod
    async def get(self, key: str) -> str | None: ...

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int | None) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

class TelephonyPort(ABC):
    """Primary port for telephony integration."""
    @abstractmethod
    async def create_call(self, to: str, from_: str, webhook_url: str) -> str: ...

    @abstractmethod
    async def end_call(self, call_sid: str) -> None: ...

    @abstractmethod
    async def transfer_call(self, call_sid: str, to: str) -> None: ...
```

---

## Summary: Shared Kernel Contents

| Module | Contains | Purpose |
|--------|----------|---------|
| `kernel/entity.py` | `Entity` | Identity-based equality |
| `kernel/aggregate_root.py` | `AggregateRoot` | Event collection, optimistic concurrency |
| `kernel/value_object.py` | `ValueObject` | Immutable, self-validating |
| `kernel/value_objects.py` | 25+ typed IDs and VO's | Eliminate primitive obsession |
| `kernel/domain_event.py` | `DomainEvent` | Event base with correlation |
| `kernel/repository.py` | `Repository[T]` | Generic repo interface |
| `kernel/unit_of_work.py` | `UnitOfWork` | Transaction + event dispatch |
| `kernel/specification.py` | `Specification[T]` | Composable query predicates |
| `kernel/result.py` | `Result[T]`, `Error` | Railway-oriented error handling |
| `kernel/cqrs.py` | `Command`, `Query`, Handlers | CQRS message bus primitives |
| `kernel/domain_service.py` | `DomainService` | Domain service marker |
| `contracts/ports.py` | All Hexagonal ports | STT, TTS, LLM, Storage, etc. |
