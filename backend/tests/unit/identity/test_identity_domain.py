"""
Unit tests for Identity Domain Layer.
"""

import unittest

from identity.domain.entities.api_key import ApiKey
from identity.domain.events.user_registered import UserRegistered
from identity.domain.events.user_role_changed import UserRoleChanged
from identity.domain.factories.user_factory import UserFactory
from identity.domain.services.authentication_service import AuthenticationService
from identity.domain.value_objects.email import Email
from identity.domain.value_objects.password_hash import PasswordHash
from identity.domain.value_objects.user_role import RoleType, UserRole
from shared.kernel.value_objects import EntityId, TenantId, UserId


class DummyPasswordHasher:
    def verify(self, plain_password: str, password_hash: PasswordHash) -> bool:
        return plain_password == "secret123" and password_hash.hash_value == "hashed_secret123"


class TestIdentityDomain(unittest.TestCase):
    def test_user_factory_creation(self):
        email = Email("admin@enterprise.com")
        pw_hash = PasswordHash.create("hashed_secret123")
        tenant_id = TenantId("tenant-100")

        user = UserFactory.create(
            email=email,
            password_hash=pw_hash,
            tenant_id=tenant_id,
            role=UserRole.admin(),
        )

        self.assertIsInstance(user.id, UserId)
        self.assertEqual(user.email, email)
        self.assertEqual(user.role.value, RoleType.ADMIN)
        self.assertEqual(user.tenant_id, tenant_id)

        # Check recorded domain event
        events = user.domain_events
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], UserRegistered)
        self.assertEqual(events[0].email, "admin@enterprise.com")

    def test_user_role_update_event(self):
        user = UserFactory.create(
            email=Email("user@enterprise.com"),
            password_hash=PasswordHash("hashed_secret123"),
            tenant_id=TenantId("tenant-1"),
        )
        user.clear_events()

        res = user.update_role(UserRole.owner())
        self.assertTrue(res.is_success)
        self.assertEqual(user.role.value, RoleType.OWNER)

        events = user.domain_events
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], UserRoleChanged)
        self.assertEqual(events[0].old_role, "MEMBER")
        self.assertEqual(events[0].new_role, "OWNER")

    def test_api_key_management(self):
        user = UserFactory.create(
            email=Email("keyholder@enterprise.com"),
            password_hash=PasswordHash("hashed"),
            tenant_id=TenantId("t1"),
        )

        key_id = EntityId("key-1")
        api_key = ApiKey(
            id=key_id,
            user_id=user.id,
            key_hash="hash_val",
            prefix="vf_live_123",
            scopes=["agents:read", "agents:write"],
        )

        res_add = user.add_api_key(api_key)
        self.assertTrue(res_add.is_success)
        self.assertEqual(len(user.api_keys), 1)

        # Duplicate key failure
        res_dup = user.add_api_key(api_key)
        self.assertTrue(res_dup.is_failure)

        # Revoke key
        res_rev = user.revoke_api_key(key_id)
        self.assertTrue(res_rev.is_success)
        self.assertEqual(len(user.api_keys), 0)

    def test_authentication_service(self):
        user = UserFactory.create(
            email=Email("auth@enterprise.com"),
            password_hash=PasswordHash("hashed_secret123"),
            tenant_id=TenantId("t1"),
        )

        service = AuthenticationService(password_hasher=DummyPasswordHasher())

        # Valid login
        res_valid = service.authenticate(user, "secret123")
        self.assertTrue(res_valid.is_success)
        self.assertIsNotNone(user.last_login)

        # Invalid login
        res_invalid = service.authenticate(user, "wrong_password")
        self.assertTrue(res_invalid.is_failure)
        self.assertEqual(res_invalid.error.code, "INVALID_CREDENTIALS")


if __name__ == "__main__":
    unittest.main()
