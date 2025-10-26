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

ALL_TOOLS = [
    KNOWLEDGE_ADD_TOOL,
    KNOWLEDGE_SEARCH_TOOL,
    KNOWLEDGE_SHOW_TOOL,
    KNOWLEDGE_REMOVE_TOOL,
    KNOWLEDGE_CLEAR_TOOL,
    KNOWLEDGE_STATUS_TOOL,
    KNOWLEDGE_TASK_STATUS_TOOL,
]
