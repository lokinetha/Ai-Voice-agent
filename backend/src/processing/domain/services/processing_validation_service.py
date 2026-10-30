"""
ProcessingValidationService Domain Service for Processing Bounded Context.

Validates ProcessingJob structure and execution readiness.
"""

from __future__ import annotations

from shared.kernel.domain_service import DomainService
from shared.kernel.result import Error, Result

from processing.domain.entities.processing_job import ProcessingJob
from processing.domain.specifications.valid_processing_job_spec import (
    ValidProcessingJobSpec,
)


class ProcessingValidationService(DomainService):
    """Domain Service validating ProcessingJob readiness and validity."""

    def __init__(self) -> None:
        self._valid_spec = ValidProcessingJobSpec()

    def validate_job(self, job: ProcessingJob) -> Result[None]:
        """Validate basic ProcessingJob integrity.

        Args:
            job: ProcessingJob aggregate root.

        Returns:
            Result indicating success or VALIDATION_ERROR.
        """
        if not self._valid_spec.is_satisfied_by(job):
            return Result.fail(Error("VALIDATION_ERROR", "ProcessingJob fails basic validity check"))

        return Result.ok(None)
