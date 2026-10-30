"""
Identity Domain Events package init.
"""

from identity.domain.events.user_registered import UserRegistered
from identity.domain.events.user_role_changed import UserRoleChanged

__all__ = ["UserRegistered", "UserRoleChanged"]
