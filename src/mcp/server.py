"""
MCP server implementation for knowledge server.
"""

import asyncio
import json
from pathlib import Path
from typing import Any

from mcp.server.sse import SseServerTransport
from mcp.server.stdio import stdio_server
from starlette.applications import Starlette
from starlette.routing import Route

from mcp import types
from mcp.server import Server
from src.config.settings import get_settings
from src.mcp.tools import ALL_TOOLS
from src.services.knowledge_service import KnowledgeService
from src.utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)


class KnowledgeMCPServer:
    """MCP server for knowledge base operations."""

    def __init__(self):
        self.app = Server("knowledge-server")
        self.knowledge_service = KnowledgeService()
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register MCP protocol handlers."""

        @self.app.list_tools()
        async def list_tools() -> list[types.Tool]:
            """List available tools."""
            return [
                types.Tool(
                    name=tool["name"],
                    description=tool["description"],
                    inputSchema=tool["inputSchema"],
                )
                for tool in ALL_TOOLS
            ]

        @self.app.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
            """Handle tool calls."""
            return await self._handle_tool_call(name, arguments)

    async def _handle_tool_call(self, name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
        """Handle a tool call and return the result."""
        try:
            if name == "knowledge-add":
                result = await self._handle_add(arguments)
            elif name == "knowledge-search":
                result = await self._handle_search(arguments)
            elif name == "knowledge-show":
                result = await self._handle_show(arguments)
            elif name == "knowledge-remove":
                result = await self._handle_remove(arguments)
            elif name == "knowledge-clear":
                result = await self._handle_clear(arguments)
            elif name == "knowledge-status":
                result = await self._handle_status(arguments)
            elif name == "knowledge-task-status":
                result = await self._handle_task_status(arguments)
            elif name == "knowledge-context-create":
                result = await self._handle_context_create(arguments)
            elif name == "knowledge-context-list":
                result = await self._handle_context_list(arguments)
            elif name == "knowledge-context-show":
                result = await self._handle_context_show(arguments)
            elif name == "knowledge-context-delete":
                result = await self._handle_context_delete(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            logger.error(f"Tool call error: {e}", exc_info=True)
            error_result = {
                "success": False,
                "error": str(type(e).__name__),
                "message": str(e),
            }
            return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]

    async def _handle_add(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle knowledge-add tool."""
        file_path = Path(args["file_path"])
        metadata = args.get("metadata", {})
        async_processing = args.get("async", True)
        force_ocr = args.get("force_ocr", False)
        contexts_str = args.get("contexts", "default")

        # Parse comma-separated contexts
        contexts = [ctx.strip() for ctx in contexts_str.split(",") if ctx.strip()]
        if not contexts:
            contexts = ["default"]

        result_id = await self.knowledge_service.add_document(
            file_path,
            metadata=metadata,
            async_processing=async_processing,
            force_ocr=force_ocr,
            contexts=contexts,
        )

        if async_processing:
            return {
                "success": True,
                "task_id": result_id,
                "message": "Document queued for processing",
                "contexts": contexts,
                "force_ocr": force_ocr,
            }
        document = self.knowledge_service.get_document(result_id)
        return {
            "success": True,
            "document_id": result_id,
            "filename": document.filename if document else None,
            "contexts": document.contexts if document else contexts,
            "chunks_created": document.chunk_count if document else 0,
            "processing_method": document.processing_method.value if document and document.processing_method else None,
        }

    async def _handle_search(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle knowledge-search tool."""
        query = args["query"]
        top_k = args.get("top_k", 10)
        min_relevance = args.get("min_relevance", 0.0)
        context = args.get("context")

        results = await self.knowledge_service.search(
            query=query,
            top_k=top_k,
            min_relevance=min_relevance,
            context=context,
        )

        return {
            "success": True,
            "query": query,
            "context": context if context else "all",
            "total_results": len(results),
            "results": results,
        }

    async def _handle_show(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle knowledge-show tool."""
        limit = args.get("limit", 100)
        context = args.get("context")
        documents = self.knowledge_service.list_documents(context=context)[:limit]

        return {
            "success": True,
            "context": context if context else "all",
            "total_count": len(self.knowledge_service.list_documents(context=context)),
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "format": doc.format.value,
                    "size_bytes": doc.size_bytes,
                    "chunk_count": doc.chunk_count,
                    "contexts": doc.contexts,
                    "processing_status": doc.processing_status.value,
                    "processing_method": doc.processing_method.value if doc.processing_method else None,
                    "date_added": doc.date_added.isoformat(),
                    "ocr_used": doc.metadata.get("ocr_used", False),
                    "ocr_confidence": doc.metadata.get("ocr_confidence"),
                }
                for doc in documents
            ],
        }

    async def _handle_remove(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle knowledge-remove tool."""
        if not args.get("confirm", False):
            return {
                "success": False,
                "error": "confirmation_required",
                "message": "Set confirm=true to remove document",
            }

        document_id = args["document_id"]
        document = self.knowledge_service.get_document(document_id)

        if not document:
            return {
                "success": False,
                "error": "not_found",
                "message": f"Document not found: {document_id}",
            }

        await self.knowledge_service.remove_document(document_id)

        return {
            "success": True,
            "message": f"Removed document: {document.filename}",
            "chunks_removed": document.chunk_count,
        }

    async def _handle_clear(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle knowledge-clear tool."""
        if not args.get("confirm", False):
            return {
                "success": False,
                "error": "confirmation_required",
                "message": "Set confirm=true to clear knowledge base",
            }

        count = await self.knowledge_service.clear_knowledge_base()

        return {
            "success": True,
            "message": f"Cleared knowledge base: {count} documents removed",
            "documents_removed": count,
        }

    async def _handle_status(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle knowledge-status tool."""
        stats = self.knowledge_service.get_statistics()

        return {
            "success": True,
            "knowledge_base": {
                "name": "default",
                "document_count": stats["document_count"],
                "total_chunks": stats["total_chunks"],
                "total_size_mb": stats["total_size_mb"],
                "average_chunks_per_document": stats["average_chunks_per_document"],
            },
            "health": {
                "status": "healthy",
                "vector_db_connected": True,
                "embedding_model_loaded": True,
            },
        }

    async def _handle_task_status(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle knowledge-task-status tool."""
        task_id = args["task_id"]
        task = self.knowledge_service.get_task_status(task_id)

        if not task:
            return {
                "success": False,
                "error": "not_found",
                "message": f"Task not found: {task_id}",
            }

        return {
            "success": True,
            "task_id": task.task_id,
            "status": task.status.value,
            "progress": task.progress,
            "current_step": task.current_step,
            "error": task.error,
        }

    async def _handle_context_create(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle knowledge-context-create tool."""
        name = args["name"]
        description = args.get("description")
        metadata = args.get("metadata", {})

        context = self.knowledge_service.context_service.create_context(
            name=name,
            description=description,
            metadata=metadata,
        )

        return {
            "success": True,
            "context": {
                "name": context.name,
                "description": context.description,
                "created_at": context.created_at.isoformat(),
                "document_count": context.document_count,
            },
        }

    async def _handle_context_list(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle knowledge-context-list tool."""
        contexts = self.knowledge_service.context_service.list_contexts()

        return {
            "success": True,
            "total_count": len(contexts),
            "contexts": [
                {
                    "name": ctx.name,
                    "description": ctx.description,
                    "document_count": ctx.document_count,
                    "created_at": ctx.created_at.isoformat(),
                    "updated_at": ctx.updated_at.isoformat(),
                }
                for ctx in contexts
            ],
        }

    async def _handle_context_show(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle knowledge-context-show tool."""
        name = args["name"]

        context = self.knowledge_service.context_service.get_context(name)
        documents = self.knowledge_service.list_documents(context=name)

        return {
            "success": True,
            "context": {
                "name": context.name,
                "description": context.description,
                "document_count": context.document_count,
                "created_at": context.created_at.isoformat(),
                "updated_at": context.updated_at.isoformat(),
            },
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "format": doc.format.value,
                    "size_bytes": doc.size_bytes,
                    "chunk_count": doc.chunk_count,
                    "processing_status": doc.processing_status.value,
                }
                for doc in documents
            ],
        }

    async def _handle_context_delete(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle knowledge-context-delete tool."""
        name = args["name"]
        confirm = args.get("confirm", False)

        if not confirm:
            return {
                "success": False,
                "error": "confirmation_required",
                "message": "Context deletion requires confirm=true",
            }

        # Delete from vector store
        self.knowledge_service.vector_store.delete_collection(name)

        # Delete from context service
        message = self.knowledge_service.context_service.delete_context(name)

        return {
            "success": True,
            "message": message,
            "context": name,
        }

    async def run(self) -> None:
        """Run the MCP server."""
        settings = get_settings()
        logger.info("Starting MCP Knowledge Server...")

        if settings.mcp.transport == "http":
            # HTTP transport using SSE
            logger.info(f"Starting HTTP server on {settings.mcp.host}:{settings.mcp.port}")

            sse = SseServerTransport("/messages")

            async def handle_sse(request):
                async with sse.connect_sse(
                    request.scope, request.receive, request._send
                ) as streams:
                    await self.app.run(
                        streams[0], streams[1], self.app.create_initialization_options()
                    )

            starlette_app = Starlette(
                debug=True,
                routes=[
                    Route("/messages", endpoint=handle_sse),
                ],
            )

            import uvicorn
            config = uvicorn.Config(
                starlette_app,
                host=settings.mcp.host,
                port=settings.mcp.port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()
        else:
            # STDIO transport (default)
            async with stdio_server() as (read_stream, write_stream):
                await self.app.run(
                    read_stream,
                    write_stream,
                    self.app.create_initialization_options(),
                )


async def main():
    """Main entry point."""
    setup_logging(level="INFO")
    settings = get_settings()

    if settings.mcp.transport == "http-streamable":
        # Use HTTP Streamable transport
        from src.mcp.http_server import HTTPStreamableServer
        server = HTTPStreamableServer()
        await server.run()
    else:
        # Use default transports (STDIO or SSE)
        server = KnowledgeMCPServer()
        await server.run()


if __name__ == "__main__":
    asyncio.run(main())
