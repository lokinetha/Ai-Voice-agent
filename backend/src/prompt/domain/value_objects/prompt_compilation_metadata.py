"""
PromptCompilationMetadata Value Object.

Preserves source Playbook version and compilation provenance metadata.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class PromptCompilationMetadata(ValueObject):
    """Immutable metadata tracking compilation inputs and SHA256 checksum.

    Attributes:
        source_playbook_id: ID of source Playbook.
        source_playbook_version: Version number of source Playbook.
        compiled_at: UTC timestamp when compilation occurred.
        template_name: Name of template used for compilation.
        checksum: SHA256 hash of final compiled prompt text.
    """

    source_playbook_id: str = ""
    source_playbook_version: int = 1
    compiled_at: datetime = datetime.now(UTC)
    template_name: str = "STANDARD_SYSTEM_PROMPT"
    checksum: str = ""

    def _validate(self) -> None:
        if self.source_playbook_version < 1:
            raise ValueError("source_playbook_version must be >= 1")

    @classmethod
    def compute(
        cls,
        source_playbook_id: str,
        source_playbook_version: int,
        compiled_text: str,
        template_name: str = "STANDARD_SYSTEM_PROMPT",
    ) -> PromptCompilationMetadata:
        """Compute SHA256 checksum and return compilation metadata."""
        sha = hashlib.sha256(compiled_text.encode("utf-8")).hexdigest()
        return cls(
            source_playbook_id=source_playbook_id,
            source_playbook_version=source_playbook_version,
            compiled_at=datetime.now(UTC),
            template_name=template_name,
            checksum=sha,
        )
