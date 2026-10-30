"""
Integration tests for Voice Infrastructure Fake Adapters.
"""

from __future__ import annotations

import asyncio
import unittest

from voice.domain.value_objects.audio_chunk import AudioChunk
from voice.domain.value_objects.audio_format import AudioFormat
from voice.infrastructure.adapters.fake_audio_stream_adapter import (
    FakeAudioStreamAdapter,
)
from voice.infrastructure.adapters.fake_llm_runtime_adapter import (
    FakeLLMRuntimeAdapter,
)
from voice.infrastructure.adapters.fake_stt_adapter import FakeSTTAdapter
from voice.infrastructure.adapters.fake_telephony_adapter import (
    FakeTelephonyAdapter,
)
from voice.infrastructure.adapters.fake_tts_adapter import FakeTTSAdapter


class TestVoiceAdapters(unittest.TestCase):
    """Integration tests verifying behavior of all Voice fake adapters."""

    def test_fake_stt_adapter(self) -> None:
        async def run() -> None:
            adapter = FakeSTTAdapter()
            chunk = AudioChunk(payload=b"Hello test audio", sequence_number=1)
            fmt = AudioFormat(sample_rate=16000)

            transcript, conf = await adapter.transcribe_audio_chunk(chunk, fmt)
            self.assertEqual(transcript, "Hello test audio")
            self.assertEqual(conf, 0.95)

        asyncio.run(run())

    def test_fake_tts_adapter(self) -> None:
        async def run() -> None:
            adapter = FakeTTSAdapter()
            fmt = AudioFormat(sample_rate=24000)
            audio = await adapter.synthesize_speech("Sample response text", "agent_voice_1", fmt)
            self.assertTrue(len(audio) > 0)
            self.assertIn(b"Sample response text", audio)

        asyncio.run(run())

    def test_fake_telephony_adapter(self) -> None:
        async def run() -> None:
            adapter = FakeTelephonyAdapter()
            conn_id = await adapter.initiate_call("+1234567890", "+0987654321")
            self.assertTrue(conn_id.startswith("call-"))
            self.assertIn(conn_id, adapter.active_calls)

            term_res = await adapter.terminate_call(conn_id)
            self.assertTrue(term_res)
            self.assertNotIn(conn_id, adapter.active_calls)

        asyncio.run(run())

    def test_fake_audio_stream_adapter(self) -> None:
        async def run() -> None:
            adapter = FakeAudioStreamAdapter()
            chunk1 = AudioChunk(payload=b"Frame 1", sequence_number=1)
            chunk2 = AudioChunk(payload=b"Frame 2", sequence_number=2)

            await adapter.send_audio_chunk("stream-1", chunk1)
            await adapter.send_audio_chunk("stream-1", chunk2)

            recv1 = await adapter.receive_audio_chunk("stream-1")
            recv2 = await adapter.receive_audio_chunk("stream-1")
            recv3 = await adapter.receive_audio_chunk("stream-1")

            self.assertIsNotNone(recv1)
            self.assertIsNotNone(recv2)
            self.assertIsNone(recv3)
            self.assertEqual(recv1.sequence_number, 1)

        asyncio.run(run())

    def test_fake_llm_runtime_adapter(self) -> None:
        async def run() -> None:
            adapter = FakeLLMRuntimeAdapter()
            resp = await adapter.generate_response("ws-1", "ag-1", "conv-1", "What is the cost?")
            self.assertIn("pricing", resp)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
