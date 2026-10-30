"""
SQLAlchemy 2.x Repository Implementation for Conversation Aggregate Root.
"""

from __future__ import annotations

from datetime import UTC

from shared.kernel.specification import Specification
from shared.kernel.value_objects import (
    AgentId,
    ConversationId,
    EntityId,
    MessageId,
    Timestamp,
    WorkspaceId,
)
from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from conversation.domain.entities.conversation import Conversation
from conversation.domain.entities.conversation_memory import ConversationMemory
from conversation.domain.entities.conversation_timeline import (
    ConversationTimeline,
)
from conversation.domain.entities.message import Message
from conversation.domain.entities.participant import Participant
from conversation.domain.repositories.conversation_repository import (
    ConversationRepository,
)
from conversation.domain.value_objects.conversation_channel import (
    ChannelType,
    ConversationChannel,
)
from conversation.domain.value_objects.conversation_language import (
    ConversationLanguage,
)
from conversation.domain.value_objects.conversation_metrics import (
    ConversationMetrics,
)
from conversation.domain.value_objects.conversation_status import (
    ConversationStatus,
    ConversationStatusType,
)
from conversation.domain.value_objects.conversation_summary import (
    ConversationSummary,
)
from conversation.domain.value_objects.participant_role import (
    ParticipantRole,
    RoleCategory,
)
from conversation.infrastructure.persistence.models import (
    ConversationModel,
    MessageModel,
    ParticipantModel,
)


class SqlAlchemyConversationRepository(ConversationRepository):
    """SQLAlchemy implementation of ConversationRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: ConversationId) -> Conversation | None:
        """Retrieve Conversation aggregate by ID."""
        stmt = select(ConversationModel).where(ConversationModel.id == str(id.value))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_aggregate(model)

    async def find_by_workspace(self, workspace_id: WorkspaceId) -> list[Conversation]:
        """Find all Conversations in target Workspace."""
        stmt = select(ConversationModel).where(
            ConversationModel.workspace_id == str(workspace_id.value)
        )
        result = await self._session.execute(stmt)
        return [self._to_aggregate(m) for m in result.scalars().all()]

    async def find_by_agent(self, agent_id: AgentId) -> list[Conversation]:
        """Find all Conversations handled by target Agent."""
        stmt = select(ConversationModel).where(
            ConversationModel.agent_id == str(agent_id.value)
        )
        result = await self._session.execute(stmt)
        return [self._to_aggregate(m) for m in result.scalars().all()]

    async def save(self, aggregate: Conversation) -> None:
        """Persist or update Conversation aggregate root."""
        stmt = select(ConversationModel).where(
            ConversationModel.id == str(aggregate.id.value)
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            model = self._to_model(aggregate)
            self._session.add(model)
        else:
            existing.status = aggregate.status.value.value
            existing.duration_seconds = aggregate.metrics.duration_seconds
            existing.total_messages = aggregate.metrics.total_messages
            existing.agent_messages = aggregate.metrics.agent_messages
            existing.customer_messages = aggregate.metrics.customer_messages
            existing.turn_count = aggregate.metrics.turn_count
            existing.version = aggregate.version

            if aggregate.summary is not None:
                existing.summary_text = aggregate.summary.text
                existing.summary_topics = list(aggregate.summary.key_topics)
                existing.summary_sentiment = aggregate.summary.sentiment
                existing.summary_actions = list(aggregate.summary.action_items)

    async def delete(self, aggregate: Conversation) -> None:
        """Delete Conversation aggregate from persistence."""
        stmt = sql_delete(ConversationModel).where(
            ConversationModel.id == str(aggregate.id.value)
        )
        await self._session.execute(stmt)

    async def find(self, spec: Specification[Conversation]) -> list[Conversation]:
        """Find Conversation aggregates satisfying specification filter."""
        stmt = select(ConversationModel)
        result = await self._session.execute(stmt)
        aggregates = [self._to_aggregate(m) for m in result.scalars().all()]
        return [a for a in aggregates if spec.is_satisfied_by(a)]

    async def count(self, spec: Specification[Conversation]) -> int:
        """Count Conversation aggregates satisfying specification filter."""
        return len(await self.find(spec))

    def _to_model(self, aggregate: Conversation) -> ConversationModel:
        """Map domain Conversation to ORM ConversationModel."""
        summary_text = aggregate.summary.text if aggregate.summary else None
        summary_topics = list(aggregate.summary.key_topics) if aggregate.summary else None
        summary_sentiment = aggregate.summary.sentiment if aggregate.summary else None
        summary_actions = list(aggregate.summary.action_items) if aggregate.summary else None

        return ConversationModel(
            id=str(aggregate.id.value),
            workspace_id=str(aggregate.workspace_id.value),
            agent_id=str(aggregate.agent_id.value),
            channel=aggregate.channel.value.value,
            language=aggregate.language.code,
            status=aggregate.status.value.value,
            duration_seconds=aggregate.metrics.duration_seconds,
            total_messages=aggregate.metrics.total_messages,
            agent_messages=aggregate.metrics.agent_messages,
            customer_messages=aggregate.metrics.customer_messages,
            turn_count=aggregate.metrics.turn_count,
            summary_text=summary_text,
            summary_topics=summary_topics,
            summary_sentiment=summary_sentiment,
            summary_actions=summary_actions,
            version=aggregate.version,
            created_at=aggregate.created_at.value,
            participants=[
                ParticipantModel(
                    id=str(p.id.value),
                    conversation_id=str(aggregate.id.value),
                    name=p.name,
                    role=p.role.value.value,
                    external_id=p.external_id,
                    is_active=p.is_active,
                    created_at=p.created_at.value,
                )
                for p in aggregate.participants
            ],
            messages=[
                MessageModel(
                    id=str(m.id.value),
                    conversation_id=str(aggregate.id.value),
                    participant_id=str(m.participant_id.value),
                    role=m.role.value.value,
                    content=m.content,
                    sequence_number=m.sequence_number,
                    metadata_json=m.metadata,
                    created_at=m.created_at.value,
                )
                for m in aggregate.messages
            ],
        )

    @staticmethod
    def _to_aggregate(model: ConversationModel) -> Conversation:
        """Map ORM ConversationModel to domain Conversation aggregate root."""
        created_at_dt = model.created_at
        if created_at_dt and created_at_dt.tzinfo is None:
            created_at_dt = created_at_dt.replace(tzinfo=UTC)

        participants = []
        for p in model.participants:
            p_created = p.created_at
            if p_created and p_created.tzinfo is None:
                p_created = p_created.replace(tzinfo=UTC)
            participants.append(
                Participant(
                    id=EntityId(p.id),
                    name=p.name,
                    role=ParticipantRole(RoleCategory(p.role)),
                    external_id=p.external_id,
                    is_active=p.is_active,
                    created_at=Timestamp(p_created),
                )
            )

        messages = []
        for m in model.messages:
            m_created = m.created_at
            if m_created and m_created.tzinfo is None:
                m_created = m_created.replace(tzinfo=UTC)
            messages.append(
                Message(
                    id=MessageId(m.id),
                    participant_id=EntityId(m.participant_id),
                    role=ParticipantRole(RoleCategory(m.role)),
                    content=m.content,
                    sequence_number=m.sequence_number,
                    metadata=m.metadata_json,
                    created_at=Timestamp(m_created),
                )
            )

        metrics = ConversationMetrics(
            duration_seconds=model.duration_seconds,
            total_messages=model.total_messages,
            agent_messages=model.agent_messages,
            customer_messages=model.customer_messages,
            turn_count=model.turn_count,
        )

        summary = None
        if model.summary_text is not None:
            summary = ConversationSummary(
                text=model.summary_text,
                key_topics=tuple(model.summary_topics) if model.summary_topics else (),
                sentiment=model.summary_sentiment or "neutral",
                action_items=tuple(model.summary_actions) if model.summary_actions else (),
            )

        memory = ConversationMemory(id=EntityId())
        timeline = ConversationTimeline(id=EntityId())

        return Conversation(
            id=ConversationId(model.id),
            workspace_id=WorkspaceId(model.workspace_id),
            agent_id=AgentId(model.agent_id),
            channel=ConversationChannel(ChannelType(model.channel)),
            language=ConversationLanguage(code=model.language),
            status=ConversationStatus(ConversationStatusType(model.status)),
            summary=summary,
            metrics=metrics,
            participants=participants,
            messages=messages,
            memory=memory,
            timeline=timeline,
            created_at=Timestamp(created_at_dt),
            version=model.version,
        )
