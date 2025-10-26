"""
Integration test for basic knowledge workflows.
"""

import asyncio
import tempfile
from pathlib import Path

import pytest

from src.models.document import ProcessingStatus
from src.services.knowledge_service import KnowledgeService


@pytest.mark.integration
class TestKnowledgeWorkflows:
    """Integration tests for knowledge base workflows."""

    @pytest.mark.asyncio
    async def test_add_simple_text_document(self):
        """Test adding a simple text file as HTML."""
        # Create a temporary HTML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(
                """
            <html>
            <head><title>Test Document</title></head>
            <body>
                <h1>Sample Knowledge</h1>
                <p>This is a test document with some sample text.</p>
                <p>It contains multiple paragraphs to test chunking.</p>
            </body>
            </html>
            """
            )
            temp_file = Path(f.name)

        try:
            # Initialize service
            service = KnowledgeService()

            # Add document synchronously
            doc_id = await service.add_document(
                temp_file,
                metadata={"test": "integration"},
                async_processing=False,
            )

            # Verify document was added
            assert doc_id is not None

            # Get document
            document = service.get_document(doc_id)
            assert document is not None
            assert document.processing_status == ProcessingStatus.COMPLETED
            assert document.filename == temp_file.name
            assert document.chunk_count > 0

            print(f"✅ Document added: {document.filename}")
            print(f"   Chunks: {document.chunk_count}")
            print(f"   Status: {document.processing_status.value}")
        finally:
            # Cleanup
            temp_file.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_list_documents(self):
        """Test listing documents."""
        service = KnowledgeService()

        # List should work even with no documents
        docs = service.list_documents()
        assert isinstance(docs, list)

        print(f"✅ Listed {len(docs)} documents")

    @pytest.mark.asyncio
    async def test_search_documents(self):
        """Test searching documents."""
        # Create a temporary HTML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(
                """
            <html>
            <body>
                <h1>Machine Learning Guide</h1>
                <p>Neural networks are computational models inspired by biological neurons.</p>
                <p>Deep learning is a subset of machine learning using neural networks.</p>
            </body>
            </html>
            """
            )
            temp_file = Path(f.name)

        try:
            service = KnowledgeService()

            # Add document
            doc_id = await service.add_document(
                temp_file,
                async_processing=False,
            )

            # Search for relevant content
            results = await service.search("neural networks", top_k=5)

            assert len(results) > 0
            assert results[0]["relevance_score"] > 0.5
            assert "neural" in results[0]["chunk_text"].lower()

            print(f"✅ Search returned {len(results)} results")
            print(f"   Top result: {results[0]['chunk_text'][:100]}...")
            print(f"   Relevance: {results[0]['relevance_score']:.2f}")
        finally:
            temp_file.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_remove_document(self):
        """Test removing a document."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write("<html><body><p>Test document</p></body></html>")
            temp_file = Path(f.name)

        try:
            service = KnowledgeService()

            # Add document
            doc_id = await service.add_document(temp_file, async_processing=False)
            assert service.get_document(doc_id) is not None

            # Remove document
            removed = await service.remove_document(doc_id)
            assert removed is True
            assert service.get_document(doc_id) is None

            print(f"✅ Document removed successfully")
        finally:
            temp_file.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_knowledge_base_statistics(self):
        """Test getting knowledge base statistics."""
        service = KnowledgeService()

        stats = service.get_statistics()

        assert "document_count" in stats
        assert "total_chunks" in stats
        assert "total_size_mb" in stats
        assert isinstance(stats["document_count"], int)

        print(f"✅ Statistics retrieved:")
        print(f"   Documents: {stats['document_count']}")
        print(f"   Chunks: {stats['total_chunks']}")
        print(f"   Size: {stats['total_size_mb']:.2f} MB")


if __name__ == "__main__":
    # Run tests
    async def main():
        test = TestKnowledgeWorkflows()
        await test.test_add_simple_text_document()
        await test.test_list_documents()
        await test.test_search_documents()
        await test.test_remove_document()
        await test.test_knowledge_base_statistics()

    asyncio.run(main())
