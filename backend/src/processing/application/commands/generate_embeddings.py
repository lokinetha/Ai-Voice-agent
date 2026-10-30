"""
GenerateEmbeddings Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result

from processing.domain.ports.embedding_port import EmbeddingPort
from processing.domain.value_objects.embedding_strategy import EmbeddingStrategy


@dataclass(frozen=True)
class GenerateEmbeddingsCommand(Command):
    """Command requesting embedding generation for text chunks."""

    texts: tuple[str, ...]
    model_name: str = "standard-text-embedding"
    dimension: int = 768


class GenerateEmbeddingsHandler(CommandHandler[GenerateEmbeddingsCommand, tuple[tuple[float, ...], ...]]):
    """Handler executing GenerateEmbeddingsCommand."""

    def __init__(self, embedding_port: EmbeddingPort) -> None:
        self._embedding = embedding_port

    async def handle(self, command: GenerateEmbeddingsCommand) -> Result[tuple[tuple[float, ...], ...]]:
        """Execute embedding generation."""
        if not command.texts:
            return Result.fail(Error("VALIDATION_ERROR", "Texts list cannot be empty"))

        try:
            strategy = EmbeddingStrategy(
                model_name=command.model_name,
                dimension=command.dimension,
            )
        except ValueError as err:
            return Result.fail(Error("VALIDATION_ERROR", str(err)))

        vectors = await self._embedding.generate_embeddings(list(command.texts), strategy)
        tuple_vectors = tuple(tuple(v) for v in vectors)
        return Result.ok(tuple_vectors)
