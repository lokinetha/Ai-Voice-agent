"""
JwtService implementation for Infrastructure Security layer.

Handles encoding, decoding, signing, and verification of JSON Web Tokens.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from typing import Any

from shared.kernel.value_objects import TenantId, UserId


class JwtService:
    """Service providing JWT encoding and decoding capabilities using HMAC SHA-256."""

    def __init__(
        self,
        secret_key: str = "super-secret-production-jwt-key-replace-in-env",
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 60,
    ) -> None:
        if not secret_key or not isinstance(secret_key, str):
            raise ValueError("JWT secret_key cannot be empty")

        self._secret_key = secret_key
        self._algorithm = algorithm
        self._expire_minutes = access_token_expire_minutes

    def create_access_token(
        self,
        user_id: UserId,
        tenant_id: TenantId,
        role: str,
        expires_delta: timedelta | None = None,
        token_type: str = "access",
    ) -> str:
        """Generate a signed JWT token."""
        now = datetime.now(UTC)
        delta = expires_delta if expires_delta is not None else timedelta(minutes=self._expire_minutes)
        expire = now + delta

        payload = {
            "sub": str(user_id.value),
            "tenant_id": str(tenant_id.value),
            "role": role,
            "type": token_type,
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
        }

        return self._encode_token(payload)

    def create_token_pair(
        self, user_id: str, tenant_id: str, role: str
    ) -> tuple[str, str, int]:
        """Generate (access_token, refresh_token, expires_in_seconds) satisfying TokenServicePort."""
        access_token = self.create_access_token(
            user_id=UserId(user_id),
            tenant_id=TenantId(tenant_id),
            role=role,
            expires_delta=timedelta(minutes=self._expire_minutes),
            token_type="access",
        )
        refresh_token = self.create_access_token(
            user_id=UserId(user_id),
            tenant_id=TenantId(tenant_id),
            role=role,
            expires_delta=timedelta(days=7),
            token_type="refresh",
        )
        return access_token, refresh_token, self._expire_minutes * 60

    def verify_refresh_token(self, token: str) -> dict[str, str]:
        """Verify refresh token and return payload dictionary."""
        payload = self.decode_token(token)
        return {
            "sub": str(payload.get("sub", "")),
            "user_id": str(payload.get("sub", "")),
            "tenant_id": str(payload.get("tenant_id", "")),
            "role": str(payload.get("role", "")),
            "type": str(payload.get("type", "refresh")),
        }

    def verify_access_token(self, token: str) -> dict[str, str]:
        """Verify access token and return payload dictionary."""
        payload = self.decode_token(token)
        return {
            "sub": str(payload.get("sub", "")),
            "user_id": str(payload.get("sub", "")),
            "tenant_id": str(payload.get("tenant_id", "")),
            "role": str(payload.get("role", "")),
            "type": str(payload.get("type", "access")),
        }

    def decode_token(self, token: str) -> dict[str, Any]:
        """Decode and verify JWT signature and expiration."""
        return self._decode_token(token)

    def _encode_token(self, payload: dict[str, Any]) -> str:
        header = {"alg": self._algorithm, "typ": "JWT"}

        header_b64 = self._base64url_encode(json.dumps(header).encode())
        payload_b64 = self._base64url_encode(json.dumps(payload).encode())

        signing_input = f"{header_b64}.{payload_b64}".encode()
        signature = hmac.new(
            self._secret_key.encode(),
            signing_input,
            hashlib.sha256,
        ).digest()

        signature_b64 = self._base64url_encode(signature)
        return f"{header_b64}.{payload_b64}.{signature_b64}"

    def _decode_token(self, token: str) -> dict[str, Any]:
        try:
            parts = token.split(".")
            if len(parts) != 3:
                raise ValueError("Invalid JWT token format")

            h_b64, p_b64, sig_b64 = parts

            signing_input = f"{h_b64}.{p_b64}".encode()
            expected_sig = hmac.new(
                self._secret_key.encode(),
                signing_input,
                hashlib.sha256,
            ).digest()

            actual_sig = self._base64url_decode(sig_b64)

            if not hmac.compare_digest(expected_sig, actual_sig):
                raise ValueError("Invalid JWT signature")

            padded_payload = p_b64 + "=" * (-len(p_b64) % 4)
            payload_json = base64.urlsafe_b64decode(padded_payload.encode()).decode("utf-8")
            payload = json.loads(payload_json)

            exp = payload.get("exp")
            if exp and datetime.now(UTC).timestamp() > exp:
                raise ValueError("JWT token has expired")

            return payload
        except (KeyError, TypeError, json.JSONDecodeError) as err:
            raise ValueError(f"Failed to decode token: {err}") from err

    @staticmethod
    def _base64url_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

    @staticmethod
    def _base64url_decode(data_str: str) -> bytes:
        padded = data_str + "=" * (-len(data_str) % 4)
        return base64.urlsafe_b64decode(padded.encode())
