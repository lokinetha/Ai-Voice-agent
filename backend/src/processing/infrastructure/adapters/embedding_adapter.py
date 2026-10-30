"""
EmbeddingAdapter implementing EmbeddingPort.

Provider-independent deterministic vector embedding generator adapter.
"""

from __future__ import annotations

import hashlib

from processing.domain.ports.embedding_port import EmbeddingPort
from processing.domain.value_objects.embedding_strategy import EmbeddingStrategy


class EmbeddingAdapter(EmbeddingPort):
    """Deterministic vector embedding adapter producing normalized float arrays."""

    async def generate_embeddings(
        self, texts: list[str], strategy: EmbeddingStrategy
    ) -> list[list[float]]:
        """Generate normalized float vector embeddings for input text strings.

        Uses deterministic SHA256 pseudo-random projection to construct vector arrays of
        the requested dimension without calling vendor APIs.

        Args:
            texts: List of text chunk strings.
            strategy: EmbeddingStrategy parameters.

        Returns:
            List of float vector arrays.
        """
        results: list[list[float]] = []

        for text in texts:
            dim = strategy.dimension
            vector: list[float] = []
            seed_bytes = hashlib.sha256(text.encode("utf-8")).digest()

            for i in range(dim):
                byte_val = seed_bytes[i % len(seed_bytes)]
                # Project byte value to normalized range [-1.0, 1.0]
                val = ((byte_val + i) % 256) / 128.0 - 1.0
                vector.append(round(val, 6))

            results.append(vector)

        return results
