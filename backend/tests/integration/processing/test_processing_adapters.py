"""
Integration tests for Processing Infrastructure Adapters.
"""

from __future__ import annotations

import asyncio
import unittest

from processing.domain.value_objects.chunking_strategy import ChunkingStrategy
from processing.domain.value_objects.embedding_strategy import EmbeddingStrategy
from processing.infrastructure.adapters.chunking_adapter import ChunkingAdapter
from processing.infrastructure.adapters.docx_parser_adapter import (
    DOCXParserAdapter,
)
from processing.infrastructure.adapters.embedding_adapter import EmbeddingAdapter
from processing.infrastructure.adapters.object_storage_adapter import (
    ObjectStorageAdapter,
)
from processing.infrastructure.adapters.ocr_adapter import OCRAdapter
from processing.infrastructure.adapters.pdf_parser_adapter import PDFParserAdapter
from processing.infrastructure.adapters.vector_store_adapter import (
    VectorStoreAdapter,
)


class TestProcessingAdapters(unittest.TestCase):
    """Integration tests verifying behavior of all 7 Processing infrastructure adapters."""

    def test_pdf_parser_adapter(self) -> None:
        async def run() -> None:
            adapter = PDFParserAdapter()
            text = await adapter.parse_document(b"(Hello PDF World)", "pdf")
            self.assertIn("Hello PDF World", text)

        asyncio.run(run())

    def test_docx_parser_adapter(self) -> None:
        async def run() -> None:
            adapter = DOCXParserAdapter()
            text = await adapter.parse_document(
                b"<w:t>Hello DOCX World</w:t>", "docx"
            )
            self.assertIn("Hello DOCX World", text)

        asyncio.run(run())

    def test_ocr_adapter(self) -> None:
        async def run() -> None:
            adapter = OCRAdapter()
            text = await adapter.extract_text_from_image(b"Sample OCR Image Content")
            self.assertTrue(len(text) > 0)

        asyncio.run(run())

    def test_chunking_adapter(self) -> None:
        async def run() -> None:
            adapter = ChunkingAdapter()
            strategy = ChunkingStrategy(chunk_size=50, chunk_overlap=10)
            text = "Alpha " * 30
            chunks = await adapter.chunk_text(text, strategy)
            self.assertGreater(len(chunks), 1)

        asyncio.run(run())

    def test_embedding_adapter(self) -> None:
        async def run() -> None:
            adapter = EmbeddingAdapter()
            strategy = EmbeddingStrategy(dimension=64)
            vectors = await adapter.generate_embeddings(
                ["chunk 1 text", "chunk 2 text"], strategy
            )
            self.assertEqual(len(vectors), 2)
            self.assertEqual(len(vectors[0]), 64)

        asyncio.run(run())

    def test_vector_store_adapter(self) -> None:
        async def run() -> None:
            adapter = VectorStoreAdapter()
            refs = await adapter.store_vectors(
                collection_name="col-1",
                vectors=[[0.1] * 64, [0.2] * 64],
                payloads=[{"idx": 1}, {"idx": 2}],
            )
            self.assertEqual(len(refs), 2)
            self.assertTrue(refs[0].startswith("vec-"))

        asyncio.run(run())

    def test_object_storage_adapter(self) -> None:
        async def run() -> None:
            adapter = ObjectStorageAdapter()
            uri = await adapter.store_object("b1", "k1", b"Data payload")
            self.assertEqual(uri, "storage://b1/k1")

            fetched = await adapter.fetch_object("b1", "k1")
            self.assertEqual(fetched, b"Data payload")

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
