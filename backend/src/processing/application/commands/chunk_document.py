"""
ChunkDocument Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result

from processing.domain.ports.chunking_port import ChunkingPort
from processing.domain.value_objects.chunking_strategy import ChunkingStrategy


@dataclass(frozen=True)
class ChunkDocumentCommand(Command):
    """Command requesting document text chunking."""

    text: str
    chunk_size: int = 500
    chunk_overlap: int = 50
    strategy_type: str = "FIXED_SIZE"


class ChunkDocumentHandler(CommandHandler[ChunkDocumentCommand, tuple[str, ...]]):
    """Handler executing ChunkDocumentCommand."""

    def __init__(self, chunking_port: ChunkingPort) -> None:
        self._chunking = chunking_port

    async def handle(self, command: ChunkDocumentCommand) -> Result[tuple[str, ...]]:
        """Execute text chunking."""
        if not command.text or not command.text.strip():
            return Result.fail(Error("VALIDATION_ERROR", "Text content cannot be empty"))

        try:
            strategy = ChunkingStrategy(
                strategy_type=command.strategy_type,
                chunk_size=command.chunk_size,
                chunk_overlap=command.chunk_overlap,
            )
        except ValueError as err:
            return Result.fail(Error("VALIDATION_ERROR", str(err)))

        chunks = await self._chunking.chunk_text(command.text, strategy)
        return Result.ok(tuple(chunks))
