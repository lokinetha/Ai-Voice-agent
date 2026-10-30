"""
Result Monad and Error primitives for Railway-Oriented Programming.

Replaces exception-driven flow control for expected business logic failures.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Error:
    """Structured Error detail object for Result failures.

    Attributes:
        code: Error code string (e.g., 'NOT_FOUND', 'VALIDATION_ERROR').
        message: Human-readable error message.
        details: Optional contextual metadata dictionary.
    """

    code: str
    message: str
    details: dict[str, Any] | None = None


@dataclass
class Result[T]:
    """Monadic Result wrapper representing success (value) or failure (Error)."""

    _value: T | None
    _error: Error | None

    @classmethod
    def ok(cls, value: T) -> Result[T]:
        """Construct a successful Result containing a value."""
        return cls(_value=value, _error=None)

    @classmethod
    def fail(cls, error: Error) -> Result[T]:
        """Construct a failed Result containing an Error."""
        return cls(_value=None, _error=error)

    @property
    def is_success(self) -> bool:
        """Returns True if the operation succeeded."""
        return self._error is None

    @property
    def is_failure(self) -> bool:
        """Returns True if the operation failed."""
        return self._error is not None

    @property
    def value(self) -> T:
        """Extract value from successful result.

        Raises:
            ValueError: If accessed on a failed result.
        """
        if self._error is not None:
            raise ValueError(f"Cannot access value of failed result: {self._error}")
        return self._value  # type: ignore[return-value]

    @property
    def error(self) -> Error:
        """Extract Error from failed result.

        Raises:
            ValueError: If accessed on a successful result.
        """
        if self._error is None:
            raise ValueError("Cannot access error of successful result")
        return self._error
