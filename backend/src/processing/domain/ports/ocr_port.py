"""
OCRPort Interface for Processing Bounded Context.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class OCRPort(ABC):
    """Abstract port for performing Optical Character Recognition on image bytes."""

    @abstractmethod
    async def extract_text_from_image(self, image_bytes: bytes) -> str:
        """Extract text from image bytes using OCR.

        Args:
            image_bytes: Raw image file bytes.

        Returns:
            Extracted text content string.
        """
        ...
