"""
Password Hasher Implementation for Identity Infrastructure Layer.

Implements PasswordHasherPort interface using PBKDF2 with SHA-256 and salt.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os

from identity.domain.services.authentication_service import PasswordHasherPort
from identity.domain.value_objects.password_hash import PasswordHash


class PBKDF2PasswordHasher(PasswordHasherPort):
    """Production-grade PasswordHasher using PBKDF2-HMAC-SHA256."""

    ITERATIONS: int = 100_000
    ALGORITHM: str = "pbkdf2_sha256"

    def hash(self, plain_password: str) -> str:
        """Hash plain text password with random 16-byte salt.

        Returns:
            Formatted hash string: 'pbkdf2_sha256$iterations$salt_b64$hash_b64'
        """
        if not plain_password:
            raise ValueError("Password string cannot be empty")

        salt = os.urandom(16)
        derived_key = hashlib.pbkdf2_hmac(
            "sha256", plain_password.encode("utf-8"), salt, self.ITERATIONS
        )
        salt_b64 = base64.b64encode(salt).decode("ascii")
        hash_b64 = base64.b64encode(derived_key).decode("ascii")
        return f"{self.ALGORITHM}${self.ITERATIONS}${salt_b64}${hash_b64}"

    def verify(self, plain_password: str, password_hash: PasswordHash) -> bool:
        """Verify plain text password against stored PasswordHash.

        Args:
            plain_password: Plain text password string.
            password_hash: PasswordHash domain value object.

        Returns:
            True if verification succeeds, False otherwise.
        """
        if not plain_password or not password_hash.hash_value:
            return False

        try:
            parts = password_hash.hash_value.split("$")
            if len(parts) != 4 or parts[0] != self.ALGORITHM:
                return False

            iterations = int(parts[1])
            salt = base64.b64decode(parts[2].encode("ascii"))
            expected_hash = base64.b64decode(parts[3].encode("ascii"))

            derived_key = hashlib.pbkdf2_hmac(
                "sha256", plain_password.encode("utf-8"), salt, iterations
            )
            return hmac.compare_digest(derived_key, expected_hash)
        except Exception:
            return False
