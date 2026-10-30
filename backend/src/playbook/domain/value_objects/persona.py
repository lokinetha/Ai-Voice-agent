"""
Persona Value Object.

Defines the character, role identity, and behavioral persona of an AI Agent.
This is NOT an LLM prompt — it describes WHO the agent is.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class Persona(ValueObject):
    """Immutable value object describing an Agent's persona.

    Attributes:
        name: Display name / alias of the persona (e.g. "Sarah the Sales Rep").
        role: Functional role description (e.g. "Senior Sales Representative").
        description: Narrative description of personality and behavior traits.
        industry: Target industry vertical (e.g. "SaaS", "Healthcare").
    """

    name: str = ""
    role: str = ""
    description: str = ""
    industry: str = ""

    def _validate(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Persona name cannot be empty")
        if not self.role or not self.role.strip():
            raise ValueError("Persona role cannot be empty")
