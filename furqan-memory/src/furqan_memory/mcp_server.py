"""
Furqan Memory — MCP-compatible memory server.

Implements JSON-RPC 2.0 over stdio following the Model Context Protocol.
Runs client-side — all data stays on user's device.

Usage:
    python -m furqan_memory.mcp_server
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from typing import Any

from furqan_memory.storage.sqlite_store import MemoryStore
from furqan_memory.storage.vector_store import MemoryVectorSearch
from furqan_memory.memory_manager import MemoryManager

logger = logging.getLogger("furqan_memory.mcp_server")


class FurqanMemoryMCPServer:
    """MCP server exposing Furqan Memory tools via JSON-RPC 2.0."""

    SERVER_NAME = "furqan-memory"
    SERVER_VERSION = "0.1.0"
    PROTOCOL_VERSION = "2024-11-05"

    TOOLS = [
        {
            "name": "furqan_remember",
            "description": "Store a verdict in local memory. All data stays on your device.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question that was evaluated",
                    },
                    "verdict": {
                        "type": "object",
                        "description": "The verdict data (gate scores, judgment, etc.)",
                    },
                    "domain": {
                        "type": "string",
                        "default": "islamic",
                        "description": "Knowledge domain",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional tags for categorization",
                    },
                },
                "required": ["question", "verdict"],
            },
        },
        {
            "name": "furqan_recall",
            "description": "Search memory for relevant past verdicts using semantic similarity.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query",
                    },
                    "domain": {
                        "type": "string",
                        "default": "all",
                        "description": "Filter by domain (or 'all')",
                    },
                    "limit": {
                        "type": "integer",
                        "default": 5,
                        "description": "Max results to return",
                    },
                },
                "required": ["query"],
            },
        },
        {
            "name": "furqan_recognize",
            "description": "Fast-path pattern matching (<50ms). Check if a query matches a known pattern.",  # pylint: disable=line-too-long
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to match against known patterns",
                    },
                    "threshold": {
                        "type": "number",
                        "default": 0.75,
                        "description": "Minimum similarity threshold (0-1)",
                    },
                },
                "required": ["query"],
            },
        },
        {
            "name": "furqan_feedback",
            "description": "Rate a verdict to improve pattern accuracy over time.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "verdict_id": {
                        "type": "string",
                        "description": "The verdict ID to rate",
                    },
                    "rating": {
                        "type": "string",
                        "enum": ["positive", "negative", "neutral"],
                        "description": "Your rating",
                    },
                    "correction": {
                        "type": "string",
                        "description": "Optional correction or note",
                    },
                },
                "required": ["verdict_id", "rating"],
            },
        },
        {
            "name": "furqan_memory_stats",
            "description": "Memory usage statistics — how many verdicts, patterns, and feedback entries are stored.",  # pylint: disable=line-too-long
            "inputSchema": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Filter stats by domain (optional)",
                    },
                },
            },
        },
    ]

    def __init__(
        self,
        db_path: str = "furqan_memory.db",
        vector_persist_dir: str | None = None,
        manager: MemoryManager | None = None,
    ):
        """Initialize the MCP server.

        Args:
            db_path: Path to SQLite database.
            vector_persist_dir: Path for ChromaDB persistence. None = ephemeral.
            manager: Pre-configured MemoryManager (for testing).
        """
        if manager:
            self.manager = manager
        else:
            store = MemoryStore(db_path)
            vectors = MemoryVectorSearch(vector_persist_dir)
            self.manager = MemoryManager(store, vectors)

    # ----- JSON-RPC dispatch -----

    def handle_request(self, request: dict) -> dict:
        """Handle a JSON-RPC 2.0 request and return a response."""
        req_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})

        try:
            result = self._dispatch(method, params)
            return self._success(req_id, result)
        except NotImplementedError:  # pylint: disable=unused-variable
            return self._error(req_id, -32601, f"Method not found: {method}")
        except (ValueError, KeyError, TypeError) as exc:
            return self._error(req_id, -32602, f"Invalid params: {exc}")
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.exception("Internal error handling %s", method)
            return self._error(req_id, -32603, f"Internal error: {exc}")

    def _dispatch(self, method: str, params: dict) -> Any:
        """Route to the appropriate handler."""
        if method == "initialize":  # pylint: disable=no-else-return
            return self._handle_initialize(params)
        elif method == "tools/list":
            return {"tools": self.TOOLS}
        elif method == "tools/call":
            return self._call_tool(params)
        elif method == "ping":
            return {}
        else:
            raise NotImplementedError(method)

    def _handle_initialize(self, _params: dict) -> dict:
        return {
            "protocolVersion": self.PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {
                "name": self.SERVER_NAME,
                "version": self.SERVER_VERSION,
            },
        }

    def _call_tool(self, params: dict) -> dict:
        """Dispatch to the appropriate tool handler."""
        name = params.get("name", "")
        args = params.get("arguments", {})

        handlers = {
            "furqan_remember": self._remember,
            "furqan_recall": self._recall,
            "furqan_recognize": self._recognize,
            "furqan_feedback": self._feedback,
            "furqan_memory_stats": self._stats,
        }
        handler = handlers.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")
        return handler(args)

    # ----- Tool handlers -----

    def _remember(self, args: dict) -> dict:
        question = args.get("question", "")
        if not question:
            raise ValueError("question is required")
        verdict = args.get("verdict", {})
        if not verdict:
            raise ValueError("verdict is required")

        domain = args.get("domain", "islamic")
        tags = args.get("tags")

        verdict_id = self.manager.remember(question, verdict, domain, tags)
        return self._content_result({
            "type": "remembered",
            "verdict_id": verdict_id,
            "message": f"Verdict stored successfully. ID: {verdict_id}",
        })

    def _recall(self, args: dict) -> dict:
        query = args.get("query", "")
        if not query:
            raise ValueError("query is required")

        domain = args.get("domain", "all")
        limit = args.get("limit", 5)

        results = self.manager.recall(query, domain, limit)
        return self._content_result({
            "type": "recall",
            "query": query,
            "results": results,
            "total_found": len(results),
        })

    def _recognize(self, args: dict) -> dict:
        query = args.get("query", "")
        if not query:
            raise ValueError("query is required")

        threshold = args.get("threshold", 0.75)
        start = time.time()
        match = self.manager.recognize(query, threshold)
        elapsed_ms = (time.time() - start) * 1000

        if match:  # pylint: disable=no-else-return
            return self._content_result({
                "type": "recognized",
                "matched": True,
                "pattern": match["pattern"],
                "similarity": match["similarity"],
                "latency_ms": elapsed_ms,
            })
        else:
            return self._content_result({
                "type": "recognized",
                "matched": False,
                "message": "No matching pattern found. Proceed with full evaluation.",
                "latency_ms": elapsed_ms,
            })

    def _feedback(self, args: dict) -> dict:
        verdict_id = args.get("verdict_id", "")
        if not verdict_id:
            raise ValueError("verdict_id is required")
        rating = args.get("rating", "")
        if rating not in ("positive", "negative", "neutral"):
            raise ValueError("rating must be one of: positive, negative, neutral")

        correction = args.get("correction")
        feedback_id = self.manager.feedback(verdict_id, rating, correction)
        return self._content_result({
            "type": "feedback",
            "feedback_id": feedback_id,
            "message": "Feedback recorded. Thank you for helping improve accuracy.",
        })

    def _stats(self, args: dict) -> dict:
        domain = args.get("domain")
        stats = self.manager.stats(domain)
        return self._content_result({
            "type": "stats",
            **stats,
        })

    # ----- Helpers -----

    @staticmethod
    def _content_result(data: dict) -> dict:
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(data, ensure_ascii=False),
                }
            ]
        }

    @staticmethod
    def _success(req_id: Any, result: Any) -> dict:
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    @staticmethod
    def _error(req_id: Any, code: int, message: str) -> dict:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": code, "message": message},
        }

    # ----- stdio main loop -----

    def run_stdio(self) -> None:
        """Run the server reading JSON-RPC from stdin, writing to stdout."""
        logger.info("Furqan Memory MCP server starting (stdio transport)")
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                resp = self._error(None, -32700, "Parse error")
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
                continue

            response = self.handle_request(request)
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()


def main():
    """Start the MCP server."""
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    db_path = os.environ.get("FURQAN_MEMORY_DB", "furqan_memory.db")
    persist_dir = os.environ.get("FURQAN_MEMORY_VECTORS", None)
    server = FurqanMemoryMCPServer(db_path=db_path, vector_persist_dir=persist_dir)
    server.run_stdio()


if __name__ == "__main__":
    main()
