"""
EmbeddingStrategy Value Object.

Configures vector embedding generation parameters.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class EmbeddingStrategy(ValueObject):
    """Immutable parameters for embedding vector generation.

    Attributes:
        model_name: Identifier of embedding model (e.g. "text-embedding-004").
        dimension: Dimensionality of vector output (e.g. 768, 1536).
    """

    model_name: str = "standard-text-embedding"
    dimension: int = 768

    def _validate(self) -> None:
        if not self.model_name or not self.model_name.strip():
            raise ValueError("model_name cannot be empty")
        if self.dimension <= 0:
            raise ValueError("dimension must be positive")
