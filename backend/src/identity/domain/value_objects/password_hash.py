"""
PasswordHash Value Object for Identity Bounded Context.

Encapsulates hashed password strings and hashing algorithm metadata.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class PasswordHash(ValueObject):
    """Immutable PasswordHash Value Object storing hashed credential string and algorithm name."""

    hash_value: str
    algorithm: str = "argon2id"

    def _validate(self) -> None:
        if not self.hash_value or not isinstance(self.hash_value, str) or not self.hash_value.strip():
            raise ValueError("PasswordHash hash_value cannot be empty")
        if not self.algorithm or not isinstance(self.algorithm, str):
            raise ValueError("PasswordHash algorithm cannot be empty")

    @classmethod
    def create(cls, hash_value: str, algorithm: str = "argon2id") -> PasswordHash:
        """Factory method to construct PasswordHash."""
        return cls(hash_value=hash_value, algorithm=algorithm)
