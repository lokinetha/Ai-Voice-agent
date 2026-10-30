"""
Integration tests for Identity Infrastructure security and persistence implementations.
"""

from __future__ import annotations

import unittest

from identity.domain.value_objects.password_hash import PasswordHash
from identity.infrastructure.security.jwt_service import JwtService
from identity.infrastructure.security.password_hasher import PBKDF2PasswordHasher


class TestIdentityInfrastructure(unittest.TestCase):
    def test_pbkdf2_password_hasher(self) -> None:
        hasher = PBKDF2PasswordHasher()
        hashed = hasher.hash("my_secret_password")
        self.assertTrue(hashed.startswith("pbkdf2_sha256$"))

        pw_hash = PasswordHash.create(hashed, algorithm="pbkdf2_sha256")

        # Verification success
        self.assertTrue(hasher.verify("my_secret_password", pw_hash))

        # Verification failure
        self.assertFalse(hasher.verify("wrong_password", pw_hash))

    def test_jwt_service_issue_and_verify(self) -> None:
        service = JwtService(secret_key="test-key-123", access_token_expire_minutes=15)
        access_token, refresh_token, expires_in = service.create_token_pair(
            user_id="usr-100", tenant_id="tenant-200", role="ADMIN"
        )

        self.assertIsNotNone(access_token)
        self.assertIsNotNone(refresh_token)
        self.assertEqual(expires_in, 900)

        # Verify refresh token
        refresh_payload = service.verify_refresh_token(refresh_token)
        self.assertEqual(refresh_payload["sub"], "usr-100")
        self.assertEqual(refresh_payload["tenant_id"], "tenant-200")
        self.assertEqual(refresh_payload["type"], "refresh")

        # Verify access token
        access_payload = service.verify_access_token(access_token)
        self.assertEqual(access_payload["sub"], "usr-100")
        self.assertEqual(access_payload["role"], "ADMIN")
        self.assertEqual(access_payload["type"], "access")


if __name__ == "__main__":
    unittest.main()
