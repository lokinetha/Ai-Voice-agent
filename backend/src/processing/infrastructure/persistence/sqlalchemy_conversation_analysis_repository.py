"""
SQLAlchemy 2.x Repository Implementation for ConversationAnalysis Aggregate Root.
"""

from __future__ import annotations

from datetime import UTC

from processing.domain.entities.behavioral_signal import BehavioralSignal
from processing.domain.entities.conversation_analysis import (
    ConversationAnalysis,
)
from processing.domain.entities.conversation_pattern import ConversationPattern
from processing.domain.repositories.conversation_analysis_repository import (
    ConversationAnalysisRepository,
)
from processing.domain.value_objects.analysis_result import AnalysisResult
from processing.domain.value_objects.analysis_status import (
    AnalysisStatus,
    AnalysisStatusType,
)
from processing.domain.value_objects.behavioral_category import (
    BehavioralCategory,
    CategoryType,
)
from processing.domain.value_objects.confidence_score import ConfidenceScore
from processing.infrastructure.persistence.models import (
    BehavioralSignalModel,
    ConversationAnalysisModel,
    ConversationPatternModel,
)
from shared.kernel.specification import Specification
from shared.kernel.value_objects import (
    ConversationId,
    EntityId,
    Timestamp,
    WorkspaceId,
)
from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyConversationAnalysisRepository(ConversationAnalysisRepository):
    """SQLAlchemy implementation of ConversationAnalysisRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: EntityId) -> ConversationAnalysis | None:
        """Retrieve ConversationAnalysis aggregate by ID."""
        stmt = select(ConversationAnalysisModel).where(
            ConversationAnalysisModel.id == str(id.value)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_aggregate(model)

    async def find_by_workspace(self, workspace_id: WorkspaceId) -> list[ConversationAnalysis]:
        """Find all ConversationAnalysis records in target Workspace."""
        stmt = select(ConversationAnalysisModel).where(
            ConversationAnalysisModel.workspace_id == str(workspace_id.value)
        )
        result = await self._session.execute(stmt)
        return [self._to_aggregate(m) for m in result.scalars().all()]

    async def find_by_conversation(self, conversation_id: ConversationId) -> list[ConversationAnalysis]:
        """Find all ConversationAnalysis records for a target Conversation."""
        stmt = select(ConversationAnalysisModel).where(
            ConversationAnalysisModel.conversation_id == str(conversation_id.value)
        )
        result = await self._session.execute(stmt)
        return [self._to_aggregate(m) for m in result.scalars().all()]

    async def save(self, aggregate: ConversationAnalysis) -> None:
        """Persist or update ConversationAnalysis aggregate root."""
        stmt = select(ConversationAnalysisModel).where(
            ConversationAnalysisModel.id == str(aggregate.id.value)
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            model = self._to_model(aggregate)
            self._session.add(model)
        else:
            existing.status = aggregate.status.value.value
            existing.error_message = aggregate.error_message
            existing.version = aggregate.version
            if aggregate.result is not None:
                existing.result_json = {
                    "signals_count": aggregate.result.signals_count,
                    "patterns_count": aggregate.result.patterns_count,
                    "execution_time_seconds": aggregate.result.execution_time_seconds,
                    "summary": aggregate.result.summary,
                    "metadata": aggregate.result.metadata,
                }

    async def delete(self, aggregate: ConversationAnalysis) -> None:
        """Delete ConversationAnalysis aggregate from persistence."""
        stmt = sql_delete(ConversationAnalysisModel).where(
            ConversationAnalysisModel.id == str(aggregate.id.value)
        )
        await self._session.execute(stmt)

    async def find(self, spec: Specification[ConversationAnalysis]) -> list[ConversationAnalysis]:
        """Find ConversationAnalysis aggregates satisfying specification filter."""
        stmt = select(ConversationAnalysisModel)
        result = await self._session.execute(stmt)
        aggregates = [self._to_aggregate(m) for m in result.scalars().all()]
        return [a for a in aggregates if spec.is_satisfied_by(a)]

    async def count(self, spec: Specification[ConversationAnalysis]) -> int:
        """Count ConversationAnalysis aggregates satisfying specification filter."""
        return len(await self.find(spec))

    def _to_model(self, aggregate: ConversationAnalysis) -> ConversationAnalysisModel:
        """Map domain ConversationAnalysis to ORM ConversationAnalysisModel."""
        res_json = None
        if aggregate.result is not None:
            res_json = {
                "signals_count": aggregate.result.signals_count,
                "patterns_count": aggregate.result.patterns_count,
                "execution_time_seconds": aggregate.result.execution_time_seconds,
                "summary": aggregate.result.summary,
                "metadata": aggregate.result.metadata,
            }

        signal_models = [
            BehavioralSignalModel(
                id=str(s.id.value),
                analysis_id=str(aggregate.id.value),
                category=s.category.category.value,
                signal_type=s.signal_type,
                description=s.description,
                confidence=s.confidence.value,
                source_message_id=s.source_message_id,
                evidence_text=s.evidence_text,
                created_at=s.created_at.value,
            )
            for s in aggregate.signals
        ]

        pattern_models = [
            ConversationPatternModel(
                id=str(p.id.value),
                analysis_id=str(aggregate.id.value),
                pattern_name=p.pattern_name,
                category=p.category.category.value,
                description=p.description,
                frequency=p.frequency,
                confidence=p.confidence.value,
                sample_signal_ids_json=list(p.sample_signal_ids),
                conversation_references_json=list(p.conversation_references),
                created_at=p.created_at.value,
            )
            for p in aggregate.patterns
        ]

        return ConversationAnalysisModel(
            id=str(aggregate.id.value),
            workspace_id=str(aggregate.workspace_id.value),
            conversation_id=str(aggregate.conversation_id.value),
            status=aggregate.status.value.value,
            error_message=aggregate.error_message,
            result_json=res_json,
            version=aggregate.version,
            created_at=aggregate.created_at.value,
            signals=signal_models,
            patterns=pattern_models,
        )

    @staticmethod
    def _to_aggregate(model: ConversationAnalysisModel) -> ConversationAnalysis:
        """Map ORM ConversationAnalysisModel to domain ConversationAnalysis aggregate root."""
        created_at_dt = model.created_at
        if created_at_dt and created_at_dt.tzinfo is None:
            created_at_dt = created_at_dt.replace(tzinfo=UTC)

        res_vo = None
        if model.result_json:
            res_vo = AnalysisResult(
                signals_count=model.result_json.get("signals_count", 0),
                patterns_count=model.result_json.get("patterns_count", 0),
                execution_time_seconds=model.result_json.get("execution_time_seconds", 0.0),
                summary=model.result_json.get("summary", ""),
                metadata=model.result_json.get("metadata", {}),
            )

        signals = []
        for s in model.signals:
            s_created = s.created_at
            if s_created and s_created.tzinfo is None:
                s_created = s_created.replace(tzinfo=UTC)
            signals.append(
                BehavioralSignal(
                    id=EntityId(s.id),
                    category=BehavioralCategory(CategoryType(s.category)),
                    signal_type=s.signal_type,
                    description=s.description,
                    confidence=ConfidenceScore(s.confidence),
                    source_message_id=s.source_message_id,
                    evidence_text=s.evidence_text,
                    created_at=Timestamp(s_created),
                )
            )

        patterns = []
        for p in model.patterns:
            p_created = p.created_at
            if p_created and p_created.tzinfo is None:
                p_created = p_created.replace(tzinfo=UTC)
            patterns.append(
                ConversationPattern(
                    id=EntityId(p.id),
                    pattern_name=p.pattern_name,
                    category=BehavioralCategory(CategoryType(p.category)),
                    description=p.description,
                    frequency=p.frequency,
                    confidence=ConfidenceScore(p.confidence),
                    sample_signal_ids=tuple(p.sample_signal_ids_json or []),
                    conversation_references=tuple(p.conversation_references_json or []),
                    created_at=Timestamp(p_created),
                )
            )

        return ConversationAnalysis(
            id=EntityId(model.id),
            workspace_id=WorkspaceId(model.workspace_id),
            conversation_id=ConversationId(model.conversation_id),
            status=AnalysisStatus(AnalysisStatusType(model.status)),
            signals=signals,
            patterns=patterns,
            result=res_vo,
            error_message=model.error_message,
            created_at=Timestamp(created_at_dt),
            version=model.version,
        )
