# Configuration — Technical Reference

**File:** `config.py`
**Role:** Centralizes all settings for the entire system. Loads from YAML, falls back to defaults.

## 1. Config File

**Location:** `config.yaml` in the project root.
**Format:** YAML (requires `pyyaml` package).
**Fallback:** If the file doesn't exist or PyYAML isn't installed, all settings use hardcoded defaults. The system works with zero configuration.

### Generate a default config file:

```bash
python main.py --init
```

This creates a fully commented `config.yaml` with all options documented inline.

## 2. Configuration Sections

### LLMConfig

Defined in `llm_layer.py`, imported by `config.py`.

```yaml
llm:
  provider: ollama                # ollama | transformers | openai_compatible
  model_name: mistral             # model identifier
  base_url: "http://localhost:11434"  # API base URL
  temperature: 0.1                # low for deterministic reasoning
  max_tokens: 4096                # max output tokens
  top_p: 0.9                     # nucleus sampling
  repeat_penalty: 1.1            # repetition penalty
  timeout: 300                   # request timeout (seconds)
  system_prompt: ""              # optional system prompt override
  device: auto                   # transformers only: auto, cpu, cuda, mps
  quantization: null             # transformers only: 4bit, 8bit, null
```

### EngineConfig

```yaml
engine:
  max_correction_passes: 5       # self-correction iterations (1-10)
```

### StoreConfig

```yaml
store:
  verdicts_dir: "verdicts"       # path to verdict JSON files
  chroma_dir: ".chroma_db"       # path to ChromaDB data
  collection_name: criterion_verdicts  # ChromaDB collection name
  default_retrieval_count: 5     # how many prior verdicts to retrieve
```

### ReviewConfig

```yaml
review:
  auto_approve_threshold: null   # set to integer (e.g., 90) to auto-approve
  show_reasoning_detail: true    # show full gate reasoning in display
  max_browse_count: 20           # max verdicts shown when browsing
```

**`auto_approve_threshold`**: When set to `null` (default), every verdict goes through human review. When set to an integer (e.g., `90`), verdicts with `total_score >= 90` are automatically approved and indexed without human review. This is useful as the system matures and produces consistently high-quality verdicts.

## 3. AppConfig (Master Dataclass)

```python
@dataclass
class AppConfig:
    llm: LLMConfig
    engine: EngineConfig
    store: StoreConfig
    review: ReviewConfig
```

**Methods:**
- `to_dict() -> dict` — Serializes all sections to a nested dictionary.

## 4. Functions

### load_config(path) -> AppConfig

Loads configuration from a YAML file. Falls back to defaults for any missing sections or fields. Unknown keys in the YAML are silently ignored.

**Behavior:**
1. If the file doesn't exist → return all defaults.
2. If PyYAML isn't installed → print warning, return all defaults.
3. Parse YAML → construct each sub-config, filtering to valid fields only.

### save_config(config, path)

Saves an AppConfig to a YAML file. Falls back to saving as JSON if PyYAML isn't installed.

### generate_default_config(path)

Writes a fully commented YAML template to the specified path. The template is a raw string (not generated from dataclass defaults) so that it includes helpful inline comments.

## 5. Path Defaults

| Constant | Value |
|----------|-------|
| `PROJECT_ROOT` | Directory containing `config.py` |
| `DEFAULT_CONFIG_PATH` | `<PROJECT_ROOT>/config.yaml` |
| `DEFAULT_VERDICTS_DIR` | `<PROJECT_ROOT>/verdicts/` |
| `DEFAULT_CHROMA_DIR` | `<PROJECT_ROOT>/.chroma_db/` |
