#!/usr/bin/env python3
"""Live test of the Tafsir Pipeline with real Qwen LLM."""

import logging
import sys
import os
import json  # pylint: disable=multiple-imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from al_furqan import setup_logging  # pylint: disable=wrong-import-position
from al_furqan.engine.tafsir.pipeline import TafsirPipeline  # pylint: disable=wrong-import-position
from al_furqan.providers import LLMConfig, create_llm  # pylint: disable=wrong-import-position

logger = logging.getLogger(__name__)

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
if not API_KEY:
    raise SystemExit("DASHSCOPE_API_KEY environment variable not set")
MODEL = "qwen3.5-397b-a17b"
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "review", "proposed_edges.db")

# Create LLM provider
llm_provider = create_llm(LLMConfig(
    provider="dashscope",
    model_name=MODEL,
    api_key=API_KEY,
    temperature=0.3,
    max_tokens=3000,
))


def llm_call(messages, tools=None):
    """Adapter: convert pipeline format to DashScope format."""
    import requests  # pylint: disable=import-outside-toplevel

    url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 3000,
        "enable_thinking": False,
    }

    # Add tools if provided (for function calling)
    if tools:
        payload["tools"] = tools
        # Force tool use on first round (when no tool results yet)
        has_tool_results = any(m.get("role") == "tool" for m in messages)
        if not has_tool_results:
            payload["tool_choice"] = "auto"

    response = requests.post(url, json=payload, headers=headers, timeout=120)
    data = response.json()

    if response.status_code != 200:
        error = data.get("error", {}).get("message", str(data))
        logger.error("LLM Error: %s", error)
        return {"content": f"Error: {error}", "tool_calls": None}

    choice = data["choices"][0]
    message = choice["message"]

    return {
        "content": message.get("content", ""),
        "tool_calls": message.get("tool_calls", None),
    }


def main():
    """Execute main."""
    setup_logging()
    question = "إيه علاقة أول أربع آيات من سورة الأنعام بالآية رقم 5؟"

    logger.info("%s", "=" * 70)
    logger.info("Live Pipeline Test - Tafsir RAG")
    logger.info("%s", "=" * 70)
    logger.info("Model: %s", MODEL)
    logger.info("Question: %s", question)

    pipeline = TafsirPipeline(
        db_path=DB_PATH,
        llm_call=llm_call,
        model_name=MODEL,
    )

    logger.info("Running pipeline...")
    result = pipeline.run(question)

    logger.info("%s", "=" * 70)
    logger.info("Pipeline Summary")
    logger.info("%s", "=" * 70)
    logger.info("%s", result.summary())

    logger.info("%s", "=" * 70)
    logger.info("Tool Calls")
    logger.info("%s", "=" * 70)
    if result.tool_calls:
        for i, tc in enumerate(result.tool_calls, 1):
            logger.info("  [%d] %s(%s)", i, tc["name"], tc["arguments"])
    else:
        logger.info("  (no tool calls)")

    logger.info("%s", "=" * 70)
    logger.info("LLM Response")
    logger.info("%s", "=" * 70)
    logger.info("%s", result.llm_response)

    # Save result
    output = {
        "question": result.question,
        "query_type": result.query_analysis.query_type.value,
        "verse_refs": result.query_analysis.verse_refs,
        "topics": result.query_analysis.topics,
        "template": result.reasoning_plan.template_name,
        "tool_calls": result.tool_calls,
        "llm_response": result.llm_response,
        "llm_calls": result.llm_calls,
        "total_time_ms": result.total_time_ms,
        "model": result.model,
    }

    out_path = os.path.join(os.path.dirname(__file__), "..", "data", "benchmark", "pipeline_test_live.json")  # pylint: disable=line-too-long
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:  # pylint: disable=unspecified-encoding
        json.dump(output, f, ensure_ascii=False, indent=2)
    logger.info("Saved to %s", out_path)


if __name__ == "__main__":
    main()
