"""
ChunkingPort Interface for Processing Bounded Context.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from processing.domain.value_objects.chunking_strategy import ChunkingStrategy


class ChunkingPort(ABC):
    """Abstract port for segmenting document text into chunks."""

    @abstractmethod
    async def chunk_text(
        self, text: str, strategy: ChunkingStrategy
    ) -> list[str]:
        """Segment raw text into normalized text chunks according to strategy.

        Args:
            text: Raw input text string.
            strategy: ChunkingStrategy parameters.

        Returns:
            List of chunk text strings.
        """
        ...
