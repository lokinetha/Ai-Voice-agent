"""
DeterministicBehaviorAnalyzerAdapter implementing BehaviorAnalyzerPort.

Deterministic rule-based behavior analyzer detecting behavioral signals and
patterns for testing and production workflow without LLM dependency.
"""

from __future__ import annotations

import re
from typing import Any

from processing.domain.entities.behavioral_signal import BehavioralSignal
from processing.domain.entities.conversation_pattern import ConversationPattern
from processing.domain.ports.behavior_analyzer_port import BehaviorAnalyzerPort
from processing.domain.value_objects.behavioral_category import (
    BehavioralCategory,
)
from processing.domain.value_objects.confidence_score import ConfidenceScore
from shared.kernel.value_objects import EntityId


class DeterministicBehaviorAnalyzerAdapter(BehaviorAnalyzerPort):
    """Deterministic rule-based behavior analyzer."""

    async def analyze_messages(
        self, messages: list[dict[str, Any]], conversation_id: str = ""
    ) -> tuple[list[BehavioralSignal], list[ConversationPattern]]:
        """Analyze message turns using rule-based pattern matching.

        Rules enforced:
        - Every signal includes confidence score and source message ID traceability.
        - Preserves traceability from patterns to signal IDs and conversation ID.

        Args:
            messages: List of message dictionaries.
            conversation_id: ID of the conversation.

        Returns:
            Tuple of (detected_signals, detected_patterns).
        """
        signals: list[BehavioralSignal] = []
        signals_by_category: dict[BehavioralCategory, list[str]] = {}

        rules = [
            (
                r"\b(expensive|cost|price|budget|too high|discount)\b",
                BehavioralCategory.objection_handling(),
                "PRICE_OBJECTION",
                "Price or budget objection expressed",
                0.90,
            ),
            (
                r"\b(how|what|why|tell me|explain|can you|details)\b",
                BehavioralCategory.discovery_question(),
                "DISCOVERY_QUESTION",
                "Discovery question asked to uncover needs",
                0.85,
            ),
            (
                r"\b(sign|buy|order|ready|proceed|deal|contract|start)\b",
                BehavioralCategory.closing_technique(),
                "CLOSING_SIGNAL",
                "Closing or deal commitment signal",
                0.88,
            ),
            (
                r"\b(understand|sorry|help|support|appreciate|hear you)\b",
                BehavioralCategory.empathy_building(),
                "EMPATHY_EXPRESSION",
                "Empathy or rapport building phrase",
                0.80,
            ),
            (
                r"\b(terms|privacy|policy|security|gdpr|compliance)\b",
                BehavioralCategory.compliance_rule(),
                "COMPLIANCE_CHECK",
                "Compliance or policy reference",
                0.95,
            ),
        ]

        for msg in messages:
            msg_id = str(msg.get("id", "msg-unknown"))
            content = str(msg.get("content", ""))

            for pattern_regex, category, signal_type, desc, conf in rules:
                if re.search(pattern_regex, content, re.IGNORECASE):
                    sig_id = EntityId()
                    signal = BehavioralSignal(
                        id=sig_id,
                        category=category,
                        signal_type=signal_type,
                        description=desc,
                        confidence=ConfidenceScore(conf),
                        source_message_id=msg_id,
                        evidence_text=content[:200],
                    )
                    signals.append(signal)

                    if category not in signals_by_category:
                        signals_by_category[category] = []
                    signals_by_category[category].append(str(sig_id.value))

        patterns: list[ConversationPattern] = []
        for category_vo, sig_ids in signals_by_category.items():
            if len(sig_ids) >= 1:
                cat_name = category_vo.category.value
                pattern = ConversationPattern(
                    id=EntityId(),
                    pattern_name=f"Recurrent {cat_name} Pattern",
                    category=category_vo,
                    description=f"Detected {len(sig_ids)} occurrences of {cat_name} behaviors",
                    frequency=len(sig_ids),
                    confidence=ConfidenceScore(0.85),
                    sample_signal_ids=tuple(sig_ids),
                    conversation_references=(conversation_id,) if conversation_id else (),
                )
                patterns.append(pattern)

        return signals, patterns
