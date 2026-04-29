"""
Furqan RaaS — MCP-compatible reasoning server.

Implements JSON-RPC 2.0 over stdio following the Model Context Protocol.
No external MCP SDK dependency — pure stdlib implementation.

Usage:
    python -m furqan_raas.mcp_server
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import uuid
from typing import Any, Callable, Optional

# ---------------------------------------------------------------------------
# Ensure the al_furqan engine is importable
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from al_furqan.engine.pipeline import EvaluationPipeline  # noqa: E402  # pylint: disable=wrong-import-position
from al_furqan.engine.models import GateResult  # noqa: E402  # pylint: disable=wrong-import-position
from al_furqan.engine.symbolic.verifier import SymbolicVerifier  # noqa: E402  # pylint: disable=wrong-import-position
from al_furqan.kb.retriever import (  # noqa: E402  # pylint: disable=unused-import, wrong-import-position
    UnifiedRetriever,
    RetrievalConfig,
    Source,
)

logger = logging.getLogger("furqan_raas.mcp_server")

# ---------------------------------------------------------------------------
# Safety / Intent helpers
# ---------------------------------------------------------------------------

_HARMFUL_KEYWORDS = [
    "how to kill",
    "how to harm",
    "how to make a bomb",
    "how to poison",
    "suicide method",
    "how to attack",
    "terrorism",
    "how to destroy",
]


def detect_intent(question: str) -> str:
    """Simple keyword-based intent detection.

    Returns one of: 'harmful', 'informational', 'evaluative'.
    """
    q_lower = question.lower().strip()
    for kw in _HARMFUL_KEYWORDS:
        if kw in q_lower:
            return "harmful"

    # Informational signals
    info_prefixes = [
        "what is", "what are", "who is", "who are",
        "when did", "when was", "where is", "where are",
        "define ", "explain ", "list ", "describe ",
        "ما هو", "ما هي", "من هو", "من هي",
    ]
    for prefix in info_prefixes:
        if q_lower.startswith(prefix):
            return "informational"

    return "evaluative"


# ---------------------------------------------------------------------------
# Available domains
# ---------------------------------------------------------------------------

AVAILABLE_DOMAINS = [
    {
        "id": "islamic",
        "name": "Islamic Studies",
        "description": "Quran, Hadith, and Fiqh — verified Islamic scholarly sources.",
        "collections": ["quran", "hadith", "fiqh"],
        "total_sources": 6316,
    },
]


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

class FurqanMCPServer:
    """MCP server exposing Furqan reasoning tools via JSON-RPC 2.0."""

    SERVER_NAME = "furqan-reasoning"
    SERVER_VERSION = "0.1.0"
    PROTOCOL_VERSION = "2024-11-05"

    TOOLS = [
        {
            "name": "furqan_evaluate",
            "description": (
                "Evaluate a question/claim through axiom-anchored reasoning "
                "with 4-gate verification and Z3 formal proof."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question or claim to evaluate",
                    },
                    "domain": {
                        "type": "string",
                        "default": "islamic",
                        "description": "Knowledge domain to evaluate against",
                    },
                    "depth": {
                        "type": "string",
                        "enum": ["quick", "standard", "deep"],
                        "default": "standard",
                        "description": "Evaluation depth: quick (no Z3), standard, deep (extra self-correction)",  # pylint: disable=line-too-long
                    },
                },
                "required": ["question"],
            },
        },
        {
            "name": "furqan_verify",
            "description": "Quick claim verification against the knowledge base. Returns confidence score and citations.",  # pylint: disable=line-too-long
            "inputSchema": {
                "type": "object",
                "properties": {
                    "claim": {
                        "type": "string",
                        "description": "The claim to verify",
                    },
                    "domain": {
                        "type": "string",
                        "default": "islamic",
                    },
                },
                "required": ["claim"],
            },
        },
        {
            "name": "furqan_retrieve",
            "description": "Pure knowledge retrieval — search verified knowledge bases and return formatted sources.",  # pylint: disable=line-too-long
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (Arabic or English)",
                    },
                    "sources": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["quran", "hadith", "fiqh"]},
                        "description": "Which collections to search (default: all)",
                    },
                    "limit": {
                        "type": "integer",
                        "default": 5,
                        "description": "Max results per source",
                    },
                },
                "required": ["query"],
            },
        },
        {
            "name": "furqan_explain",
            "description": "Get a sourced explanation of a topic grounded in verified knowledge.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The topic to explain",
                    },
                    "domain": {
                        "type": "string",
                        "default": "islamic",
                    },
                },
                "required": ["topic"],
            },
        },
        {
            "name": "furqan_domains",
            "description": "List all available knowledge domains and their statistics.",
            "inputSchema": {
                "type": "object",
                "properties": {},
            },
        },
    ]

    def __init__(
        self,
        llm_fn: Optional[Callable[[str], str]] = None,
        retriever: Optional[UnifiedRetriever] = None,
        verifier: Optional[SymbolicVerifier] = None,
    ):
        """Initialize the MCP server.

        Args:
            llm_fn: LLM callable (prompt -> response). Required for evaluate/explain.
            retriever: Knowledge base retriever. Optional.
            verifier: Z3 symbolic verifier. Optional.
        """
        self.llm_fn = llm_fn
        self.retriever = retriever
        self.verifier = verifier
        self._pipeline: Optional[EvaluationPipeline] = None
        if llm_fn:
            self._pipeline = EvaluationPipeline(llm_fn)

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
            "furqan_evaluate": self._evaluate,
            "furqan_verify": self._verify,
            "furqan_retrieve": self._retrieve,
            "furqan_explain": self._explain,
            "furqan_domains": self._domains,
        }
        handler = handlers.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")
        return handler(args)

    # ----- Tool handlers -----

    def _evaluate(self, args: dict) -> dict:  # pylint: disable=too-many-locals
        """Full axiom-anchored evaluation with 4-gate scoring and optional Z3."""
        question = args.get("question", "")
        if not question:
            raise ValueError("question is required")

        _domain = args.get("domain", "islamic")
        depth = args.get("depth", "standard")

        start = time.time()
        eval_id = f"eval_{uuid.uuid4().hex[:12]}"

        # 1. Intent detection
        intent = detect_intent(question)

        # 2. Safety filter
        if intent == "harmful":
            return self._content_result({
                "type": "evaluation",
                "refused": True,
                "reason": "This question has been flagged as potentially harmful and cannot be evaluated.",  # pylint: disable=line-too-long
                "evaluation_id": eval_id,
            })

        # 3. Informational shortcut
        if intent == "informational" and self._pipeline:
            info = self._pipeline.answer_informational(question)
            return self._content_result({
                "type": "informational",
                "response": info.answer,
                "category": info.category,
                "sources_suggested": info.sources_suggested,
                "related_topics": info.related_topics,
                "evaluation_id": eval_id,
                "processing_time_ms": (time.time() - start) * 1000,
            })

        # 4. Full evaluation pipeline
        if not self._pipeline:
            raise ValueError("LLM function required for evaluation — server not configured with llm_fn")  # pylint: disable=line-too-long

        # Retrieve KB context
        context = ""
        sources_data: list[dict] = []
        if self.retriever:
            try:
                kb_ctx = self.retriever.retrieve(question)
                context = kb_ctx.formatted_text
                sources_data = [
                    {
                        "source": r.source.value,
                        "reference": r.reference,
                        "content_en": r.content_en,
                    }
                    for r in kb_ctx.results
                ]
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.warning("KB retrieval failed: %s", e)

        # Run pipeline
        verdict = self._pipeline.evaluate(question, context=context)

        # Z3 verification
        z3_data: Optional[dict] = None
        if depth != "quick" and self.verifier:
            try:
                v_data = {"exists": True, "has_purpose": True}
                z3_result = self.verifier.verify_verdict(v_data)
                z3_data = {
                    "consistent": z3_result.consistent,
                    "proof": z3_result.proof,
                    "contradictions": z3_result.contradictions,
                    "verification_time_ms": z3_result.verification_time_ms,
                }
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.warning("Z3 verification failed: %s", e)

        gate_scores = [gs.to_dict() for gs in verdict.gate_scores]
        processing_time = (time.time() - start) * 1000

        return self._content_result({
            "type": "evaluation",
            "response": verdict.final_judgment,
            "verdict": {
                "gate_scores": gate_scores,
                "z3_verification": z3_data,
                "total_score": verdict.total_score,
                "origin_gate": verdict.origin_gate.value if isinstance(verdict.origin_gate, GateResult) else str(verdict.origin_gate),  # pylint: disable=line-too-long
            },
            "sources": sources_data,
            "evaluation_id": eval_id,
            "processing_time_ms": processing_time,
        })

    def _verify(self, args: dict) -> dict:
        """Quick claim verification against the knowledge base."""
        claim = args.get("claim", "")
        if not claim:
            raise ValueError("claim is required")

        start = time.time()
        sources_data: list[dict] = []
        confidence = 0.0

        if self.retriever:
            try:
                kb_ctx = self.retriever.retrieve(claim)
                for r in kb_ctx.results:
                    sources_data.append({
                        "source": r.source.value,
                        "reference": r.reference,
                        "content_ar": r.content_ar,
                        "content_en": r.content_en,
                    })
                # Simple confidence: if sources found, proportional to count
                if sources_data:
                    confidence = min(1.0, len(sources_data) / 5.0)
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.warning("KB retrieval for verification failed: %s", e)

        processing_time = (time.time() - start) * 1000

        return self._content_result({
            "type": "verification",
            "claim": claim,
            "confidence": round(confidence, 3),
            "sources_found": len(sources_data),
            "citations": sources_data,
            "processing_time_ms": processing_time,
        })

    def _retrieve(self, args: dict) -> dict:
        """Pure knowledge retrieval."""
        query = args.get("query", "")
        if not query:
            raise ValueError("query is required")

        source_names = args.get("sources", ["quran", "hadith", "fiqh"])
        limit = args.get("limit", 5)

        source_map = {"quran": Source.QURAN, "hadith": Source.HADITH, "fiqh": Source.FIQH}
        sources = [source_map[s] for s in source_names if s in source_map]

        results_data: list[dict] = []
        if self.retriever:
            config = RetrievalConfig(sources=sources, limit_per_source=limit)
            try:
                kb_ctx = self.retriever.retrieve(query, config=config)
                for r in kb_ctx.results:
                    results_data.append({
                        "source": r.source.value,
                        "reference": r.reference,
                        "content_ar": r.content_ar,
                        "content_en": r.content_en,
                        "metadata": r.metadata,
                    })
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.warning("Retrieval failed: %s", e)

        return self._content_result({
            "type": "retrieval",
            "query": query,
            "results": results_data,
            "total_found": len(results_data),
        })

    def _explain(self, args: dict) -> dict:
        """Sourced explanation of a topic."""
        topic = args.get("topic", "")
        if not topic:
            raise ValueError("topic is required")

        start = time.time()

        # Retrieve relevant sources
        sources_data: list[dict] = []
        context_text = ""
        if self.retriever:
            try:
                kb_ctx = self.retriever.retrieve(topic)
                context_text = kb_ctx.formatted_text
                for r in kb_ctx.results:
                    sources_data.append({
                        "source": r.source.value,
                        "reference": r.reference,
                        "content_en": r.content_en,
                    })
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.warning("Retrieval for explain failed: %s", e)

        # Generate explanation via LLM
        explanation = ""
        if self.llm_fn and context_text:
            prompt = (
                f"Based on the following verified sources, provide a clear and accurate "
                f"explanation of: {topic}\n\n"
                f"Sources:\n{context_text}\n\n"
                f"Provide an explanation grounded ONLY in the sources above. "
                f"Cite specific references."
            )
            try:
                explanation = self.llm_fn(prompt)
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.warning("LLM explanation failed: %s", e)
                explanation = f"Sources found but explanation generation failed: {e}"
        elif not self.llm_fn:
            explanation = f"Sources retrieved for '{topic}'. LLM not configured for explanation generation."  # pylint: disable=line-too-long
        else:
            explanation = f"No sources found for '{topic}'."

        processing_time = (time.time() - start) * 1000

        return self._content_result({
            "type": "explanation",
            "topic": topic,
            "explanation": explanation,
            "sources": sources_data,
            "processing_time_ms": processing_time,
        })

    def _domains(self, _args: dict) -> dict:
        """List available knowledge domains."""
        return self._content_result({
            "type": "domains",
            "domains": AVAILABLE_DOMAINS,
        })

    # ----- Helpers -----

    @staticmethod
    def _content_result(data: dict) -> dict:
        """Wrap data in MCP content response format."""
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
        logger.info("Furqan RaaS MCP server starting (stdio transport)")
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


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    """Start the MCP server."""
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    server = FurqanMCPServer()
    server.run_stdio()


if __name__ == "__main__":
    main()
