# Furqan RaaS — Reasoning-as-a-Skill

MCP-compatible reasoning server that exposes the Al-Furqan axiom-anchored evaluation engine via JSON-RPC 2.0 over stdio.

## Quick Start

```bash
# From the al-furqan project root
python -m furqan_raas.mcp_server
```

The server reads JSON-RPC requests from stdin and writes responses to stdout.

## Available Tools

| Tool | Description |
|------|-------------|
| `furqan_evaluate` | Full 4-gate evaluation with Z3 formal proof |
| `furqan_verify` | Quick claim verification against knowledge base |
| `furqan_retrieve` | Search verified knowledge bases (Quran, Hadith, Fiqh) |
| `furqan_explain` | Get sourced explanation grounded in verified sources |
| `furqan_domains` | List available knowledge domains |

## Example

```json
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"furqan_evaluate","arguments":{"question":"Is charity obligatory in Islam?"}}}
```

Response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{
      "type": "text",
      "text": "{\"type\":\"evaluation\",\"response\":\"...\",\"verdict\":{\"gate_scores\":[...],\"total_score\":82},\"sources\":[...],\"evaluation_id\":\"eval_abc123\"}"
    }]
  }
}
```

## MCP Configuration

Add to your MCP client config (e.g., Claude Code):

```json
{
  "mcpServers": {
    "furqan-reasoning": {
      "command": "python",
      "args": ["-m", "furqan_raas.mcp_server"],
      "cwd": "/path/to/al-furqan/furqan-raas/src"
    }
  }
}
```

## Architecture

```
furqan-raas/          ← This package (thin MCP wrapper)
  └── imports from →
src/al_furqan/        ← Core engine (gates, pipeline, KB, Z3)
```

The RaaS layer does NOT duplicate engine code — it imports and wraps existing modules.

## Running Tests

```bash
cd /path/to/al-furqan
python -m pytest furqan-raas/tests/ -v
```
