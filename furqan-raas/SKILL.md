---
name: furqan-reasoning
description: Axiom-anchored reasoning engine with formal Z3 verification. Evaluates claims against verified sources with deterministic scoring.
---

# Furqan Reasoning Skill

## Commands

- `furqan_evaluate` — Full evaluation through 4 survival gates (Source-Integrity, Structural-Consistency, Mediation-Zeroing, Origin-Aware) with optional Z3 formal proof
- `furqan_verify` — Quick claim verification against Quran, Hadith, and Fiqh sources with confidence scoring
- `furqan_retrieve` — Search verified knowledge bases and return formatted citations
- `furqan_explain` — Get a sourced explanation of a topic grounded in verified knowledge
- `furqan_domains` — List available knowledge domains and their statistics

## Transport

JSON-RPC 2.0 over stdio. Start with:

```bash
python -m furqan_raas.mcp_server
```

## Evaluation Depths

- `quick` — Gate evaluation only (no Z3 verification)
- `standard` — Gates + Z3 verification (default)
- `deep` — Gates + Z3 + extended self-correction passes

## Safety

- Harmful queries are automatically refused
- Informational questions get direct answers (no gate overhead)
- Evaluative claims go through the full 4-gate pipeline
