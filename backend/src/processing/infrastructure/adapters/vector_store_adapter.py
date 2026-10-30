"""
VectorStoreAdapter implementing VectorStorePort.

Provider-independent vector store indexing adapter.
"""

from __future__ import annotations

import uuid
from typing import Any

from processing.domain.ports.vector_store_port import VectorStorePort


class VectorStoreAdapter(VectorStorePort):
    """In-memory vector store indexing adapter."""

    def __init__(self) -> None:
        self._collections: dict[str, list[dict[str, Any]]] = {}

    async def store_vectors(
        self,
        collection_name: str,
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
    ) -> list[str]:
        """Index vectors into target collection.

        Args:
            collection_name: Target collection name.
            vectors: List of embedding vector float arrays.
            payloads: List of associated metadata dictionaries.

        Returns:
            List of generated vector reference IDs.
        """
        if collection_name not in self._collections:
            self._collections[collection_name] = []

        vector_refs: list[str] = []

        for vec, payload in zip(vectors, payloads, strict=False):
            ref_id = f"vec-{uuid.uuid4()}"
            self._collections[collection_name].append(
                {
                    "id": ref_id,
                    "vector": vec,
                    "payload": payload,
                }
            )
            vector_refs.append(ref_id)

        return vector_refs
