"""
Integration tests for ConversationAnalysis Infrastructure Adapters.
"""

from __future__ import annotations

import asyncio
import unittest

from processing.infrastructure.adapters.deterministic_behavior_analyzer_adapter import (
    DeterministicBehaviorAnalyzerAdapter,
)


class TestConversationAnalysisAdapters(unittest.TestCase):
    """Integration tests verifying behavior of ConversationAnalysis infrastructure adapters."""

    def test_deterministic_behavior_analyzer(self) -> None:
        async def run() -> None:
            analyzer = DeterministicBehaviorAnalyzerAdapter()
            messages = [
                {"id": "msg-10", "role": "CUSTOMER", "content": "What is the price of this plan?"},
                {"id": "msg-11", "role": "CUSTOMER", "content": "It is too expensive for our budget."},
                {"id": "msg-12", "role": "AGENT", "content": "I understand your concern, let me check options."},
                {"id": "msg-13", "role": "CUSTOMER", "content": "Okay, we are ready to sign the contract."},
            ]

            signals, patterns = await analyzer.analyze_messages(messages, conversation_id="conv-test")

            self.assertGreaterEqual(len(signals), 4)
            self.assertGreater(len(patterns), 0)

            # Enforce rule: Every signal must include a confidence score and source_message_id
            for sig in signals:
                self.assertTrue(0.0 <= sig.confidence.value <= 1.0)
                self.assertTrue(len(sig.source_message_id) > 0)
                self.assertTrue(sig.source_message_id.startswith("msg-"))

            # Enforce rule: Traceability from pattern back to signal IDs & conversation reference
            for pat in patterns:
                self.assertGreater(len(pat.sample_signal_ids), 0)
                self.assertIn("conv-test", pat.conversation_references)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
