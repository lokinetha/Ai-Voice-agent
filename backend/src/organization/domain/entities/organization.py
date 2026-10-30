"""
Organization Aggregate Root for Organization Bounded Context.

Central Aggregate Root managing multi-tenant boundary, workspaces, subscription plan,
billing info, and organization settings.
"""

from __future__ import annotations

from collections.abc import Sequence

from shared.kernel.aggregate_root import AggregateRoot
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import (
    OrganizationId,
    TenantId,
    Timestamp,
    WorkspaceId,
)

from organization.domain.entities.workspace import Workspace
from organization.domain.events.plan_changed import PlanChanged
from organization.domain.events.workspace_created import WorkspaceCreated
from organization.domain.value_objects.billing_info import BillingInfo
from organization.domain.value_objects.org_settings import OrgSettings
from organization.domain.value_objects.plan import Plan


class Organization(AggregateRoot[OrganizationId]):
    """Organization Aggregate Root.

    Enforces workspace count limits according to subscription Plan invariants.
    """

    def __init__(
        self,
        id: OrganizationId,
        tenant_id: TenantId,
        name: str,
        plan: Plan,
        billing_info: BillingInfo,
        settings: OrgSettings | None = None,
        workspaces: Sequence[Workspace] = (),
        created_at: Timestamp | None = None,
        version: int = 0,
    ) -> None:
        super().__init__(id=id, created_at=created_at, version=version)

        if not name or not isinstance(name, str) or not name.strip():
            raise ValueError("Organization name cannot be empty")

        self._tenant_id = tenant_id
        self._name = name.strip()
        self._plan = plan
        self._billing_info = billing_info
        self._settings = settings or OrgSettings.default()
        self._workspaces: dict[WorkspaceId, Workspace] = {w.id: w for w in workspaces}

    @property
    def tenant_id(self) -> TenantId:
        """Get multi-tenancy tenant identifier."""
        return self._tenant_id

    @property
    def name(self) -> str:
        """Get organization name string."""
        return self._name

    @property
    def plan(self) -> Plan:
        """Get subscription plan value object."""
        return self._plan

    @property
    def billing_info(self) -> BillingInfo:
        """Get billing info value object."""
        return self._billing_info

    @property
    def settings(self) -> OrgSettings:
        """Get org settings value object."""
        return self._settings

    @property
    def workspaces(self) -> tuple[Workspace, ...]:
        """Get immutable view of child Workspace entities."""
        return tuple(self._workspaces.values())

    def get_workspace(self, workspace_id: WorkspaceId) -> Workspace | None:
        """Get workspace by ID."""
        return self._workspaces.get(workspace_id)

    def create_workspace(
        self, name: str, workspace_id: WorkspaceId | None = None
    ) -> Result[Workspace]:
        """Create a new Workspace child entity within Plan limits.

        Args:
            name: Name of workspace to create.
            workspace_id: Optional explicit WorkspaceId.

        Returns:
            Result wrapping created Workspace on success, or LIMIT_EXCEEDED Error.
        """
        # Aggregate Invariant check: workspace count <= plan.max_workspaces
        if len(self._workspaces) >= self._plan.max_workspaces:
            return Result.fail(
                Error(
                    "LIMIT_EXCEEDED",
                    f"Workspace limit reached for {self._plan.tier.value} plan "
                    f"(max {self._plan.max_workspaces})",
                )
            )

        ws_id = workspace_id or WorkspaceId()
        workspace = Workspace(id=ws_id, name=name, status="active")
        self._workspaces[ws_id] = workspace

        self._raise_event(
            WorkspaceCreated(
                organization_id=str(self.id.value),
                workspace_id=str(ws_id.value),
                workspace_name=name,
                tenant_id=str(self.tenant_id.value),
            )
        )

        return Result.ok(workspace)

    def change_plan(self, new_plan: Plan) -> Result[None]:
        """Upgrade or downgrade Organization subscription plan.

        Args:
            new_plan: Target Plan value object.

        Returns:
            Result indicating success or INVARIANT_VIOLATION if workspace count exceeds target plan limit.
        """
        if len(self._workspaces) > new_plan.max_workspaces:
            return Result.fail(
                Error(
                    "INVARIANT_VIOLATION",
                    f"Cannot downgrade to {new_plan.tier.value}: existing workspace count "
                    f"({len(self._workspaces)}) exceeds plan limit ({new_plan.max_workspaces})",
                )
            )

        old_tier = self._plan.tier.value
        self._plan = new_plan

        self._raise_event(
            PlanChanged(
                organization_id=str(self.id.value),
                tenant_id=str(self.tenant_id.value),
                old_plan_tier=old_tier,
                new_plan_tier=new_plan.tier.value,
            )
        )

        return Result.ok(None)

    def update_settings(self, new_settings: OrgSettings) -> Result[None]:
        """Update Organization settings value object."""
        self._settings = new_settings
        return Result.ok(None)
