"""
EmbeddingPort Interface for Processing Bounded Context.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from processing.domain.value_objects.embedding_strategy import EmbeddingStrategy


class EmbeddingPort(ABC):
    """Abstract port for generating dense embedding vectors from text chunks."""

    @abstractmethod
    async def generate_embeddings(
        self, texts: list[str], strategy: EmbeddingStrategy
    ) -> list[list[float]]:
        """Generate embedding vectors for input text strings.

        Args:
            texts: List of chunk text strings.
            strategy: EmbeddingStrategy parameters.

        Returns:
            List of float vector arrays.
        """
        ...
