# Furqan Memory

**Client-side memory and learning skill for AI agents.**

Stores verdicts, learns patterns, enables offline reasoning. All data stays on the user's device.

## Features

- **Remember** — Store evaluation verdicts in local SQLite + vector search
- **Recall** — Semantic search over past verdicts
- **Recognize** — Fast-path pattern matching (<50ms target)
- **Feedback** — Rate verdicts to improve pattern accuracy
- **Stats** — Memory usage dashboard

## Architecture

```
furqan-memory/
├── src/furqan_memory/
│   ├── storage/
│   │   ├── sqlite_store.py    # SQLite structured storage
│   │   └── vector_store.py    # ChromaDB semantic search
│   ├── memory_manager.py      # Core orchestration
│   └── mcp_server.py          # MCP JSON-RPC server
├── tests/
│   ├── test_sqlite_store.py
│   ├── test_vector_search.py
│   ├── test_memory_manager.py
│   └── test_mcp_memory.py
└── SKILL.md
```

## Storage Schema

### verdicts
| Column | Type | Description |
|--------|------|-------------|
| id | TEXT PK | Verdict ID (v_xxxx) |
| question | TEXT | Original question |
| domain | TEXT | Knowledge domain |
| verdict_json | TEXT | Full verdict data as JSON |
| total_score | INTEGER | Overall score |
| gate_results | TEXT | Gate scores as JSON |
| final_judgment | TEXT | Final judgment text |
| tags | TEXT | JSON array of tags |
| created_at | REAL | Unix timestamp |
| accessed_at | REAL | Last access time |
| access_count | INTEGER | Number of accesses |

### patterns
| Column | Type | Description |
|--------|------|-------------|
| id | TEXT PK | Pattern ID (p_xxxx) |
| category | TEXT | Pattern category |
| domain | TEXT | Knowledge domain |
| rule | TEXT | Pattern rule text |
| signals | TEXT | Trigger signals (JSON) |
| expected_gates | TEXT | Expected gate results (JSON) |
| confidence | REAL | Pattern confidence (0-1) |
| hit_count | INTEGER | Times matched |
| version | INTEGER | Pattern version |

### feedback
| Column | Type | Description |
|--------|------|-------------|
| id | TEXT PK | Feedback ID (f_xxxx) |
| target_id | TEXT | Verdict/pattern ID |
| target_type | TEXT | "verdict" or "pattern" |
| rating | TEXT | positive/negative/neutral |
| correction | TEXT | Optional correction |

### context
| Column | Type | Description |
|--------|------|-------------|
| key | TEXT PK | Context key |
| value | TEXT | JSON value |
| domain | TEXT | Scope domain |

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Start MCP server
python -m furqan_memory
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `furqan_remember` | Store a verdict in local memory |
| `furqan_recall` | Search memory for relevant past verdicts |
| `furqan_recognize` | Fast-path pattern matching (<50ms) |
| `furqan_feedback` | Rate a verdict to improve accuracy |
| `furqan_memory_stats` | Memory usage statistics |

## Privacy

All data stays on the user's device. No network calls. No telemetry.
