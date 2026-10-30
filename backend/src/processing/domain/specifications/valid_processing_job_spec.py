"""
ValidProcessingJobSpec Specification for Processing Bounded Context.
"""

from __future__ import annotations

from shared.kernel.specification import Specification

from processing.domain.entities.processing_job import ProcessingJob


class ValidProcessingJobSpec(Specification[ProcessingJob]):
    """Specification checking overall structural validity of a ProcessingJob."""

    def is_satisfied_by(self, candidate: ProcessingJob) -> bool:
        if not candidate.document_id or not str(candidate.document_id.value).strip():
            return False
        if not candidate.workspace_id or not str(candidate.workspace_id.value).strip():
            return False
        return True
