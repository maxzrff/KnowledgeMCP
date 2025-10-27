"""
MCP tool definitions for knowledge server.
"""


# MCP Tool schemas
KNOWLEDGE_ADD_TOOL = {
    "name": "knowledge-add",
    "description": "Add a document or image to the knowledge base for semantic search",
    "inputSchema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the document or image file",
            },
            "metadata": {
                "type": "object",
                "description": "Additional metadata (author, title, tags)",
                "default": {},
            },
            "force_ocr": {
                "type": "boolean",
                "description": "Force OCR even if text extraction available",
                "default": False,
            },
            "async": {
                "type": "boolean",
                "description": "Process asynchronously and return task ID",
                "default": True,
            },
            "contexts": {
                "type": "string",
                "description": "Comma-separated list of context names (e.g., 'aws,healthcare'). Defaults to 'default'",
                "default": "default",
            },
        },
        "required": ["file_path"],
    },
}

KNOWLEDGE_SEARCH_TOOL = {
    "name": "knowledge-search",
    "description": "Search the knowledge base using natural language query",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language search query",
            },
            "top_k": {
                "type": "integer",
                "description": "Number of results to return",
                "default": 10,
                "minimum": 1,
                "maximum": 50,
            },
            "min_relevance": {
                "type": "number",
                "description": "Minimum relevance score threshold (0.0 to 1.0)",
                "default": 0.0,
                "minimum": 0.0,
                "maximum": 1.0,
            },
            "context": {
                "type": "string",
                "description": "Optional context name to search within (omit to search all contexts)",
            },
        },
        "required": ["query"],
    },
}

KNOWLEDGE_SHOW_TOOL = {
    "name": "knowledge-show",
    "description": "List all documents in the knowledge base",
    "inputSchema": {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Maximum number of documents to return",
                "default": 100,
            },
            "context": {
                "type": "string",
                "description": "Optional context name to filter documents (omit to show all)",
            },
        },
    },
}

KNOWLEDGE_REMOVE_TOOL = {
    "name": "knowledge-remove",
    "description": "Remove a specific document from the knowledge base",
    "inputSchema": {
        "type": "object",
        "properties": {
            "document_id": {
                "type": "string",
                "description": "ID of the document to remove",
            },
            "confirm": {
                "type": "boolean",
                "description": "Confirmation flag for destructive operation",
                "default": False,
            },
        },
        "required": ["document_id", "confirm"],
    },
}

KNOWLEDGE_CLEAR_TOOL = {
    "name": "knowledge-clear",
    "description": "Clear all documents from the knowledge base",
    "inputSchema": {
        "type": "object",
        "properties": {
            "confirm": {
                "type": "boolean",
                "description": "Confirmation flag for destructive operation",
                "default": False,
            },
        },
        "required": ["confirm"],
    },
}

KNOWLEDGE_STATUS_TOOL = {
    "name": "knowledge-status",
    "description": "Get knowledge base statistics and status",
    "inputSchema": {
        "type": "object",
        "properties": {},
    },
}

KNOWLEDGE_TASK_STATUS_TOOL = {
    "name": "knowledge-task-status",
    "description": "Get status of an async processing task",
    "inputSchema": {
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "Task ID from async operation",
            },
        },
        "required": ["task_id"],
    },
}

KNOWLEDGE_CONTEXT_CREATE_TOOL = {
    "name": "knowledge-context-create",
    "description": "Create a new context for organizing documents",
    "inputSchema": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Unique context name (alphanumeric, dash, underscore, 1-64 chars)",
            },
            "description": {
                "type": "string",
                "description": "Optional description of the context",
            },
            "metadata": {
                "type": "object",
                "description": "Optional metadata dictionary",
                "default": {},
            },
        },
        "required": ["name"],
    },
}

KNOWLEDGE_CONTEXT_LIST_TOOL = {
    "name": "knowledge-context-list",
    "description": "List all contexts in the knowledge base",
    "inputSchema": {
        "type": "object",
        "properties": {},
    },
}

KNOWLEDGE_CONTEXT_SHOW_TOOL = {
    "name": "knowledge-context-show",
    "description": "Show details of a specific context including its documents",
    "inputSchema": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Context name",
            },
        },
        "required": ["name"],
    },
}

KNOWLEDGE_CONTEXT_DELETE_TOOL = {
    "name": "knowledge-context-delete",
    "description": "Delete a context and all its vectors (documents remain in other contexts)",
    "inputSchema": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Context name to delete",
            },
            "confirm": {
                "type": "boolean",
                "description": "Confirmation flag for destructive operation",
                "default": False,
            },
        },
        "required": ["name", "confirm"],
    },
}

ALL_TOOLS = [
    KNOWLEDGE_ADD_TOOL,
    KNOWLEDGE_SEARCH_TOOL,
    KNOWLEDGE_SHOW_TOOL,
    KNOWLEDGE_REMOVE_TOOL,
    KNOWLEDGE_CLEAR_TOOL,
    KNOWLEDGE_STATUS_TOOL,
    KNOWLEDGE_TASK_STATUS_TOOL,
    KNOWLEDGE_CONTEXT_CREATE_TOOL,
    KNOWLEDGE_CONTEXT_LIST_TOOL,
    KNOWLEDGE_CONTEXT_SHOW_TOOL,
    KNOWLEDGE_CONTEXT_DELETE_TOOL,
]
