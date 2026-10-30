"""
Specification Pattern Implementation.

Encapsulates business rules and query predicates into composable specification objects.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

T = TypeVar("T")


class Specification[T](ABC):
    """Abstract Base Class for Specification pattern.

    Allows composing complex business rule predicates using logical AND, OR, and NOT operations.
    """

    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool:
        """Evaluate if the candidate object satisfies this specification.

        Args:
            candidate: Domain entity or value object under evaluation.

        Returns:
            True if candidate satisfies the specification rule, False otherwise.
        """
        ...

    def and_(self, other: Specification[T]) -> Specification[T]:
        """Combine specifications using logical AND."""
        return _AndSpecification(self, other)

    def or_(self, other: Specification[T]) -> Specification[T]:
        """Combine specifications using logical OR."""
        return _OrSpecification(self, other)

    def not_(self) -> Specification[T]:
        """Negate this specification using logical NOT."""
        return _NotSpecification(self)


class _AndSpecification(Specification[T]):
    def __init__(self, left: Specification[T], right: Specification[T]) -> None:
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        return self._left.is_satisfied_by(candidate) and self._right.is_satisfied_by(candidate)


class _OrSpecification(Specification[T]):
    def __init__(self, left: Specification[T], right: Specification[T]) -> None:
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        return self._left.is_satisfied_by(candidate) or self._right.is_satisfied_by(candidate)


class _NotSpecification(Specification[T]):
    def __init__(self, spec: Specification[T]) -> None:
        self._spec = spec

    def is_satisfied_by(self, candidate: T) -> bool:
        return not self._spec.is_satisfied_by(candidate)
