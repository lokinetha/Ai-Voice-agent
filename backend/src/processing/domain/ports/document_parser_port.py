"""
DocumentParserPort Interface for Processing Bounded Context.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class DocumentParserPort(ABC):
    """Abstract port for parsing raw document binary content into plain text."""

    @abstractmethod
    async def parse_document(self, file_content: bytes, file_type: str) -> str:
        """Extract plain text from document bytes.

        Args:
            file_content: Raw document bytes.
            file_type: Document mime type or extension (e.g. "pdf", "docx").

        Returns:
            Extracted text content string.
        """
        ...
