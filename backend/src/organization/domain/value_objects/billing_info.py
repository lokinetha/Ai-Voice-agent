"""
BillingInfo Value Object for Organization Bounded Context.

Encapsulates organization billing details and subscription status.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.value_object import ValueObject
from shared.kernel.value_objects import Email


@dataclass(frozen=True)
class BillingInfo(ValueObject):
    """BillingInfo Value Object."""

    billing_email: Email
    stripe_customer_id: str | None = None
    subscription_status: str = "active"

    def _validate(self) -> None:
        if not self.subscription_status or not isinstance(self.subscription_status, str):
            raise ValueError("subscription_status cannot be empty")
