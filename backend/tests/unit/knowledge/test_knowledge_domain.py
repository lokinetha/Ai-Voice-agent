"""
Unit tests for Knowledge Domain Layer and Aggregate Roots.
"""

from __future__ import annotations

import unittest

from knowledge.domain.entities.chunk import Chunk
from knowledge.domain.entities.document import Document
from knowledge.domain.events.document_deleted import DocumentDeleted
from knowledge.domain.events.document_uploaded import DocumentUploaded
from knowledge.domain.events.knowledge_base_created import KnowledgeBaseCreated
from knowledge.domain.events.knowledge_base_reindexed import (
    KnowledgeBaseReindexed,
)
from knowledge.domain.factories.knowledge_base_factory import KnowledgeBaseFactory
from knowledge.domain.services.knowledge_base_indexing_service import (
    KnowledgeBaseIndexingService,
)
from knowledge.domain.value_objects.document_metadata import DocumentMetadata
from knowledge.domain.value_objects.kb_status import KBStatusType
from shared.kernel.value_objects import DocumentId, EntityId, WorkspaceId


class TestKnowledgeDomain(unittest.TestCase):
    def test_knowledge_base_factory_creation(self) -> None:
        ws_id = WorkspaceId("ws-kb-1")
        kb = KnowledgeBaseFactory.create(
            workspace_id=ws_id,
            name="SOP Docs Base",
            description="Telesales procedure manuals",
        )

        self.assertEqual(kb.name, "SOP Docs Base")
        self.assertEqual(kb.workspace_id, ws_id)
        self.assertEqual(kb.status.value, KBStatusType.ACTIVE)
        self.assertEqual(kb.document_count, 0)
        self.assertEqual(kb.total_chunks, 0)

        events = kb.domain_events
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], KnowledgeBaseCreated)

    def test_document_and_chunk_management(self) -> None:
        kb = KnowledgeBaseFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="Doc Test KB",
        )
        kb.clear_events()

        doc_id = DocumentId("doc-100")
        meta = DocumentMetadata.create(
            file_type="pdf",
            size_bytes=2048,
            tags={"department": "sales"},
        )
        doc = Document(id=doc_id, file_name="sales_manual.pdf", metadata=meta)

        chunk1 = Chunk(id=EntityId(), text_content="Intro text", sequence_index=0, token_count=10)
        chunk2 = Chunk(id=EntityId(), text_content="Objection handling", sequence_index=1, token_count=15)
        doc.add_chunk(chunk1)
        doc.add_chunk(chunk2)

        add_res = kb.add_document(doc)
        self.assertTrue(add_res.is_success)
        self.assertEqual(kb.document_count, 1)
        self.assertEqual(kb.total_chunks, 2)

        events = kb.domain_events
        self.assertTrue(any(isinstance(e, DocumentUploaded) for e in events))

        # Remove document
        rem_res = kb.remove_document(doc_id)
        self.assertTrue(rem_res.is_success)
        self.assertEqual(kb.document_count, 0)

        events_after = kb.domain_events
        self.assertTrue(any(isinstance(e, DocumentDeleted) for e in events_after))

    def test_reindexing_service(self) -> None:
        svc = KnowledgeBaseIndexingService()
        kb = KnowledgeBaseFactory.create(workspace_id=WorkspaceId("w-1"), name="Reindex KB")

        res = svc.validate_and_reindex(kb)
        self.assertTrue(res.is_success)
        self.assertEqual(kb.status.value, KBStatusType.INDEXING)

        events = kb.domain_events
        self.assertTrue(any(isinstance(e, KnowledgeBaseReindexed) for e in events))


if __name__ == "__main__":
    unittest.main()
