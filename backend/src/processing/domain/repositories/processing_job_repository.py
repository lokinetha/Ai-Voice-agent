"""
ProcessingJobRepository Domain Interface for Processing Bounded Context.
"""

from __future__ import annotations

from abc import abstractmethod

from shared.kernel.repository import Repository
from shared.kernel.value_objects import DocumentId, EntityId, WorkspaceId

from processing.domain.entities.processing_job import ProcessingJob


class ProcessingJobRepository(Repository[ProcessingJob, EntityId]):
    """Domain Repository Interface for ProcessingJob Aggregate Root."""

    @abstractmethod
    async def find_by_workspace(
        self, workspace_id: WorkspaceId
    ) -> list[ProcessingJob]:
        """Find all ProcessingJobs in target Workspace.

        Args:
            workspace_id: WorkspaceId value object.

        Returns:
            List of matching ProcessingJob aggregate roots.
        """
        ...

    @abstractmethod
    async def find_by_document(
        self, document_id: DocumentId
    ) -> list[ProcessingJob]:
        """Find all ProcessingJobs for a given Document.

        Args:
            document_id: DocumentId value object.

        Returns:
            List of matching ProcessingJob aggregate roots.
        """
        ...
