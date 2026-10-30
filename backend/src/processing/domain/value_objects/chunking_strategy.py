"""
ChunkingStrategy Value Object.

Configures document text segmentation parameters.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class ChunkingStrategy(ValueObject):
    """Immutable parameters for document text chunking.

    Attributes:
        strategy_type: Name of chunking strategy (e.g. "FIXED_SIZE", "SEMANTIC", "PARAGRAPH").
        chunk_size: Target size in characters or tokens.
        chunk_overlap: Overlap size in characters or tokens.
    """

    strategy_type: str = "FIXED_SIZE"
    chunk_size: int = 500
    chunk_overlap: int = 50

    def _validate(self) -> None:
        if not self.strategy_type or not self.strategy_type.strip():
            raise ValueError("strategy_type cannot be empty")
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if self.chunk_overlap < 0 or self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be >= 0 and less than chunk_size")
