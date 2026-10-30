"""
Knowledge Domain Entities package init.
"""

from knowledge.domain.entities.chunk import Chunk
from knowledge.domain.entities.document import Document
from knowledge.domain.entities.knowledge_base import KnowledgeBase

__all__ = ["KnowledgeBase", "Document", "Chunk"]
