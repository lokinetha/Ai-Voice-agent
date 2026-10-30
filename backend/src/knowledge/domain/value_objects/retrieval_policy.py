"""
RetrievalPolicy Value Object for Knowledge Bounded Context.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class RetrievalPolicy(ValueObject):
    """RetrievalPolicy Value Object defining search and retrieval strategy."""

    top_k: int = 5
    similarity_threshold: float = 0.7
    strategy: str = "hybrid"
    reranking_enabled: bool = False

    def _validate(self) -> None:
        if not 1 <= self.top_k <= 100:
            raise ValueError(f"top_k must be between 1 and 100, got: {self.top_k}")
        if not 0.0 <= self.similarity_threshold <= 1.0:
            raise ValueError(f"similarity_threshold must be between 0.0 and 1.0, got: {self.similarity_threshold}")
        if self.strategy not in ("dense", "sparse", "hybrid"):
            raise ValueError(f"Invalid retrieval strategy: {self.strategy}")

    @classmethod
    def default(cls) -> RetrievalPolicy:
        """Construct default hybrid retrieval policy."""
        return cls(top_k=5, similarity_threshold=0.7, strategy="hybrid", reranking_enabled=False)
