"""
Base ValueObject implementation for Domain-Driven Design (DDD).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValueObject:
    """Base class for all domain Value Objects.

    Value Objects are immutable data containers defined entirely by their attributes
    rather than a distinct identity. Equal attribute values imply object equality.
    Subclasses should be frozen dataclasses.
    """

    def __post_init__(self) -> None:
        """Enforces domain invariants upon instantiation."""
        self._validate()

    def _validate(self) -> None:
        """Enforce specific domain invariants for the value object.

        Override in concrete subclasses to raise ValueError or domain-specific exceptions.
        """
