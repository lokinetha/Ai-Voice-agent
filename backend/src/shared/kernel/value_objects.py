"""
Shared Kernel Standard Domain Value Objects.

Common strongly-typed identifiers and primitive value objects used across Bounded Contexts.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from shared.kernel.value_object import ValueObject

# ── Typed Identifier Base ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class EntityId(ValueObject):
    """Base class for all strongly-typed domain entity identifiers.

    Encapsulates UUID4 string generation and string validation.
    """

    value: str = ""

    def __post_init__(self) -> None:
        if not self.value:
            object.__setattr__(self, "value", str(uuid.uuid4()))
        super().__post_init__()

    def _validate(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("EntityId value must be a non-empty string")

    def __str__(self) -> str:
        return self.value


# ── Specialized Domain Entity Identifiers ─────────────────────────────────────


@dataclass(frozen=True)
class TenantId(EntityId):
    """Identifier for multi-tenant isolation boundary."""


@dataclass(frozen=True)
class UserId(EntityId):
    """Identifier for User aggregate root."""


@dataclass(frozen=True)
class OrganizationId(EntityId):
    """Identifier for Organization aggregate root."""


@dataclass(frozen=True)
class WorkspaceId(EntityId):
    """Identifier for Workspace entity."""


@dataclass(frozen=True)
class AgentId(EntityId):
    """Identifier for Agent aggregate root."""


@dataclass(frozen=True)
class SessionId(EntityId):
    """Identifier for Voice Session entity."""


@dataclass(frozen=True)
class PlaybookId(EntityId):
    """Identifier for Agent Playbook aggregate root."""


@dataclass(frozen=True)
class PromptId(EntityId):
    """Identifier for Prompt entity."""


@dataclass(frozen=True)
class DocumentId(EntityId):
    """Identifier for Document entity."""


@dataclass(frozen=True)
class MessageId(EntityId):
    """Identifier for Message entity."""


@dataclass(frozen=True)
class ConversationId(EntityId):
    """Identifier for Conversation entity."""


@dataclass(frozen=True)
class CustomerId(EntityId):
    """Identifier for Customer entity."""


@dataclass(frozen=True)
class EvaluationId(EntityId):
    """Identifier for Evaluation entity."""


@dataclass(frozen=True)
class KnowledgeBaseId(EntityId):
    """Identifier for Knowledge Base entity."""


@dataclass(frozen=True)
class PlaybookVersion(EntityId):
    """Identifier for Playbook Version entity."""


@dataclass(frozen=True)
class PromptVersion(EntityId):
    """Identifier for Prompt Version entity."""


@dataclass(frozen=True)
class RecordingId(EntityId):
    """Identifier for Recording entity."""


# ── Generic Domain Value Objects ──────────────────────────────────────────────


@dataclass(frozen=True)
class Email(ValueObject):
    """Valid email address value object."""

    value: str

    def _validate(self) -> None:
        pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not self.value or not re.match(pattern, self.value):
            raise ValueError(f"Invalid email address: {self.value}")


@dataclass(frozen=True)
class PhoneNumber(ValueObject):
    """E.164 compliant or international phone number value object."""

    value: str
    country_code: str = "+1"

    def _validate(self) -> None:
        cleaned = re.sub(r"[^\d+]", "", self.value)
        if len(cleaned) < 7:
            raise ValueError(f"Invalid phone number format: {self.value}")


@dataclass(frozen=True)
class Timestamp(ValueObject):
    """UTC timestamp value object."""

    value: datetime

    def _validate(self) -> None:
        if not isinstance(self.value, datetime):
            raise ValueError("Timestamp value must be a datetime instance")

    @classmethod
    def now(cls) -> Timestamp:
        """Create timestamp initialized to current UTC time."""
        return cls(value=datetime.now(UTC))

    def __str__(self) -> str:
        return self.value.isoformat()


@dataclass(frozen=True)
class Version(ValueObject):
    """Monotonic aggregate version counter."""

    value: int = 1

    def _validate(self) -> None:
        if self.value < 0:
            raise ValueError("Version number cannot be negative")

    def next(self) -> Version:
        """Return next monotonic version."""
        return Version(value=self.value + 1)


@dataclass(frozen=True)
class Language(ValueObject):
    """ISO language code value object (e.g., 'en-US', 'es')."""

    code: str

    def _validate(self) -> None:
        pattern = r"^[a-z]{2}(-[A-Z]{2})?$"
        if not self.code or not re.match(pattern, self.code):
            raise ValueError(f"Invalid BCP 47 language code: {self.code}")


@dataclass(frozen=True)
class Region(ValueObject):
    """Cloud region code (e.g., 'us-east-1')."""

    value: str

    def _validate(self) -> None:
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Region value cannot be empty")


@dataclass(frozen=True)
class Score(ValueObject):
    """Normalized score between 0.0 and 1.0."""

    value: float

    def _validate(self) -> None:
        if not isinstance(self.value, (int, float)) or not (0.0 <= float(self.value) <= 1.0):
            raise ValueError(f"Score must be a float between 0.0 and 1.0, got: {self.value}")

    def to_percentage(self) -> float:
        """Return score formatted as a rounded percentage."""
        return round(self.value * 100, 2)


@dataclass(frozen=True)
class EmbeddingVector(ValueObject):
    """Text embedding vector with dimensionality check."""

    values: tuple[float, ...]
    dimension: int

    def _validate(self) -> None:
        if len(self.values) != self.dimension:
            raise ValueError(
                f"Vector dimension mismatch: expected {self.dimension}, got {len(self.values)}"
            )


@dataclass(frozen=True)
class TranscriptSegment(ValueObject):
    """Segment of transcribed conversation audio."""

    speaker: str
    start_time: float
    end_time: float
    text: str
    confidence: float

    def _validate(self) -> None:
        if self.start_time < 0.0 or self.end_time < self.start_time:
            raise ValueError("Invalid segment timing interval")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")


@dataclass(frozen=True)
class Transcript(ValueObject):
    """Complete audio transcript representation."""

    full_text: str
    segments: tuple[TranscriptSegment, ...]
    confidence: float
    duration_seconds: float

    def _validate(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Transcript confidence must be between 0.0 and 1.0")


@dataclass(frozen=True)
class MoneyAmount(ValueObject):
    """Monetary amount in smallest currency unit (e.g. cents) with ISO 4217 currency."""

    amount: int
    currency: str = "USD"

    def _validate(self) -> None:
        if self.amount < 0:
            raise ValueError("Monetary amount cannot be negative")
        if not self.currency or len(self.currency) != 3:
            raise ValueError(f"Currency must be 3-letter ISO code, got: {self.currency}")

    @property
    def amount_cents(self) -> int:
        """Alias for amount in cents."""
        return self.amount

    def __add__(self, other: MoneyAmount) -> MoneyAmount:
        """Add two MoneyAmount instances with matching currency."""
        if not isinstance(other, MoneyAmount):
            return NotImplemented
        if self.currency != other.currency:
            raise ValueError(f"Cannot add money with different currencies: {self.currency} vs {other.currency}")
        return MoneyAmount(amount=self.amount + other.amount, currency=self.currency)
