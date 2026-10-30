"""
ObjectStoragePort Interface for Processing Bounded Context.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class ObjectStoragePort(ABC):
    """Abstract port for storing and retrieving raw binary objects."""

    @abstractmethod
    async def store_object(self, bucket: str, key: str, data: bytes) -> str:
        """Store binary data under a bucket and key.

        Args:
            bucket: Storage bucket identifier.
            key: Storage object key path.
            data: Binary payload.

        Returns:
            Object reference URI.
        """
        ...

    @abstractmethod
    async def fetch_object(self, bucket: str, key: str) -> bytes:
        """Retrieve binary payload from bucket and key.

        Args:
            bucket: Storage bucket identifier.
            key: Storage object key path.

        Returns:
            Binary payload bytes.
        """
        ...
