"""
WorkspaceCreated Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class WorkspaceCreated(DomainEvent):
    """Domain Event published when a new Workspace entity is added to an Organization.

    Attributes:
        organization_id: OrganizationId string.
        workspace_id: WorkspaceId string.
        workspace_name: Name of workspace.
    """

    organization_id: str = ""
    workspace_id: str = ""
    workspace_name: str = ""
