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

import logging


from al_furqan.config import (
    AppConfig,
    EngineConfig,
    StoreConfig,
    ReviewConfig,
    load_config,
    save_config,
    generate_default_config,
)
from al_furqan.providers.llm_layer import LLMConfig

logger = logging.getLogger("test_config")


# ---------------------------------------------------------------------------
# Default Values
# ---------------------------------------------------------------------------

class TestDefaults:
    """TestDefaults class."""
    def test_app_config_defaults(self):
        """Test app_config_defaults."""
        logger.info("Creating AppConfig with all defaults")
        config = AppConfig()
        logger.debug("llm.provider=%s, llm.model_name=%s", config.llm.provider, config.llm.model_name)  # pylint: disable=line-too-long
        logger.debug("engine.max_correction_passes=%d", config.engine.max_correction_passes)
        logger.debug("store.collection_name=%s, store.default_retrieval_count=%d",
                      config.store.collection_name, config.store.default_retrieval_count)
        logger.debug("review.auto_approve_threshold=%s, review.show_reasoning_detail=%s, review.max_browse_count=%d",  # pylint: disable=line-too-long
                      config.review.auto_approve_threshold, config.review.show_reasoning_detail,
                      config.review.max_browse_count)
        assert config.llm.provider == "ollama"
        assert config.llm.model_name == "mistral"
        assert config.engine.max_correction_passes == 5
        assert config.store.collection_name == "criterion_verdicts"
        assert config.store.default_retrieval_count == 5
        assert config.review.auto_approve_threshold is None
        assert config.review.show_reasoning_detail is True
        assert config.review.max_browse_count == 20
        logger.info("All AppConfig defaults verified")

    def test_engine_config_defaults(self):
        """Test engine_config_defaults."""
        logger.info("Creating EngineConfig with defaults")
        config = EngineConfig()
        logger.debug("max_correction_passes=%d", config.max_correction_passes)
        assert config.max_correction_passes == 5
        logger.info("EngineConfig defaults verified")

    def test_store_config_defaults(self):
        """Test store_config_defaults."""
        logger.info("Creating StoreConfig with defaults")
        config = StoreConfig()
        logger.debug("collection_name=%s, default_retrieval_count=%d",
                      config.collection_name, config.default_retrieval_count)
        assert config.collection_name == "criterion_verdicts"
        assert config.default_retrieval_count == 5
        logger.info("StoreConfig defaults verified")

    def test_review_config_defaults(self):
        """Test review_config_defaults."""
        logger.info("Creating ReviewConfig with defaults")
        config = ReviewConfig()
        logger.debug("auto_approve_threshold=%s, show_reasoning_detail=%s",
                      config.auto_approve_threshold, config.show_reasoning_detail)
        assert config.auto_approve_threshold is None
        assert config.show_reasoning_detail is True
        logger.info("ReviewConfig defaults verified")


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

class TestSerialization:
    """TestSerialization class."""
    def test_to_dict(self):
        """Test to_dict."""
        logger.info("Serializing default AppConfig to dict")
        config = AppConfig()
        d = config.to_dict()
        logger.debug("Serialized keys: %s", list(d.keys()))
        logger.debug("llm section: %s", d["llm"])
        logger.debug("engine section: %s", d["engine"])
        assert "llm" in d
        assert "engine" in d
        assert "store" in d
        assert "review" in d
        assert d["llm"]["provider"] == "ollama"
        assert d["engine"]["max_correction_passes"] == 5
        logger.info("Default AppConfig serialized correctly")

    def test_to_dict_custom_values(self):
        """Test to_dict_custom_values."""
        logger.info("Serializing custom AppConfig (provider=transformers, model=llama3, passes=10)")
        config = AppConfig(
            llm=LLMConfig(provider="transformers", model_name="llama3"),
            engine=EngineConfig(max_correction_passes=10),
        )
        d = config.to_dict()
        logger.debug("Custom llm section: %s", d["llm"])
        logger.debug("Custom engine section: %s", d["engine"])
        assert d["llm"]["provider"] == "transformers"
        assert d["llm"]["model_name"] == "llama3"
        assert d["engine"]["max_correction_passes"] == 10
        logger.info("Custom AppConfig serialized correctly")


# ---------------------------------------------------------------------------
# Load Config
# ---------------------------------------------------------------------------

class TestLoadConfig:
    """TestLoadConfig class."""
    def test_load_missing_file_returns_defaults(self, tmp_path):
        """Test load_missing_file_returns_defaults."""
        missing = tmp_path / "nonexistent.yaml"
        logger.info("Loading config from missing file: %s", missing)
        config = load_config(missing)
        logger.debug("Returned provider=%s, max_correction_passes=%d",
                      config.llm.provider, config.engine.max_correction_passes)
        assert config.llm.provider == "ollama"
        assert config.engine.max_correction_passes == 5
        logger.info("Missing file correctly fell back to defaults")

    def test_load_from_yaml(self, tmp_path):
        """Test load_from_yaml."""
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
        logger.info("Loading full config from %s", config_path)
        config = load_config(config_path)
        logger.debug("Loaded: provider=%s, model=%s, temp=%s, passes=%d, collection=%s, threshold=%s",  # pylint: disable=line-too-long
                      config.llm.provider, config.llm.model_name, config.llm.temperature,
                      config.engine.max_correction_passes, config.store.collection_name,
                      config.review.auto_approve_threshold)
        assert config.llm.provider == "transformers"
        assert config.llm.model_name == "llama3"
        assert config.llm.temperature == 0.5
        assert config.engine.max_correction_passes == 10
        assert config.store.collection_name == "test_collection"
        assert config.review.auto_approve_threshold == 90
        logger.info("Full YAML config loaded and verified")

    def test_load_partial_yaml(self, tmp_path):
        """Test load_partial_yaml."""
        yaml_content = """
llm:
  model_name: qwen2.5
"""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml_content)
        logger.info("Loading partial config (only llm.model_name) from %s", config_path)
        config = load_config(config_path)
        logger.debug("Loaded model_name=%s, provider=%s (should be default), passes=%d (should be default)",  # pylint: disable=line-too-long
                      config.llm.model_name, config.llm.provider, config.engine.max_correction_passes)  # pylint: disable=line-too-long
        assert config.llm.model_name == "qwen2.5"
        # Other values should be defaults
        assert config.llm.provider == "ollama"
        assert config.engine.max_correction_passes == 5
        logger.info("Partial YAML correctly merged with defaults")

    def test_load_empty_yaml(self, tmp_path):
        """Test load_empty_yaml."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("")
        logger.info("Loading empty YAML file from %s", config_path)
        config = load_config(config_path)
        logger.debug("Returned provider=%s (expected default 'ollama')", config.llm.provider)
        assert config.llm.provider == "ollama"
        logger.info("Empty YAML correctly fell back to defaults")

    def test_load_ignores_unknown_keys(self, tmp_path):
        """Test load_ignores_unknown_keys."""
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
        logger.info("Loading YAML with unknown keys (unknown_key, fake_field) from %s", config_path)
        config = load_config(config_path)
        logger.debug("Loaded provider=%s, passes=%d — unknown keys silently ignored",
                      config.llm.provider, config.engine.max_correction_passes)
        assert config.llm.provider == "ollama"
        assert config.engine.max_correction_passes == 3
        logger.info("Unknown keys correctly ignored during load")


# ---------------------------------------------------------------------------
# Save Config
# ---------------------------------------------------------------------------

class TestSaveConfig:  # pylint: disable=too-few-public-methods
    """TestSaveConfig class."""
    def test_save_and_reload(self, tmp_path):
        """Test save_and_reload."""
        config = AppConfig(
            llm=LLMConfig(provider="transformers", model_name="test_model"),
            engine=EngineConfig(max_correction_passes=7),
        )
        config_path = tmp_path / "config.yaml"
        logger.info("Saving config to %s (provider=transformers, model=test_model, passes=7)", config_path)  # pylint: disable=line-too-long
        save_config(config, config_path)
        assert config_path.exists()
        logger.debug("File created successfully, size=%d bytes", config_path.stat().st_size)

        logger.info("Reloading saved config from %s", config_path)
        reloaded = load_config(config_path)
        logger.debug("Reloaded: provider=%s, model=%s, passes=%d",
                      reloaded.llm.provider, reloaded.llm.model_name,
                      reloaded.engine.max_correction_passes)
        assert reloaded.llm.provider == "transformers"
        assert reloaded.llm.model_name == "test_model"
        assert reloaded.engine.max_correction_passes == 7
        logger.info("Save → reload roundtrip verified")


# ---------------------------------------------------------------------------
# Generate Default Config
# ---------------------------------------------------------------------------

class TestGenerateDefaultConfig:
    """TestGenerateDefaultConfig class."""
    def test_generates_file(self, tmp_path):
        """Test generates_file."""
        config_path = tmp_path / "config.yaml"
        logger.info("Generating default config at %s", config_path)
        generate_default_config(config_path)
        assert config_path.exists()
        logger.info("Default config file generated (size=%d bytes)", config_path.stat().st_size)

    def test_generated_file_contains_sections(self, tmp_path):
        """Test generated_file_contains_sections."""
        config_path = tmp_path / "config.yaml"
        generate_default_config(config_path)
        content = config_path.read_text()
        logger.info("Checking generated config contains required sections")
        for section in ["llm:", "engine:", "store:", "review:", "provider: ollama"]:
            found = section in content
            logger.debug("Section '%s' present: %s", section, found)
            assert found
        logger.info("All required sections found in generated config")

    def test_generated_file_is_loadable(self, tmp_path):
        """Test generated_file_is_loadable."""
        config_path = tmp_path / "config.yaml"
        generate_default_config(config_path)
        logger.info("Loading generated default config from %s", config_path)
        config = load_config(config_path)
        logger.debug("Loaded from generated: provider=%s, passes=%d",
                      config.llm.provider, config.engine.max_correction_passes)
        assert config.llm.provider == "ollama"
        assert config.engine.max_correction_passes == 5
        logger.info("Generated config is valid and loadable")
