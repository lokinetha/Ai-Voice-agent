"""
ConversationAnalysisMapper for mapping between Domain aggregate and DTOs.
"""

from __future__ import annotations

from processing.application.dto.conversation_analysis_dto import (
    AnalysisResultDTO,
    BehavioralSignalDTO,
    ConversationAnalysisDTO,
    ConversationPatternDTO,
)
from processing.domain.entities.behavioral_signal import BehavioralSignal
from processing.domain.entities.conversation_analysis import (
    ConversationAnalysis,
)
from processing.domain.entities.conversation_pattern import ConversationPattern


class ConversationAnalysisMapper:
    """Static mapper converting ConversationAnalysis domain entities to DTOs."""

    @staticmethod
    def to_dto(analysis: ConversationAnalysis) -> ConversationAnalysisDTO:
        """Map ConversationAnalysis aggregate root to ConversationAnalysisDTO."""
        res_dto = None
        if analysis.result is not None:
            res_dto = AnalysisResultDTO(
                signals_count=analysis.result.signals_count,
                patterns_count=analysis.result.patterns_count,
                execution_time_seconds=analysis.result.execution_time_seconds,
                summary=analysis.result.summary,
                metadata=analysis.result.metadata,
            )

        sig_dtos = tuple(ConversationAnalysisMapper.to_signal_dto(s) for s in analysis.signals)
        pat_dtos = tuple(ConversationAnalysisMapper.to_pattern_dto(p) for p in analysis.patterns)

        return ConversationAnalysisDTO(
            id=str(analysis.id.value),
            workspace_id=str(analysis.workspace_id.value),
            conversation_id=str(analysis.conversation_id.value),
            status=analysis.status.value.value,
            signals=sig_dtos,
            patterns=pat_dtos,
            result=res_dto,
            error_message=analysis.error_message,
            version=analysis.version,
            created_at=analysis.created_at.value,
        )

    @staticmethod
    def to_signal_dto(signal: BehavioralSignal) -> BehavioralSignalDTO:
        """Map BehavioralSignal entity to BehavioralSignalDTO."""
        return BehavioralSignalDTO(
            id=str(signal.id.value),
            category=signal.category.category.value,
            signal_type=signal.signal_type,
            description=signal.description,
            confidence=signal.confidence.value,
            source_message_id=signal.source_message_id,
            evidence_text=signal.evidence_text,
        )

    @staticmethod
    def to_pattern_dto(pattern: ConversationPattern) -> ConversationPatternDTO:
        """Map ConversationPattern entity to ConversationPatternDTO."""
        return ConversationPatternDTO(
            id=str(pattern.id.value),
            pattern_name=pattern.pattern_name,
            category=pattern.category.category.value,
            description=pattern.description,
            frequency=pattern.frequency,
            confidence=pattern.confidence.value,
            sample_signal_ids=pattern.sample_signal_ids,
            conversation_references=pattern.conversation_references,
        )
