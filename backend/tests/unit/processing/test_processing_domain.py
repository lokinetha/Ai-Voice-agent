"""
Unit tests for Processing Domain Layer — Aggregate Root, Entities, Value Objects,
Factory, Specifications, and Domain Services.
"""

from __future__ import annotations

import unittest

from processing.domain.events.processing_completed import ProcessingCompleted
from processing.domain.events.processing_failed import ProcessingFailed
from processing.domain.events.processing_started import ProcessingStarted
from processing.domain.factories.processing_job_factory import (
    ProcessingJobFactory,
)
from processing.domain.services.processing_validation_service import (
    ProcessingValidationService,
)
from processing.domain.specifications.valid_processing_job_spec import (
    ValidProcessingJobSpec,
)
from processing.domain.value_objects.chunking_strategy import ChunkingStrategy
from processing.domain.value_objects.embedding_strategy import EmbeddingStrategy
from processing.domain.value_objects.processing_job_status import (
    ProcessingJobStatusType,
)
from processing.domain.value_objects.processing_result import ProcessingResult
from processing.domain.value_objects.processing_task_type import TaskCategory
from shared.kernel.value_objects import DocumentId, WorkspaceId


class TestProcessingJobFactory(unittest.TestCase):
    """Tests for ProcessingJobFactory."""

    def test_factory_creates_job_with_4_tasks(self) -> None:
        job = ProcessingJobFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            document_id=DocumentId("doc-1"),
        )

        self.assertEqual(job.status.value, ProcessingJobStatusType.PENDING)
        self.assertEqual(len(job.tasks), 4)

        categories = [t.task_type.category.value for t in job.tasks]
        self.assertEqual(categories, ["PARSING", "CHUNKING", "EMBEDDING", "INDEXING"])


class TestProcessingJobAggregate(unittest.TestCase):
    """Tests for ProcessingJob Aggregate Root rules and state machine."""

    def _make_job(self) -> ProcessingJobFactory:
        return ProcessingJobFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            document_id=DocumentId("doc-1"),
        )

    def test_job_lifecycle_start_complete_tasks_and_job(self) -> None:
        job = self._make_job()
        job.clear_events()

        # Start job
        start_res = job.start()
        self.assertTrue(start_res.is_success)
        self.assertEqual(job.status.value, ProcessingJobStatusType.RUNNING)
        self.assertEqual(len(job.domain_events), 1)
        self.assertIsInstance(job.domain_events[0], ProcessingStarted)

        # Complete parsing task
        p_res = job.complete_task(
            TaskCategory.PARSING,
            ProcessingResult(output_count=1, execution_time_seconds=0.1),
        )
        self.assertTrue(p_res.is_success)
        self.assertTrue(job.tasks[0].status.is_completed)
        self.assertTrue(job.tasks[1].status.is_running)

        # Complete overall job
        job.clear_events()
        comp_res = job.complete_job(
            chunk_refs=["c-1", "c-2"],
            vector_refs=["v-1", "v-2"],
        )
        self.assertTrue(comp_res.is_success)
        self.assertEqual(job.status.value, ProcessingJobStatusType.COMPLETED)
        self.assertEqual(len(job.chunk_references), 2)
        self.assertEqual(len(job.vector_references), 2)
        self.assertTrue(any(isinstance(e, ProcessingCompleted) for e in job.domain_events))

    def test_fail_job(self) -> None:
        job = self._make_job()
        job.start()
        job.clear_events()

        fail_res = job.fail_job("PDF parse error")
        self.assertTrue(fail_res.is_success)
        self.assertEqual(job.status.value, ProcessingJobStatusType.FAILED)
        self.assertEqual(job.error_message, "PDF parse error")
        self.assertTrue(any(isinstance(e, ProcessingFailed) for e in job.domain_events))

    def test_cannot_start_already_running_or_completed_job(self) -> None:
        job = self._make_job()
        job.start()
        self.assertTrue(job.start().is_failure)

    def test_value_object_validations(self) -> None:
        with self.assertRaises(ValueError):
            ChunkingStrategy(chunk_size=-100)

        with self.assertRaises(ValueError):
            ChunkingStrategy(chunk_size=100, chunk_overlap=150)

        with self.assertRaises(ValueError):
            EmbeddingStrategy(dimension=0)


class TestSpecifications(unittest.TestCase):
    """Tests for Processing specifications."""

    def test_valid_processing_job_spec(self) -> None:
        spec = ValidProcessingJobSpec()
        job = ProcessingJobFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            document_id=DocumentId("doc-1"),
        )
        self.assertTrue(spec.is_satisfied_by(job))


class TestProcessingValidationService(unittest.TestCase):
    """Tests for ProcessingValidationService."""

    def test_service_validates_job(self) -> None:
        svc = ProcessingValidationService()
        job = ProcessingJobFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            document_id=DocumentId("doc-1"),
        )
        res = svc.validate_job(job)
        self.assertTrue(res.is_success)


if __name__ == "__main__":
    unittest.main()
