---
name: furqan-memory
description: >
  Client-side memory and learning skill for AI agents.
  Stores verdicts, learns patterns, enables offline reasoning.
  All data stays on user's device — zero network dependency.
version: 0.1.0
transport: stdio
protocol: json-rpc-2.0
---

# Furqan Memory Skill

## What It Does

Furqan Memory gives your AI agent persistent memory across sessions. It stores evaluation verdicts locally, learns patterns from repeated queries, and enables fast-path recognition for known question types.

**Privacy-first:** All data stays on the user's device. No cloud sync. No telemetry.

## Available Tools

### furqan_remember
Store a verdict in local memory after evaluation.

```json
{
  "question": "Is riba (interest) haram?",
  "verdict": {
    "total_score": 95,
    "gate_results": [...],
    "final_judgment": "Prohibited based on Quran and Sunnah"
  },
  "domain": "islamic",
  "tags": ["fiqh", "muamalat"]
}
```

### furqan_recall
Search memory for relevant past verdicts using semantic similarity.

```json
{
  "query": "interest and banking",
  "domain": "islamic",
  "limit": 5
}
```

### furqan_recognize
Fast-path pattern matching. Check if a query matches a known, high-confidence pattern before running full evaluation. Target: <50ms.

```json
{
  "query": "Is bank interest allowed?",
  "threshold": 0.75
}
```

### furqan_feedback
Rate a verdict to improve pattern accuracy over time.

```json
{
  "verdict_id": "v_abc123",
  "rating": "positive",
  "correction": null
}
```

### furqan_memory_stats
Get memory usage statistics.

```json
{
  "domain": "islamic"
}
```

## Usage Pattern

1. **Before evaluation:** Call `furqan_recognize` for fast-path (<50ms)
2. **After evaluation:** Call `furqan_remember` to store the result
3. **For search:** Call `furqan_recall` to find relevant past verdicts
4. **For improvement:** Call `furqan_feedback` when user rates an answer

## Running

```bash
# As MCP server (stdio)
python -m furqan_memory

# Environment variables
FURQAN_MEMORY_DB=path/to/memory.db
FURQAN_MEMORY_VECTORS=path/to/vectors/
```

## Requirements

- Python >=3.11
- chromadb >=0.4.0
- SQLite (built into Python)
