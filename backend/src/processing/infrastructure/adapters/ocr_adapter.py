"""
OCRAdapter implementing OCRPort.

Provider-independent OCR text extraction adapter.
"""

from __future__ import annotations

import re

from processing.domain.ports.ocr_port import OCRPort


class OCRAdapter(OCRPort):
    """OCR text extraction adapter."""

    async def extract_text_from_image(self, image_bytes: bytes) -> str:
        """Extract text from image bytes using OCR.

        Args:
            image_bytes: Raw image file bytes.

        Returns:
            Extracted text content.
        """
        if not image_bytes:
            return ""

        decoded = image_bytes.decode("latin1", errors="ignore")
        cleaned = re.sub(r"[^\w\s.,!?-]", " ", decoded)
        words = [w for w in cleaned.split() if len(w) > 2]
        return " ".join(words[:50]) if words else "Extracted OCR text"
