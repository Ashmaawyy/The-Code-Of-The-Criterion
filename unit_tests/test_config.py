"""
Unit tests for config.py

Tests:
- Default config values
- Config serialization (to_dict)
- Load config from YAML file
- Load config with missing file (fallback to defaults)
- Save config
- Generate default config template
"""

import sys
from pathlib import Path

import pytest

# Ensure project root is on the path so bare module imports resolve
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (
    AppConfig,
    EngineConfig,
    StoreConfig,
    ReviewConfig,
    load_config,
    save_config,
    generate_default_config,
)
from llm_layer import LLMConfig


# ---------------------------------------------------------------------------
# Default Values
# ---------------------------------------------------------------------------

class TestDefaults:
    def test_app_config_defaults(self):
        config = AppConfig()
        assert config.llm.provider == "ollama"
        assert config.llm.model_name == "mistral"
        assert config.engine.max_correction_passes == 5
        assert config.store.collection_name == "criterion_verdicts"
        assert config.store.default_retrieval_count == 5
        assert config.review.auto_approve_threshold is None
        assert config.review.show_reasoning_detail is True
        assert config.review.max_browse_count == 20

    def test_engine_config_defaults(self):
        config = EngineConfig()
        assert config.max_correction_passes == 5

    def test_store_config_defaults(self):
        config = StoreConfig()
        assert config.collection_name == "criterion_verdicts"
        assert config.default_retrieval_count == 5

    def test_review_config_defaults(self):
        config = ReviewConfig()
        assert config.auto_approve_threshold is None
        assert config.show_reasoning_detail is True


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

class TestSerialization:
    def test_to_dict(self):
        config = AppConfig()
        d = config.to_dict()
        assert "llm" in d
        assert "engine" in d
        assert "store" in d
        assert "review" in d
        assert d["llm"]["provider"] == "ollama"
        assert d["engine"]["max_correction_passes"] == 5

    def test_to_dict_custom_values(self):
        config = AppConfig(
            llm=LLMConfig(provider="transformers", model_name="llama3"),
            engine=EngineConfig(max_correction_passes=10),
        )
        d = config.to_dict()
        assert d["llm"]["provider"] == "transformers"
        assert d["llm"]["model_name"] == "llama3"
        assert d["engine"]["max_correction_passes"] == 10


# ---------------------------------------------------------------------------
# Load Config
# ---------------------------------------------------------------------------

class TestLoadConfig:
    def test_load_missing_file_returns_defaults(self, tmp_path):
        config = load_config(tmp_path / "nonexistent.yaml")
        assert config.llm.provider == "ollama"
        assert config.engine.max_correction_passes == 5

    def test_load_from_yaml(self, tmp_path):
        yaml_content = """
llm:
  provider: transformers
  model_name: llama3
  temperature: 0.5
engine:
  max_correction_passes: 10
store:
  collection_name: test_collection
review:
  auto_approve_threshold: 90
"""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml_content)
        config = load_config(config_path)
        assert config.llm.provider == "transformers"
        assert config.llm.model_name == "llama3"
        assert config.llm.temperature == 0.5
        assert config.engine.max_correction_passes == 10
        assert config.store.collection_name == "test_collection"
        assert config.review.auto_approve_threshold == 90

    def test_load_partial_yaml(self, tmp_path):
        yaml_content = """
llm:
  model_name: qwen2.5
"""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml_content)
        config = load_config(config_path)
        assert config.llm.model_name == "qwen2.5"
        # Other values should be defaults
        assert config.llm.provider == "ollama"
        assert config.engine.max_correction_passes == 5

    def test_load_empty_yaml(self, tmp_path):
        config_path = tmp_path / "config.yaml"
        config_path.write_text("")
        config = load_config(config_path)
        assert config.llm.provider == "ollama"

    def test_load_ignores_unknown_keys(self, tmp_path):
        yaml_content = """
llm:
  provider: ollama
  unknown_key: value
engine:
  max_correction_passes: 3
  fake_field: 42
"""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml_content)
        config = load_config(config_path)
        assert config.llm.provider == "ollama"
        assert config.engine.max_correction_passes == 3


# ---------------------------------------------------------------------------
# Save Config
# ---------------------------------------------------------------------------

class TestSaveConfig:
    def test_save_and_reload(self, tmp_path):
        config = AppConfig(
            llm=LLMConfig(provider="transformers", model_name="test_model"),
            engine=EngineConfig(max_correction_passes=7),
        )
        config_path = tmp_path / "config.yaml"
        save_config(config, config_path)
        assert config_path.exists()

        reloaded = load_config(config_path)
        assert reloaded.llm.provider == "transformers"
        assert reloaded.llm.model_name == "test_model"
        assert reloaded.engine.max_correction_passes == 7


# ---------------------------------------------------------------------------
# Generate Default Config
# ---------------------------------------------------------------------------

class TestGenerateDefaultConfig:
    def test_generates_file(self, tmp_path):
        config_path = tmp_path / "config.yaml"
        generate_default_config(config_path)
        assert config_path.exists()

    def test_generated_file_contains_sections(self, tmp_path):
        config_path = tmp_path / "config.yaml"
        generate_default_config(config_path)
        content = config_path.read_text()
        assert "llm:" in content
        assert "engine:" in content
        assert "store:" in content
        assert "review:" in content
        assert "provider: ollama" in content

    def test_generated_file_is_loadable(self, tmp_path):
        config_path = tmp_path / "config.yaml"
        generate_default_config(config_path)
        config = load_config(config_path)
        assert config.llm.provider == "ollama"
        assert config.engine.max_correction_passes == 5
