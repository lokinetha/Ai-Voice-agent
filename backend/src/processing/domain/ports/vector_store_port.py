"""
VectorStorePort Interface for Processing Bounded Context.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class VectorStorePort(ABC):
    """Abstract port for indexing vector embeddings into a vector store."""

    @abstractmethod
    async def store_vectors(
        self,
        collection_name: str,
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
    ) -> list[str]:
        """Index vectors into target collection.

        Args:
            collection_name: Target vector store collection name.
            vectors: List of embedding vector float arrays.
            payloads: List of associated metadata dictionaries.

        Returns:
            List of generated vector reference IDs.
        """
        ...
