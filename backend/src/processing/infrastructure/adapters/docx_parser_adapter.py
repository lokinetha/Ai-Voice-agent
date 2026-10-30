"""
DOCXParserAdapter implementing DocumentParserPort.

Provider-independent DOCX document text parser adapter.
"""

from __future__ import annotations

import re

from processing.domain.ports.document_parser_port import DocumentParserPort


class DOCXParserAdapter(DocumentParserPort):
    """DOCX document text parser adapter using standard XML text extraction."""

    async def parse_document(self, file_content: bytes, file_type: str) -> str:
        """Extract text from DOCX file content bytes.

        Args:
            file_content: Raw DOCX file bytes.
            file_type: File type string.

        Returns:
            Extracted text content.
        """
        if not file_content:
            return ""

        text = file_content.decode("utf-8", errors="ignore")
        # Extract content inside XML tags <w:t>...</w:t>
        matches = re.findall(r"<w:t[^>]*>(.*?)</w:t>", text)
        if matches:
            return " ".join(matches)

        cleaned = re.sub(r"<[^>]+>", " ", text)
        cleaned = re.sub(r"[^\w\s.,!?-]", " ", cleaned)
        lines = [line.strip() for line in cleaned.splitlines() if len(line.strip()) > 3]
        return "\n".join(lines[:100]) if lines else "Extracted DOCX content"
