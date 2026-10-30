"""
FakeTelephonyAdapter implementing TelephonyPort.

Provider-independent fake Telephony adapter.
"""

from __future__ import annotations

import uuid

from voice.domain.ports.telephony_port import TelephonyPort


class FakeTelephonyAdapter(TelephonyPort):
    """Fake Telephony connection adapter."""

    def __init__(self) -> None:
        self.active_calls: set[str] = set()

    async def initiate_call(self, to_number: str, from_number: str) -> str:
        """Initiate fake phone call and return call connection ID."""
        connection_id = f"call-{uuid.uuid4()}"
        self.active_calls.add(connection_id)
        return connection_id

    async def terminate_call(self, connection_id: str) -> bool:
        """Terminate fake phone call connection."""
        if connection_id in self.active_calls:
            self.active_calls.remove(connection_id)
            return True
        return True
