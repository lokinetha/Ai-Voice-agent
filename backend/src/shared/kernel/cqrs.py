"""
CQRS Base Abstractions.

Defines Command, Query, CommandHandler, and QueryHandler primitives for separating
read and write paths.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeVar

from shared.kernel.result import Result

# ── Message Primitives ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Command:
    """Base dataclass for all Commands. Commands represent state-mutating intent."""



@dataclass(frozen=True)
class Query:
    """Base dataclass for all Queries. Queries represent side-effect-free data retrieval requests."""



# ── Handler Primitives ────────────────────────────────────────────────────────

TResult = TypeVar("TResult")
TCommand = TypeVar("TCommand", bound=Command)
TQuery = TypeVar("TQuery", bound=Query)


class CommandHandler[TCommand: Command, TResult](ABC):
    """Interface for handling Commands."""

    @abstractmethod
    async def handle(self, command: TCommand) -> Result[TResult]:
        """Execute command business logic and return Result.

        Args:
            command: Concrete Command instance.

        Returns:
            Result wrapping the operation outcome.
        """
        ...


class QueryHandler[TQuery: Query, TResult](ABC):
    """Interface for handling Queries."""

    @abstractmethod
    async def handle(self, query: TQuery) -> Result[TResult]:
        """Execute query evaluation logic and return Result.

        Args:
            query: Concrete Query instance.

        Returns:
            Result wrapping the queried data DTO or view.
        """
        ...
