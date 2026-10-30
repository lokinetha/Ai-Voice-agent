"""
DocumentMetadata Value Object for Knowledge Bounded Context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class DocumentMetadata(ValueObject):
    """DocumentMetadata Value Object storing file properties and tags."""

    file_type: str
    size_bytes: int
    source_url: str | None = None
    mime_type: str = "application/pdf"
    tags: dict[str, Any] = field(default_factory=dict)

    def _validate(self) -> None:
        if not self.file_type or not isinstance(self.file_type, str):
            raise ValueError("file_type cannot be empty")
        if self.size_bytes < 0:
            raise ValueError("size_bytes cannot be negative")

    @classmethod
    def create(
        cls,
        file_type: str,
        size_bytes: int,
        source_url: str | None = None,
        mime_type: str = "application/pdf",
        tags: dict[str, Any] | None = None,
    ) -> DocumentMetadata:
        """Factory method constructing DocumentMetadata."""
        return cls(
            file_type=file_type.lower(),
            size_bytes=size_bytes,
            source_url=source_url,
            mime_type=mime_type,
            tags=dict(tags) if tags else {},
        )
