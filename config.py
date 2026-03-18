"""
Al-Furqan Configuration

Central configuration for the entire system. Loads from a YAML config file
if present, otherwise uses sensible defaults.

Config file location: config.yaml in the project root.
"""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from llm_layer import LLMConfig


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"
DEFAULT_VERDICTS_DIR = PROJECT_ROOT / "verdicts"
DEFAULT_CHROMA_DIR = PROJECT_ROOT / ".chroma_db"


# ---------------------------------------------------------------------------
# Sub-Configs
# ---------------------------------------------------------------------------

@dataclass
class EngineConfig:
    """Configuration for the reasoning engine."""
    max_correction_passes: int = 5


@dataclass
class StoreConfig:
    """Configuration for the verdict store."""
    verdicts_dir: str = str(DEFAULT_VERDICTS_DIR)
    chroma_dir: str = str(DEFAULT_CHROMA_DIR)
    collection_name: str = "criterion_verdicts"
    default_retrieval_count: int = 5


@dataclass
class ReviewConfig:
    """Configuration for the human review interface."""
    auto_approve_threshold: Optional[int] = None  # score above which verdicts auto-approve (None = always review)
    show_reasoning_detail: bool = True             # show full gate reasoning in display
    max_browse_count: int = 20                     # max verdicts shown when browsing


# ---------------------------------------------------------------------------
# Master Config
# ---------------------------------------------------------------------------

@dataclass
class AppConfig:
    """Master configuration for the Al-Furqan system."""
    llm: LLMConfig = field(default_factory=LLMConfig)
    engine: EngineConfig = field(default_factory=EngineConfig)
    store: StoreConfig = field(default_factory=StoreConfig)
    review: ReviewConfig = field(default_factory=ReviewConfig)

    def to_dict(self) -> dict:
        return {
            "llm": asdict(self.llm),
            "engine": asdict(self.engine),
            "store": asdict(self.store),
            "review": asdict(self.review),
        }


# ---------------------------------------------------------------------------
# Load / Save
# ---------------------------------------------------------------------------

def load_config(path: Optional[Path] = None) -> AppConfig:
    """
    Load configuration from a YAML file.
    Falls back to defaults if the file doesn't exist.
    """
    config_path = path or DEFAULT_CONFIG_PATH

    if not config_path.exists():
        return AppConfig()

    try:
        import yaml
    except ImportError:
        print("  Warning: PyYAML not installed. Using default config.")
        print("  Install with: pip install pyyaml")
        return AppConfig()

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    # Build config from YAML sections
    llm_data = raw.get("llm", {})
    engine_data = raw.get("engine", {})
    store_data = raw.get("store", {})
    review_data = raw.get("review", {})

    llm_config = LLMConfig(**{
        k: v for k, v in llm_data.items()
        if k in LLMConfig.__dataclass_fields__
    })

    engine_config = EngineConfig(**{
        k: v for k, v in engine_data.items()
        if k in EngineConfig.__dataclass_fields__
    })

    store_config = StoreConfig(**{
        k: v for k, v in store_data.items()
        if k in StoreConfig.__dataclass_fields__
    })

    review_config = ReviewConfig(**{
        k: v for k, v in review_data.items()
        if k in ReviewConfig.__dataclass_fields__
    })

    return AppConfig(
        llm=llm_config,
        engine=engine_config,
        store=store_config,
        review=review_config,
    )


def save_config(config: AppConfig, path: Optional[Path] = None) -> None:
    """Save configuration to a YAML file."""
    config_path = path or DEFAULT_CONFIG_PATH

    try:
        import yaml
    except ImportError:
        # Fall back to JSON if PyYAML not available
        json_path = config_path.with_suffix(".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, indent=2)
        print(f"  Config saved as JSON (install pyyaml for YAML): {json_path}")
        return

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(
            config.to_dict(),
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )


def generate_default_config(path: Optional[Path] = None) -> None:
    """Generate a default config file with comments for documentation."""
    config_path = path or DEFAULT_CONFIG_PATH

    template = """# =============================================================================
# Al-Furqan (The Criterion) — Configuration
# =============================================================================

# --- LLM Provider -----------------------------------------------------------
# provider: ollama | transformers | openai_compatible
# For Ollama:    ollama pull <model_name>, then ollama serve
# For Transformers: pip install torch transformers (+ bitsandbytes for quantization)
# For OpenAI-compatible: any server with /v1/chat/completions endpoint
llm:
  provider: ollama
  model_name: mistral
  base_url: "http://localhost:11434"
  temperature: 0.1
  max_tokens: 4096
  top_p: 0.9
  repeat_penalty: 1.1
  timeout: 300
  system_prompt: ""
  device: auto           # transformers only: auto, cpu, cuda, mps
  quantization: null     # transformers only: 4bit, 8bit, or null

# --- Reasoning Engine --------------------------------------------------------
engine:
  max_correction_passes: 5

# --- Verdict Store -----------------------------------------------------------
store:
  verdicts_dir: "verdicts"
  chroma_dir: ".chroma_db"
  collection_name: criterion_verdicts
  default_retrieval_count: 5

# --- Human Review ------------------------------------------------------------
review:
  auto_approve_threshold: null   # set to an integer (e.g. 90) to auto-approve high-score verdicts
  show_reasoning_detail: true
  max_browse_count: 20
"""

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(template)

    print(f"  Default config generated: {config_path}")
