"""
FakeKnowledgeRetrievalAdapter implementing KnowledgeRetrievalPort.

In-memory test double for Knowledge retrieval with optional simulated failure mode.
"""

from __future__ import annotations

from agent_runtime.application.ports.knowledge_retrieval_port import (
    KnowledgeRetrievalPort,
)


class FakeKnowledgeRetrievalAdapter(KnowledgeRetrievalPort):
    """In-memory test double for KnowledgeRetrievalPort."""

    def __init__(
        self,
        snippets: list[str] | None = None,
        should_fail: bool = False,
        error_message: str = "Knowledge database unreachable",
    ) -> None:
        self.snippets = snippets or ["Default knowledge context snippet."]
        self.should_fail = should_fail
        self.error_message = error_message

    async def retrieve_knowledge(
        self, workspace_id: str, query: str, top_k: int = 3
    ) -> list[str]:
        """Retrieve simulated knowledge context or raise failure."""
        if self.should_fail:
            raise RuntimeError(self.error_message)

        return self.snippets[:top_k]
