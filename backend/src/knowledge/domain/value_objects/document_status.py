"""
DocumentStatus Value Object for Knowledge Bounded Context.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from shared.kernel.value_object import ValueObject


class DocumentStatusType(StrEnum):
    """Enumeration of Document processing states."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


@dataclass(frozen=True)
class DocumentStatus(ValueObject):
    """DocumentStatus Value Object."""

    value: DocumentStatusType

    def _validate(self) -> None:
        if not isinstance(self.value, DocumentStatusType):
            if isinstance(self.value, str):
                try:
                    object.__setattr__(self, "value", DocumentStatusType(self.value.upper()))
                except ValueError as err:
                    raise ValueError(f"Invalid DocumentStatus string: {self.value}") from err
            else:
                raise ValueError(f"DocumentStatus value must be DocumentStatusType enum, got: {type(self.value)}")

    @classmethod
    def pending(cls) -> DocumentStatus:
        return cls(value=DocumentStatusType.PENDING)

    @classmethod
    def processing(cls) -> DocumentStatus:
        return cls(value=DocumentStatusType.PROCESSING)

    @classmethod
    def indexed(cls) -> DocumentStatus:
        return cls(value=DocumentStatusType.INDEXED)

    @classmethod
    def failed(cls) -> DocumentStatus:
        return cls(value=DocumentStatusType.FAILED)

    @classmethod
    def archived(cls) -> DocumentStatus:
        return cls(value=DocumentStatusType.ARCHIVED)

    @property
    def is_indexed(self) -> bool:
        return self.value == DocumentStatusType.INDEXED
