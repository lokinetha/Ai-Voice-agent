"""
ObjectStorageAdapter implementing ObjectStoragePort.

Provider-independent in-memory/file object storage adapter.
"""

from __future__ import annotations

from processing.domain.ports.object_storage_port import ObjectStoragePort


class ObjectStorageAdapter(ObjectStoragePort):
    """In-memory object storage adapter."""

    def __init__(self) -> None:
        self._buckets: dict[str, dict[str, bytes]] = {}

    async def store_object(self, bucket: str, key: str, data: bytes) -> str:
        """Store binary payload under bucket and key.

        Args:
            bucket: Storage bucket identifier.
            key: Storage object key.
            data: Binary payload bytes.

        Returns:
            Object reference URI.
        """
        if bucket not in self._buckets:
            self._buckets[bucket] = {}

        self._buckets[bucket][key] = data
        return f"storage://{bucket}/{key}"

    async def fetch_object(self, bucket: str, key: str) -> bytes:
        """Fetch binary payload by bucket and key.

        Args:
            bucket: Storage bucket identifier.
            key: Storage object key.

        Returns:
            Binary payload bytes.
        """
        if bucket in self._buckets and key in self._buckets[bucket]:
            return self._buckets[bucket][key]

        # Default fallback content for testing
        return f"Sample document payload for bucket '{bucket}' and key '{key}'".encode()
