"""
TelephonyPort Interface for Voice Bounded Context.

Abstract port for telephony call control (SIP, WebRTC signaling, PSTN).
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class TelephonyPort(ABC):
    """Abstract port for Telephony connection management."""

    @abstractmethod
    async def initiate_call(self, to_number: str, from_number: str) -> str:
        """Initiate outbound phone call.

        Args:
            to_number: Recipient phone number.
            from_number: Sender phone number.

        Returns:
            Call connection ID reference.
        """
        ...

    @abstractmethod
    async def terminate_call(self, connection_id: str) -> bool:
        """Terminate active call connection.

        Args:
            connection_id: Call connection ID reference.

        Returns:
            True if successfully terminated.
        """
        ...
