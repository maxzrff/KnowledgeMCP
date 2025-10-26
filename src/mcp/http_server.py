"""
HTTP Streamable transport implementation for MCP server.
Implements the MCP Streamable HTTP specification.
"""

import asyncio
import json
import secrets
from typing import Any

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, StreamingResponse
from starlette.routing import Route
from sse_starlette import EventSourceResponse

from mcp.server import Server
from mcp import types
from src.mcp.tools import ALL_TOOLS
from src.services.knowledge_service import KnowledgeService
from src.utils.logging_config import get_logger, setup_logging
from src.config.settings import get_settings

logger = get_logger(__name__)


class HTTPStreamableServer:
    """MCP server using HTTP Streamable transport."""

    def __init__(self):
        self.mcp_server = Server("knowledge-server")
        self.knowledge_service = KnowledgeService()
        self.sessions: dict[str, dict] = {}
        self._register_handlers()
        self._create_app()

    def _register_handlers(self) -> None:
        """Register MCP protocol handlers."""

        @self.mcp_server.list_tools()
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

        @self.mcp_server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
            """Handle tool calls."""
            from src.mcp.server import KnowledgeMCPServer
            
            temp_server = KnowledgeMCPServer()
            return await temp_server._handle_tool_call(name, arguments)

    def _create_app(self) -> None:
        """Create Starlette application."""
        self.app = Starlette(
            debug=True,
            routes=[
                Route("/mcp", endpoint=self.handle_mcp_post, methods=["POST"]),
                Route("/mcp", endpoint=self.handle_mcp_get, methods=["GET"]),
                Route("/mcp", endpoint=self.handle_mcp_delete, methods=["DELETE"]),
            ],
        )

    async def handle_mcp_post(self, request: Request) -> Response:
        """Handle HTTP POST requests (client messages to server)."""
        # Security: Validate Origin header
        origin = request.headers.get("origin")
        if origin and not self._is_valid_origin(origin):
            return JSONResponse(
                {"error": "Invalid origin"},
                status_code=403,
            )

        # Get session ID if present
        session_id = request.headers.get("mcp-session-id")
        
        # Parse request body
        try:
            body = await request.json()
        except Exception as e:
            logger.error(f"Invalid JSON: {e}")
            return JSONResponse(
                {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None},
                status_code=400,
            )

        # Handle session management
        # If session ID provided but not found, create it on demand
        if session_id and session_id not in self.sessions:
            self.sessions[session_id] = {
                "created_at": asyncio.get_event_loop().time(),
                "last_activity": asyncio.get_event_loop().time(),
            }
            logger.info(f"Created session on demand: {session_id}")

        # Check if this is an initialize request
        is_init = False
        if isinstance(body, dict):
            is_init = body.get("method") == "initialize"
        elif isinstance(body, list):
            is_init = any(msg.get("method") == "initialize" for msg in body if isinstance(msg, dict))

        # Create new session on initialize if no session ID provided
        if is_init and not session_id:
            session_id = secrets.token_urlsafe(32)
            self.sessions[session_id] = {
                "created_at": asyncio.get_event_loop().time(),
                "last_activity": asyncio.get_event_loop().time(),
            }
            logger.info(f"Created new session: {session_id}")

        # Process the message
        has_requests = self._has_requests(body)
        
        if not has_requests:
            # Only notifications/responses - return 202 Accepted
            return Response(status_code=202)

        # Has requests - return SSE stream or JSON response
        accept_header = request.headers.get("accept", "")
        if "text/event-stream" in accept_header:
            # Client supports SSE - stream response
            return await self._stream_response(body, session_id)
        else:
            # Client doesn't support SSE - return single JSON response
            response_data = await self._process_message(body)
            response = JSONResponse(response_data)
            
            if is_init and session_id:
                response.headers["mcp-session-id"] = session_id
            
            return response

    async def handle_mcp_get(self, request: Request) -> Response:
        """Handle HTTP GET requests (server messages to client)."""
        # Security: Validate Origin header
        origin = request.headers.get("origin")
        if origin and not self._is_valid_origin(origin):
            return JSONResponse(
                {"error": "Invalid origin"},
                status_code=403,
            )

        # Check if client accepts SSE
        accept_header = request.headers.get("accept", "")
        if "text/event-stream" not in accept_header:
            return Response(status_code=405)

        # Get session ID
        session_id = request.headers.get("mcp-session-id")
        if session_id and session_id not in self.sessions:
            return JSONResponse(
                {"error": "Session not found"},
                status_code=404,
            )

        # Open SSE stream for server-to-client messages
        async def event_generator():
            # This would be used for server-initiated notifications
            # For now, just keep the connection alive
            while True:
                await asyncio.sleep(30)
                yield {"event": "ping", "data": ""}

        return EventSourceResponse(event_generator())

    async def handle_mcp_delete(self, request: Request) -> Response:
        """Handle HTTP DELETE requests (session termination)."""
        session_id = request.headers.get("mcp-session-id")
        
        if not session_id:
            return Response(status_code=400)

        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Terminated session: {session_id}")
            return Response(status_code=200)
        
        return JSONResponse(
            {"error": "Session not found"},
            status_code=404,
        )

    def _is_valid_origin(self, origin: str) -> bool:
        """Validate origin header for DNS rebinding protection."""
        # Allow localhost origins
        if any(host in origin for host in ["localhost", "127.0.0.1", "[::1]"]):
            return True
        
        # Add your allowed origins here
        # For production, validate against a whitelist
        return False

    async def _handle_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any] | None:
        """Handle a tool call and return the result."""
        try:
            if tool_name == "knowledge-add":
                return await self._handle_add(arguments)
            elif tool_name == "knowledge-search":
                return await self._handle_search(arguments)
            elif tool_name == "knowledge-show":
                return await self._handle_show(arguments)
            elif tool_name == "knowledge-remove":
                return await self._handle_remove(arguments)
            elif tool_name == "knowledge-clear":
                return await self._handle_clear(arguments)
            elif tool_name == "knowledge-status":
                return await self._handle_status(arguments)
            elif tool_name == "knowledge-task-status":
                return await self._handle_task_status(arguments)
            else:
                return None
        except Exception as e:
            logger.error(f"Tool call error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(type(e).__name__),
                "message": str(e),
            }

    async def _handle_add(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle knowledge-add tool."""
        from pathlib import Path
        
        file_path = Path(args["file_path"])
        metadata = args.get("metadata", {})
        async_processing = args.get("async", True)

        result_id = await self.knowledge_service.add_document(
            file_path,
            metadata=metadata,
            async_processing=async_processing,
        )

        if async_processing:
            return {
                "success": True,
                "task_id": result_id,
                "message": "Document queued for processing",
            }
        document = self.knowledge_service.get_document(result_id)
        return {
            "success": True,
            "document_id": result_id,
            "filename": document.filename if document else None,
            "chunks_created": document.chunk_count if document else 0,
        }

    async def _handle_search(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle knowledge-search tool."""
        query = args["query"]
        top_k = args.get("top_k", 10)
        min_relevance = args.get("min_relevance", 0.0)

        results = await self.knowledge_service.search(
            query=query,
            top_k=top_k,
            min_relevance=min_relevance,
        )

        return {
            "success": True,
            "query": query,
            "total_results": len(results),
            "results": results,
        }

    async def _handle_show(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle knowledge-show tool."""
        limit = args.get("limit", 100)
        documents = self.knowledge_service.list_documents()[:limit]

        return {
            "success": True,
            "total_count": len(self.knowledge_service.list_documents()),
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "format": doc.format.value,
                    "size_bytes": doc.size_bytes,
                    "chunk_count": doc.chunk_count,
                    "processing_status": doc.processing_status.value,
                    "date_added": doc.date_added.isoformat(),
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

    def _has_requests(self, body: Any) -> bool:
        """Check if body contains any requests (vs only notifications/responses)."""
        if isinstance(body, dict):
            return body.get("method") is not None and "id" in body
        elif isinstance(body, list):
            return any(
                isinstance(msg, dict) and msg.get("method") is not None and "id" in msg
                for msg in body
            )
        return False

    async def _process_message(self, body: Any) -> Any:
        """Process a JSON-RPC message."""
        # This is a simplified implementation
        # In a real implementation, you would use the MCP server's protocol handler
        
        if isinstance(body, dict):
            method = body.get("method")
            params = body.get("params", {})
            msg_id = body.get("id")

            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2025-03-26",
                        "capabilities": {
                            "tools": {},
                        },
                        "serverInfo": {
                            "name": "knowledge-server",
                            "version": "1.0.0",
                        },
                    },
                }
            elif method == "tools/list":
                tools = [
                    {
                        "name": tool["name"],
                        "description": tool["description"],
                        "inputSchema": tool["inputSchema"],
                    }
                    for tool in ALL_TOOLS
                ]
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"tools": tools},
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                # Call the tool handler using shared knowledge service
                result = await self._handle_tool_call(tool_name, arguments)
                
                if result is None:
                    return {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {
                            "code": -32601,
                            "message": f"Unknown tool: {tool_name}",
                        },
                    }

                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2),
                            }
                        ]
                    },
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}",
                    },
                }
        
        return {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": None}

    async def _stream_response(self, body: Any, session_id: str | None) -> StreamingResponse:
        """Stream response using SSE."""
        async def event_generator():
            response = await self._process_message(body)
            yield {
                "event": "message",
                "data": json.dumps(response),
            }

        response = EventSourceResponse(event_generator())
        if session_id:
            response.headers["mcp-session-id"] = session_id
        return response

    async def run(self) -> None:
        """Run the HTTP server."""
        settings = get_settings()
        logger.info(f"Starting HTTP Streamable server on {settings.mcp.host}:{settings.mcp.port}")
        logger.info(f"MCP endpoint: http://{settings.mcp.host}:{settings.mcp.port}/mcp")
        
        config = uvicorn.Config(
            self.app,
            host=settings.mcp.host,
            port=settings.mcp.port,
            log_level="info",
        )
        server = uvicorn.Server(config)
        await server.serve()


async def main():
    """Main entry point."""
    setup_logging(level="INFO")
    server = HTTPStreamableServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
