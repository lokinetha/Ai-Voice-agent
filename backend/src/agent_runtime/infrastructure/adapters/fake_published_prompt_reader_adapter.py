"""
FakePublishedPromptReaderAdapter implementing PublishedPromptReaderPort.

In-memory test double for loading published Prompt versions.
"""

from __future__ import annotations

from agent_runtime.application.dto.agent_runtime_dto import PublishedPromptDTO
from agent_runtime.application.ports.published_prompt_reader_port import (
    PublishedPromptReaderPort,
)


class FakePublishedPromptReaderAdapter(PublishedPromptReaderPort):
    """In-memory test double for PublishedPromptReaderPort."""

    def __init__(self, prompts: list[PublishedPromptDTO] | None = None) -> None:
        self._prompts: dict[tuple[str, str], PublishedPromptDTO] = {}
        if prompts:
            for p in prompts:
                self.add_prompt(p)

    def add_prompt(self, prompt: PublishedPromptDTO) -> None:
        """Register published Prompt version in memory."""
        self._prompts[(prompt.workspace_id, prompt.agent_id)] = prompt

    async def get_published_prompt(
        self, workspace_id: str, agent_id: str
    ) -> PublishedPromptDTO | None:
        """Retrieve registered published Prompt version."""
        prompt = self._prompts.get((workspace_id, agent_id))
        if prompt and prompt.is_published:
            return prompt
        return None
