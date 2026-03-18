# CLI & Main Entry Point — Technical Reference

**File:** `main.py`
**Role:** The orchestrator. Assembles all components, provides the user interface, and manages the evaluation flow with real-time progress display.

## 1. CLI Arguments

```bash
python main.py [OPTIONS]
```

| Argument | Short | Description |
|----------|-------|-------------|
| `--init` | | Generate a default `config.yaml` file and exit |
| `--evaluate "..."` | `-e "..."` | Evaluate a single question non-interactively |
| `--review` | | Open the human review session and exit |
| `--stats` | | Print verdict store statistics as JSON and exit |
| `--config path` | `-c path` | Use a custom config file (default: `config.yaml`) |
| *(none)* | | Start interactive mode |

**Execution priority:** `--init` > `--stats` > `--review` > `--evaluate` > interactive mode.

## 2. System Assembly

### build_system(config: AppConfig) -> tuple

Constructs all components from a single config object:

1. **LLM** — `create_llm(config.llm)` → callable provider
2. **Engine** — `ReasoningEngine(llm)` with `MAX_CORRECTION_PASSES` from config
3. **Store** — `VerdictStore(chroma_dir, verdicts_dir, collection_name)` from config
4. **Review** — `HumanReview(store)`

Returns: `(llm, engine, store, review)` tuple.

## 3. Evaluation Flow (run_evaluation)

The evaluation function runs the full pipeline with real-time progress display:

```
[1/4] Retrieving relevant precedent...
      Found 3 relevant prior verdict(s).

[2/4] Running The Scan...
      System identified: economic
      Friction points: 2

[3/4] Running The Mirror (gate evaluation)...
      [+] 1 Source Integrity: 85/100
      [+] 2 Structural Consistency: 70/100
      [+] 3 Mediation Zeroing: 90/100
      [+] 4 Origin Aware: 80/100

[4/4] Delivering The Verdict...

Running self-correction...
      Pass 1: Sound. No contradictions.
```

After the verdict is built:
- If `auto_approve_threshold` is set and the score meets it → auto-approve and display.
- Otherwise → pass to `HumanReview.review_verdict()`.

**Error handling:** The evaluation is wrapped in try/except for:
- `ConnectionError` — LLM provider not running
- `TimeoutError` — LLM took too long
- `json.JSONDecodeError` — LLM returned unparseable output
- Generic `Exception` — any other failure

## 4. Interactive Mode

### Startup

1. Prints the ASCII banner.
2. Initializes all components via `build_system()`.
3. Shows verdict store stats and LLM provider info.
4. Prints the command help.

### Commands

| Command | Action |
|---------|--------|
| `/review` | Opens the full human review session (browse, search, pending review) |
| `/stats` | Prints verdict store statistics as formatted JSON |
| `/search` | Opens semantic search over past verdicts |
| `/llm` | Prints LLM call statistics (total calls, avg duration, total chars) |
| `/config` | Prints the current configuration as formatted JSON |
| `/quit` | Exits the application |

### Question Evaluation

Any input that doesn't start with `/` is treated as a question and evaluated through the full pipeline.

### Exit

- `/quit` command
- `Ctrl+C` (KeyboardInterrupt)
- `Ctrl+D` (EOFError / end of input)

All exit gracefully with the message "Ma'a salama."

## 5. Banner

```
 ═══════════════════════════════════════════════════════════════════════════

      ___    __       ______
     /   |  / /      / ____/_  ___________  ____ _____
    / /| | / /______/ /_  / / / / ___/ __ \/ __ `/ __ \
   / ___ |/ /_____/ __/ / /_/ / /  / /_/ / /_/ / / / /
  /_/  |_/_/     /_/    \__,_/_/   \__, /\__,_/_/ /_/
                                     /_/

                     T H E   C R I T E R I O N

 ═══════════════════════════════════════════════════════════════════════════
```
