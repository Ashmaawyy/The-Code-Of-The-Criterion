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

import time

import pytest

from llm_layer import (
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


# ---------------------------------------------------------------------------
# LLMConfig
# ---------------------------------------------------------------------------

class TestLLMConfig:
    def test_defaults(self):
        config = LLMConfig()
        assert config.provider == "ollama"
        assert config.model_name == "mistral"
        assert config.temperature == 0.1
        assert config.max_tokens == 4096
        assert config.base_url == "http://localhost:11434"
        assert config.device == "auto"
        assert config.quantization is None

    def test_custom_values(self):
        config = LLMConfig(
            provider="transformers",
            model_name="meta-llama/Llama-3.1-8B",
            temperature=0.5,
            quantization="4bit",
        )
        assert config.provider == "transformers"
        assert config.model_name == "meta-llama/Llama-3.1-8B"
        assert config.temperature == 0.5
        assert config.quantization == "4bit"


# ---------------------------------------------------------------------------
# LLMCallLog
# ---------------------------------------------------------------------------

class TestLLMCallLog:
    def test_to_dict(self):
        log = LLMCallLog(
            prompt_length=500,
            response_length=200,
            duration_seconds=1.234,
            model="mistral",
            provider="ollama",
            timestamp=1700000000.0,
        )
        d = log.to_dict()
        assert d["prompt_length"] == 500
        assert d["response_length"] == 200
        assert d["duration_seconds"] == 1.23  # rounded to 2 decimals
        assert d["model"] == "mistral"

    def test_auto_timestamp(self):
        before = time.time()
        log = LLMCallLog(100, 50, 0.5, "model", "provider")
        after = time.time()
        assert before <= log.timestamp <= after


# ---------------------------------------------------------------------------
# LLMProvider Base Class
# ---------------------------------------------------------------------------

class MockProvider(LLMProvider):
    """Concrete test provider that returns a fixed string."""

    def generate(self, prompt: str) -> str:
        return f"Response to: {prompt[:20]}"


class TestLLMProviderBase:
    def test_callable_interface(self):
        config = LLMConfig()
        provider = MockProvider(config)
        result = provider("test prompt")
        assert result == "Response to: test prompt"

    def test_call_logging(self):
        config = LLMConfig()
        provider = MockProvider(config)
        provider("first call")
        provider("second call")
        assert len(provider.call_log) == 2
        assert provider.call_log[0].prompt_length == len("first call")
        assert provider.call_log[1].prompt_length == len("second call")

    def test_call_log_duration(self):
        config = LLMConfig()
        provider = MockProvider(config)
        provider("test")
        assert provider.call_log[0].duration_seconds >= 0

    def test_get_stats_empty(self):
        config = LLMConfig()
        provider = MockProvider(config)
        stats = provider.get_stats()
        assert stats["total_calls"] == 0

    def test_get_stats_with_calls(self):
        config = LLMConfig()
        provider = MockProvider(config)
        provider("call 1")
        provider("call 2")
        provider("call 3")
        stats = provider.get_stats()
        assert stats["total_calls"] == 3
        assert stats["total_prompt_chars"] == len("call 1") + len("call 2") + len("call 3")
        assert stats["model"] == "mistral"
        assert stats["provider"] == "ollama"
        assert "avg_duration_seconds" in stats
        assert "total_duration_seconds" in stats


# ---------------------------------------------------------------------------
# Factory Functions
# ---------------------------------------------------------------------------

class TestFactory:
    def test_create_llm_ollama(self):
        config = LLMConfig(provider="ollama")
        provider = create_llm(config)
        assert isinstance(provider, OllamaProvider)

    def test_create_llm_transformers(self):
        config = LLMConfig(provider="transformers")
        provider = create_llm(config)
        assert isinstance(provider, TransformersProvider)

    def test_create_llm_openai_compatible(self):
        config = LLMConfig(provider="openai_compatible")
        provider = create_llm(config)
        assert isinstance(provider, OpenAICompatibleProvider)

    def test_create_llm_default_config(self):
        provider = create_llm()
        assert isinstance(provider, OllamaProvider)

    def test_create_llm_unknown_provider(self):
        config = LLMConfig(provider="nonexistent")
        with pytest.raises(ValueError, match="Unknown provider"):
            create_llm(config)

    def test_create_llm_from_dict(self):
        d = {"provider": "ollama", "model_name": "llama3.1", "temperature": 0.3}
        provider = create_llm_from_dict(d)
        assert isinstance(provider, OllamaProvider)
        assert provider.config.model_name == "llama3.1"
        assert provider.config.temperature == 0.3

    def test_create_llm_from_dict_ignores_extra_keys(self):
        d = {"provider": "ollama", "unknown_key": "value"}
        provider = create_llm_from_dict(d)
        assert isinstance(provider, OllamaProvider)

    def test_create_llm_from_empty_dict(self):
        provider = create_llm_from_dict({})
        assert isinstance(provider, OllamaProvider)  # defaults


# ---------------------------------------------------------------------------
# Provider Registration
# ---------------------------------------------------------------------------

class TestProviderRegistry:
    def test_all_providers_registered(self):
        assert "ollama" in PROVIDERS
        assert "transformers" in PROVIDERS
        assert "openai_compatible" in PROVIDERS
        assert len(PROVIDERS) == 3

    def test_providers_are_subclasses(self):
        for name, cls in PROVIDERS.items():
            assert issubclass(cls, LLMProvider), f"{name} is not an LLMProvider subclass"
