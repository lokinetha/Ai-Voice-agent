"""
Playbook Aggregate Root for Playbook Bounded Context.

Represents the behavioral playbook used to configure an AI Agent.
The Playbook describes HOW the agent should behave; it is NOT an LLM prompt.
"""

from __future__ import annotations

from collections.abc import Sequence

from shared.kernel.aggregate_root import AggregateRoot
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import (
    EntityId,
    PlaybookId,
    PlaybookVersion,
    Timestamp,
    WorkspaceId,
)

from playbook.domain.entities.playbook_example import PlaybookExample
from playbook.domain.entities.playbook_goal import PlaybookGoal
from playbook.domain.entities.playbook_objection import PlaybookObjection
from playbook.domain.entities.playbook_rule import PlaybookRule
from playbook.domain.entities.playbook_stage import PlaybookStage
from playbook.domain.entities.playbook_transition import PlaybookTransition
from playbook.domain.events.playbook_archived import PlaybookArchived
from playbook.domain.events.playbook_published import PlaybookPublished
from playbook.domain.events.playbook_updated import PlaybookUpdated
from playbook.domain.events.playbook_version_created import PlaybookVersionCreated
from playbook.domain.value_objects.communication_style import CommunicationStyle
from playbook.domain.value_objects.persona import Persona
from playbook.domain.value_objects.playbook_status import PlaybookStatus
from playbook.domain.value_objects.playbook_version_info import PlaybookVersionInfo
from playbook.domain.value_objects.success_criteria import SuccessCriteria


class Playbook(AggregateRoot[PlaybookId]):
    """Playbook Aggregate Root.

    Enforces invariants:
    - Only valid playbooks can be published (valid persona, at least 1 goal, valid stage transitions).
    - Published versions are immutable.
    - Must have a defined persona.
    - Must have at least one goal.
    - Conversation stages must have valid transitions connecting them.
    - Every published version is immutable and independently identifiable.
    """

    def __init__(
        self,
        id: PlaybookId,
        workspace_id: WorkspaceId,
        name: str,
        description: str = "",
        status: PlaybookStatus | None = None,
        version_info: PlaybookVersionInfo | None = None,
        persona: Persona | None = None,
        communication_style: CommunicationStyle | None = None,
        success_criteria: SuccessCriteria | None = None,
        goals: Sequence[PlaybookGoal] = (),
        stages: Sequence[PlaybookStage] = (),
        rules: Sequence[PlaybookRule] = (),
        objections: Sequence[PlaybookObjection] = (),
        examples: Sequence[PlaybookExample] = (),
        transitions: Sequence[PlaybookTransition] = (),
        created_at: Timestamp | None = None,
        version: int = 1,
    ) -> None:
        super().__init__(id=id, created_at=created_at, version=version)

        if not name or not name.strip():
            raise ValueError("Playbook name cannot be empty")

        self._workspace_id = workspace_id
        self._name = name.strip()
        self._description = description.strip()
        self._status = status or PlaybookStatus.draft()
        self._version_info = version_info or PlaybookVersionInfo()
        self._persona = persona
        self._communication_style = communication_style or CommunicationStyle.default()
        self._success_criteria = success_criteria
        self._goals: list[PlaybookGoal] = list(goals)
        self._stages: list[PlaybookStage] = list(stages)
        self._rules: list[PlaybookRule] = list(rules)
        self._objections: list[PlaybookObjection] = list(objections)
        self._examples: list[PlaybookExample] = list(examples)
        self._transitions: list[PlaybookTransition] = list(transitions)

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def workspace_id(self) -> WorkspaceId:
        return self._workspace_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def status(self) -> PlaybookStatus:
        return self._status

    @property
    def version_info(self) -> PlaybookVersionInfo:
        return self._version_info

    @property
    def persona(self) -> Persona | None:
        return self._persona

    @property
    def communication_style(self) -> CommunicationStyle:
        return self._communication_style

    @property
    def success_criteria(self) -> SuccessCriteria | None:
        return self._success_criteria

    @property
    def goals(self) -> tuple[PlaybookGoal, ...]:
        return tuple(self._goals)

    @property
    def stages(self) -> tuple[PlaybookStage, ...]:
        return tuple(self._stages)

    @property
    def rules(self) -> tuple[PlaybookRule, ...]:
        return tuple(self._rules)

    @property
    def objections(self) -> tuple[PlaybookObjection, ...]:
        return tuple(self._objections)

    @property
    def examples(self) -> tuple[PlaybookExample, ...]:
        return tuple(self._examples)

    @property
    def transitions(self) -> tuple[PlaybookTransition, ...]:
        return tuple(self._transitions)

    # ── Mutators ──────────────────────────────────────────────────────────

    def update_metadata(self, name: str, description: str = "") -> Result[None]:
        """Update Playbook name and description."""
        if self._status.is_archived:
            return Result.fail(Error("INVALID_STATE", "Cannot update archived playbook"))

        if not name or not name.strip():
            return Result.fail(Error("VALIDATION_ERROR", "Playbook name cannot be empty"))

        self._name = name.strip()
        self._description = description.strip()
        self._raise_event(PlaybookUpdated(playbook_id=str(self.id.value), name=self._name))
        return Result.ok(None)

    def set_persona(self, persona: Persona) -> Result[None]:
        """Set the persona describing WHO the agent is."""
        if self._status.is_archived:
            return Result.fail(Error("INVALID_STATE", "Cannot modify archived playbook"))

        self._persona = persona
        self._raise_event(PlaybookUpdated(playbook_id=str(self.id.value), name=self._name))
        return Result.ok(None)

    def set_communication_style(self, style: CommunicationStyle) -> Result[None]:
        """Set the agent communication style."""
        if self._status.is_archived:
            return Result.fail(Error("INVALID_STATE", "Cannot modify archived playbook"))

        self._communication_style = style
        self._raise_event(PlaybookUpdated(playbook_id=str(self.id.value), name=self._name))
        return Result.ok(None)

    def set_success_criteria(self, criteria: SuccessCriteria) -> Result[None]:
        """Set success criteria for the playbook."""
        if self._status.is_archived:
            return Result.fail(Error("INVALID_STATE", "Cannot modify archived playbook"))

        self._success_criteria = criteria
        self._raise_event(PlaybookUpdated(playbook_id=str(self.id.value), name=self._name))
        return Result.ok(None)

    def add_goal(self, goal: PlaybookGoal) -> Result[None]:
        """Add a goal to the playbook."""
        if self._status.is_archived:
            return Result.fail(Error("INVALID_STATE", "Cannot modify archived playbook"))

        self._goals.append(goal)
        self._raise_event(PlaybookUpdated(playbook_id=str(self.id.value), name=self._name))
        return Result.ok(None)

    def remove_goal(self, goal_id: EntityId) -> Result[None]:
        """Remove a goal from the playbook."""
        if self._status.is_archived:
            return Result.fail(Error("INVALID_STATE", "Cannot modify archived playbook"))

        self._goals = [g for g in self._goals if g.id != goal_id]
        self._raise_event(PlaybookUpdated(playbook_id=str(self.id.value), name=self._name))
        return Result.ok(None)

    def add_stage(self, stage: PlaybookStage) -> Result[None]:
        """Add a stage to the playbook."""
        if self._status.is_archived:
            return Result.fail(Error("INVALID_STATE", "Cannot modify archived playbook"))

        self._stages.append(stage)
        self._raise_event(PlaybookUpdated(playbook_id=str(self.id.value), name=self._name))
        return Result.ok(None)

    def add_rule(self, rule: PlaybookRule) -> Result[None]:
        """Add a rule to the playbook."""
        if self._status.is_archived:
            return Result.fail(Error("INVALID_STATE", "Cannot modify archived playbook"))

        self._rules.append(rule)
        self._raise_event(PlaybookUpdated(playbook_id=str(self.id.value), name=self._name))
        return Result.ok(None)

    def add_objection(self, objection: PlaybookObjection) -> Result[None]:
        """Add an objection handler to the playbook."""
        if self._status.is_archived:
            return Result.fail(Error("INVALID_STATE", "Cannot modify archived playbook"))

        self._objections.append(objection)
        self._raise_event(PlaybookUpdated(playbook_id=str(self.id.value), name=self._name))
        return Result.ok(None)

    def add_example(self, example: PlaybookExample) -> Result[None]:
        """Add an example to the playbook."""
        if self._status.is_archived:
            return Result.fail(Error("INVALID_STATE", "Cannot modify archived playbook"))

        self._examples.append(example)
        self._raise_event(PlaybookUpdated(playbook_id=str(self.id.value), name=self._name))
        return Result.ok(None)

    def add_transition(self, transition: PlaybookTransition) -> Result[None]:
        """Add a stage transition to the playbook."""
        if self._status.is_archived:
            return Result.fail(Error("INVALID_STATE", "Cannot modify archived playbook"))

        stage_ids = {s.id for s in self._stages}
        if transition.from_stage_id not in stage_ids or transition.to_stage_id not in stage_ids:
            return Result.fail(
                Error(
                    "INVARIANT_VIOLATION",
                    "Transition connects stage IDs that do not exist in the playbook",
                )
            )

        self._transitions.append(transition)
        self._raise_event(PlaybookUpdated(playbook_id=str(self.id.value), name=self._name))
        return Result.ok(None)

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def validate_publishability(self) -> Result[None]:
        """Validate whether the playbook satisfies publishability invariants."""
        if self._persona is None:
            return Result.fail(Error("INVARIANT_VIOLATION", "Playbook must have a defined Persona"))

        if len(self._goals) == 0:
            return Result.fail(Error("INVARIANT_VIOLATION", "Playbook must have at least one Goal"))

        if len(self._stages) > 1:
            # Verify every transition connects existing stages
            stage_ids = {s.id for s in self._stages}
            for t in self._transitions:
                if t.from_stage_id not in stage_ids or t.to_stage_id not in stage_ids:
                    return Result.fail(
                        Error("INVARIANT_VIOLATION", f"Invalid transition between stages: {t.from_stage_id} -> {t.to_stage_id}")
                    )

        return Result.ok(None)

    def publish(self, label: str = "", changelog: str = "") -> Result[PlaybookVersion]:
        """Publish the Playbook creating an immutable version snapshot."""
        if self._status.is_archived:
            return Result.fail(Error("INVALID_STATE", "Cannot publish archived playbook"))

        val_res = self.validate_publishability()
        if val_res.is_failure:
            return Result.fail(val_res.error)

        self._status = PlaybookStatus.published()
        self._version_info = self._version_info.next(label=label, changelog=changelog)
        self._version += 1

        version_id = PlaybookVersion()

        self._raise_event(
            PlaybookPublished(
                playbook_id=str(self.id.value),
                version_number=self._version_info.version_number,
            )
        )
        self._raise_event(
            PlaybookVersionCreated(
                playbook_id=str(self.id.value),
                version_id=str(version_id.value),
                version_number=self._version_info.version_number,
            )
        )

        return Result.ok(version_id)

    def archive(self, reason: str = "") -> Result[None]:
        """Archive the Playbook."""
        if self._status.is_archived:
            return Result.fail(Error("INVALID_STATE", "Playbook is already archived"))

        self._status = PlaybookStatus.archived()
        self._raise_event(
            PlaybookArchived(
                playbook_id=str(self.id.value),
                reason=reason,
            )
        )
        return Result.ok(None)
