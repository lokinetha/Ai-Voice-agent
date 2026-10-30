"""
ChunkingAdapter implementing ChunkingPort.

Provider-independent deterministic text chunking adapter.
"""

from __future__ import annotations

from processing.domain.ports.chunking_port import ChunkingPort
from processing.domain.value_objects.chunking_strategy import ChunkingStrategy


class ChunkingAdapter(ChunkingPort):
    """Deterministic text chunking adapter."""

    async def chunk_text(
        self, text: str, strategy: ChunkingStrategy
    ) -> list[str]:
        """Segment text into chunks with specified size and overlap.

        Args:
            text: Input raw text string.
            strategy: ChunkingStrategy parameters.

        Returns:
            List of text chunk strings.
        """
        if not text or not text.strip():
            return []

        clean_text = text.strip()
        step = strategy.chunk_size - strategy.chunk_overlap
        if step <= 0:
            step = strategy.chunk_size

        chunks: list[str] = []
        start = 0
        text_length = len(clean_text)

        while start < text_length:
            end = min(start + strategy.chunk_size, text_length)
            chunk = clean_text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= text_length:
                break
            start += step

        return chunks
