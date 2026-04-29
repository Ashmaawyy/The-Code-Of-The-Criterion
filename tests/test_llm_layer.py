"""
Unit tests for llm_layer.py

Tests:
- LLMConfig defaults and construction
- LLMProvider base class behavior (call logging, stats)
- Factory function (create_llm, create_llm_from_dict)
- Provider registration
- Error handling for unknown providers

Note: Actual API calls to Ollama/Transformers/OpenAI are NOT tested here.
Those require integration tests with running services.
"""

import logging
import time

import pytest

from al_furqan.providers.llm_layer import (
    LLMConfig,
    LLMCallLog,
    LLMProvider,
    OllamaProvider,
    TransformersProvider,
    OpenAICompatibleProvider,
    PROVIDERS,
    create_llm,
    create_llm_from_dict,
)

logger = logging.getLogger("test_llm_layer")


# ---------------------------------------------------------------------------
# LLMConfig
# ---------------------------------------------------------------------------

class TestLLMConfig:
    """TestLLMConfig class."""
    def test_defaults(self):
        """Test defaults."""
        logger.info("Creating LLMConfig with all defaults")
        config = LLMConfig()
        logger.debug("provider=%s, model_name=%s, temperature=%s, max_tokens=%d",
                      config.provider, config.model_name, config.temperature, config.max_tokens)
        logger.debug("base_url=%s, device=%s, quantization=%s",
                      config.base_url, config.device, config.quantization)
        assert config.provider == "ollama"
        assert config.model_name == "mistral"
        assert config.temperature == 0.1
        assert config.max_tokens == 4096
        assert config.base_url == "http://localhost:11434"
        assert config.device == "auto"
        assert config.quantization is None
        logger.info("All LLMConfig defaults verified")

    def test_custom_values(self):
        """Test custom_values."""
        logger.info("Creating LLMConfig with custom values (transformers, llama3, 4bit)")
        config = LLMConfig(
            provider="transformers",
            model_name="meta-llama/Llama-3.1-8B",
            temperature=0.5,
            quantization="4bit",
        )
        logger.debug("provider=%s, model_name=%s, temperature=%s, quantization=%s",
                      config.provider, config.model_name, config.temperature, config.quantization)
        assert config.provider == "transformers"
        assert config.model_name == "meta-llama/Llama-3.1-8B"
        assert config.temperature == 0.5
        assert config.quantization == "4bit"
        logger.info("Custom LLMConfig values verified")


# ---------------------------------------------------------------------------
# LLMCallLog
# ---------------------------------------------------------------------------

class TestLLMCallLog:
    """TestLLMCallLog class."""
    def test_to_dict(self):
        """Test to_dict."""
        logger.info("Creating LLMCallLog with known values")
        log = LLMCallLog(
            prompt_length=500,
            response_length=200,
            duration_seconds=1.234,
            model="mistral",
            provider="ollama",
            timestamp=1700000000.0,
        )
        d = log.to_dict()
        logger.debug("Serialized call log: %s", d)
        assert d["prompt_length"] == 500
        assert d["response_length"] == 200
        assert d["duration_seconds"] == 1.23  # rounded to 2 decimals
        assert d["model"] == "mistral"
        logger.info("LLMCallLog serialization verified (duration rounded to 2dp)")

    def test_auto_timestamp(self):
        """Test auto_timestamp."""
        logger.info("Testing auto-timestamp on LLMCallLog")
        before = time.time()
        log = LLMCallLog(100, 50, 0.5, "model", "provider")
        after = time.time()
        logger.debug("before=%.3f, log.timestamp=%.3f, after=%.3f", before, log.timestamp, after)
        assert before <= log.timestamp <= after
        logger.info("Auto-timestamp falls within expected window")


# ---------------------------------------------------------------------------
# LLMProvider Base Class
# ---------------------------------------------------------------------------

class MockProvider(LLMProvider):
    """Concrete test provider that returns a fixed string."""

    def generate(self, prompt: str) -> str:
        return f"Response to: {prompt[:20]}"


class TestLLMProviderBase:
    """TestLLMProviderBase class."""
    def test_callable_interface(self):
        """Test callable_interface."""
        logger.info("Testing LLMProvider __call__ interface via MockProvider")
        config = LLMConfig()
        provider = MockProvider(config)
        result = provider("test prompt")
        logger.debug("Input: 'test prompt' → Output: '%s'", result)
        assert result == "Response to: test prompt"
        logger.info("Callable interface works correctly")

    def test_call_logging(self):
        """Test call_logging."""
        logger.info("Testing call log accumulation over 2 calls")
        config = LLMConfig()
        provider = MockProvider(config)
        provider("first call")
        provider("second call")
        logger.debug("call_log length=%d", len(provider.call_log))
        logger.debug("Call 1: prompt_length=%d, Call 2: prompt_length=%d",
                      provider.call_log[0].prompt_length, provider.call_log[1].prompt_length)
        assert len(provider.call_log) == 2
        assert provider.call_log[0].prompt_length == len("first call")
        assert provider.call_log[1].prompt_length == len("second call")
        logger.info("Call logging captured both calls with correct prompt lengths")

    def test_call_log_duration(self):
        """Test call_log_duration."""
        logger.info("Testing call log records non-negative duration")
        config = LLMConfig()
        provider = MockProvider(config)
        provider("test")
        duration = provider.call_log[0].duration_seconds
        logger.debug("Recorded duration=%.4f seconds", duration)
        assert duration >= 0
        logger.info("Duration is non-negative: %.4fs", duration)

    def test_get_stats_empty(self):
        """Test get_stats_empty."""
        logger.info("Testing stats on fresh provider (no calls)")
        config = LLMConfig()
        provider = MockProvider(config)
        stats = provider.get_stats()
        logger.debug("Empty stats: %s", stats)
        assert stats["total_calls"] == 0
        logger.info("Empty provider correctly reports 0 calls")

    def test_get_stats_with_calls(self):
        """Test get_stats_with_calls."""
        logger.info("Testing stats after 3 calls")
        config = LLMConfig()
        provider = MockProvider(config)
        provider("call 1")
        provider("call 2")
        provider("call 3")
        stats = provider.get_stats()
        logger.debug("Stats after 3 calls: %s", stats)
        assert stats["total_calls"] == 3
        assert stats["total_prompt_chars"] == len("call 1") + len("call 2") + len("call 3")
        assert stats["model"] == "mistral"
        assert stats["provider"] == "ollama"
        assert "avg_duration_seconds" in stats
        assert "total_duration_seconds" in stats
        logger.info("Stats correct: %d calls, %d total prompt chars",
                     stats["total_calls"], stats["total_prompt_chars"])


# ---------------------------------------------------------------------------
# Factory Functions
# ---------------------------------------------------------------------------

class TestFactory:
    """TestFactory class."""
    def test_create_llm_ollama(self):
        """Test create_llm_ollama."""
        logger.info("Creating LLM with provider='ollama'")
        config = LLMConfig(provider="ollama")
        provider = create_llm(config)
        logger.debug("Returned type: %s", type(provider).__name__)
        assert isinstance(provider, OllamaProvider)
        logger.info("Factory returned OllamaProvider")

    def test_create_llm_transformers(self):
        """Test create_llm_transformers."""
        logger.info("Creating LLM with provider='transformers'")
        config = LLMConfig(provider="transformers")
        provider = create_llm(config)
        logger.debug("Returned type: %s", type(provider).__name__)
        assert isinstance(provider, TransformersProvider)
        logger.info("Factory returned TransformersProvider")

    def test_create_llm_openai_compatible(self):
        """Test create_llm_openai_compatible."""
        logger.info("Creating LLM with provider='openai_compatible'")
        config = LLMConfig(provider="openai_compatible")
        provider = create_llm(config)
        logger.debug("Returned type: %s", type(provider).__name__)
        assert isinstance(provider, OpenAICompatibleProvider)
        logger.info("Factory returned OpenAICompatibleProvider")

    def test_create_llm_default_config(self):
        """Test create_llm_default_config."""
        logger.info("Creating LLM with no config (should default to ollama)")
        provider = create_llm()
        logger.debug("Returned type: %s", type(provider).__name__)
        assert isinstance(provider, OllamaProvider)
        logger.info("Default factory returned OllamaProvider")

    def test_create_llm_unknown_provider(self):
        """Test create_llm_unknown_provider."""
        logger.info("Attempting to create LLM with unknown provider='nonexistent'")
        config = LLMConfig(provider="nonexistent")
        with pytest.raises(ValueError, match="Unknown provider"):
            create_llm(config)
        logger.info("ValueError raised as expected for unknown provider")

    def test_create_llm_from_dict(self):
        """Test create_llm_from_dict."""
        d = {"provider": "ollama", "model_name": "llama3.1", "temperature": 0.3}
        logger.info("Creating LLM from dict: %s", d)
        provider = create_llm_from_dict(d)
        logger.debug("Returned type=%s, model=%s, temp=%s",
                      type(provider).__name__, provider.config.model_name, provider.config.temperature)  # pylint: disable=line-too-long
        assert isinstance(provider, OllamaProvider)
        assert provider.config.model_name == "llama3.1"
        assert provider.config.temperature == 0.3
        logger.info("LLM from dict created with correct config")

    def test_create_llm_from_dict_ignores_extra_keys(self):
        """Test create_llm_from_dict_ignores_extra_keys."""
        d = {"provider": "ollama", "unknown_key": "value"}
        logger.info("Creating LLM from dict with extra key 'unknown_key'")
        provider = create_llm_from_dict(d)
        logger.debug("Returned type: %s (extra keys silently ignored)", type(provider).__name__)
        assert isinstance(provider, OllamaProvider)
        logger.info("Extra dict keys ignored correctly")

    def test_create_llm_from_empty_dict(self):
        """Test create_llm_from_empty_dict."""
        logger.info("Creating LLM from empty dict (should use all defaults)")
        provider = create_llm_from_dict({})
        logger.debug("Returned type: %s", type(provider).__name__)
        assert isinstance(provider, OllamaProvider)  # defaults
        logger.info("Empty dict correctly produced default OllamaProvider")


# ---------------------------------------------------------------------------
# Provider Registration
# ---------------------------------------------------------------------------

class TestProviderRegistry:
    """TestProviderRegistry class."""
    def test_all_providers_registered(self):
        """Test all_providers_registered."""
        logger.info("Checking PROVIDERS registry contains all 3 providers")
        logger.debug("Registered providers: %s", list(PROVIDERS.keys()))
        assert "ollama" in PROVIDERS
        assert "transformers" in PROVIDERS
        assert "openai_compatible" in PROVIDERS
        assert len(PROVIDERS) >= 3
        logger.info("All providers registered: %s", list(PROVIDERS.keys()))

    def test_providers_are_subclasses(self):
        """Test providers_are_subclasses."""
        logger.info("Verifying all registered providers are LLMProvider subclasses")
        for name, cls in PROVIDERS.items():
            is_subclass = issubclass(cls, LLMProvider)
            logger.debug("  %s → %s (is LLMProvider subclass: %s)", name, cls.__name__, is_subclass)
            assert is_subclass, f"{name} is not an LLMProvider subclass"
        logger.info("All providers are valid LLMProvider subclasses")
