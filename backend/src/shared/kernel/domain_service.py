"""
DomainService Marker Interface.

Domain Services encapsulate business logic that spans multiple aggregates or value objects,
or does not naturally fit within a single Aggregate boundary.
"""

from abc import ABC


class DomainService(ABC):
    """Marker abstract base class for all Domain Services in Clean Architecture."""

