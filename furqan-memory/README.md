# Furqan Memory

Client-side memory and learning MCP server for Al-Furqan-compatible agents.
It stores verdict-shaped records locally, recalls related past judgments, learns
patterns, and records feedback without sending data to a network service.

This package is deliberately separate from the core engine:

```text
MCP client
  -> JSON-RPC over stdio
  -> FurqanMemoryMCPServer
  -> MemoryManager
  -> SQLite structured store
  -> ChromaDB vector collections
```

The core Al-Furqan runtime uses Elasticsearch for verdict and feedback storage.
`furqan-memory/` is different by design: it is a local agent memory cache that
stays on the user's device.

---

## Capabilities

| Capability | Tool | Backing layer |
| --- | --- | --- |
| Store a verdict | `furqan_remember` | SQLite verdict table + Chroma verdict vector |
| Recall related verdicts | `furqan_recall` | Chroma semantic search enriched from SQLite |
| Recognize mature patterns | `furqan_recognize` | Chroma pattern vector + SQLite confidence gate |
| Record feedback | `furqan_feedback` | SQLite feedback table and pattern confidence update |
| Inspect local usage | `furqan_memory_stats` | SQLite counts + Chroma collection counts |

---

## Package Layout

```text
furqan-memory/
  src/furqan_memory/
    __main__.py
    mcp_server.py              JSON-RPC/MCP stdio server
    memory_manager.py          Coordinates structured and vector storage
    storage/
      sqlite_store.py          Verdicts, patterns, feedback, context
      vector_store.py          ChromaDB verdict/pattern collections
  tests/
    test_mcp_memory.py
    test_memory_manager.py
    test_sqlite_store.py
    test_vector_search.py
  pyproject.toml
  SKILL.md
```

---

## Local Storage Model

SQLite tables are created automatically:

| Table | Purpose |
| --- | --- |
| `verdicts` | Original question, domain, verdict JSON, score, gate results, tags, access metadata |
| `patterns` | Learned recognition rules, signals, expected gates, confidence, source verdicts, hit counts |
| `feedback` | Positive/negative/neutral ratings and optional corrections |
| `context` | Domain-scoped key/value context |

ChromaDB keeps two collections:

| Collection | Purpose |
| --- | --- |
| `verdicts` | Semantic recall over stored questions/verdicts |
| `patterns` | Fast recognition of mature patterns |

The recognition path only returns a match when vector similarity clears the
requested threshold and the stored pattern confidence is at least `0.8`.

---

## Quick Start

From this package directory:

```bash
pip install -e ".[dev]"
pytest tests/ -v
python -m furqan_memory
```

From the repository root:

```bash
python -m pytest furqan-memory/tests/ -v
```

Runtime paths can be controlled with environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `FURQAN_MEMORY_DB` | `furqan_memory.db` | SQLite database path |
| `FURQAN_MEMORY_VECTORS` | unset | ChromaDB persistence directory; unset is ephemeral |

Example:

```bash
FURQAN_MEMORY_DB=~/.al-furqan/memory.db \
FURQAN_MEMORY_VECTORS=~/.al-furqan/memory_vectors \
python -m furqan_memory.mcp_server
```

On Windows PowerShell:

```powershell
$env:FURQAN_MEMORY_DB = "$HOME\.al-furqan\memory.db"
$env:FURQAN_MEMORY_VECTORS = "$HOME\.al-furqan\memory_vectors"
python -m furqan_memory.mcp_server
```

---

## MCP Client Configuration

Use the package module as a stdio server:

```json
{
  "mcpServers": {
    "furqan-memory": {
      "command": "python",
      "args": ["-m", "furqan_memory.mcp_server"],
      "cwd": "/path/to/al-furqan/furqan-memory"
    }
  }
}
```

---

## Tool Arguments

| Tool | Required arguments | Optional arguments |
| --- | --- | --- |
| `furqan_remember` | `question`, `verdict` | `domain`, `tags` |
| `furqan_recall` | `query` | `domain`, `limit` |
| `furqan_recognize` | `query` | `threshold` |
| `furqan_feedback` | `verdict_id`, `rating` | `correction` |
| `furqan_memory_stats` | none | `domain` |

Ratings for `furqan_feedback` are `positive`, `negative`, or `neutral`.

---

## Privacy Boundary

- No network call is made by the SQLite store.
- ChromaDB runs locally; persistence is controlled by `FURQAN_MEMORY_VECTORS`.
- The server does not import the core Al-Furqan engine and does not evaluate
  claims itself. It stores, retrieves, and learns from verdict-shaped data.
