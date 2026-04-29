"""
Al-Furqan LLM Layer

The "tongue" of the system. Provides a unified interface for the reasoning
engine to call any LLM — local open-source models via Ollama, HuggingFace
Transformers, or any OpenAI-compatible API.

All providers expose the same callable signature:
    llm_call(prompt: str) -> str

This is the only interface the reasoning engine depends on.
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import logging
import os

import requests


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class LLMConfig:  # pylint: disable=too-many-instance-attributes
    """Configuration for an LLM provider."""

    provider: str = (
        "sglang"  # sglang, ollama, transformers, openai_compatible, anthropic
    )
    model_name: str = "Qwen/Qwen3.5-397B-A17B"  # model identifier
    base_url: str = (
        "http://localhost:30000"  # API base URL (SGLang / OpenAI-compatible)
    )
    api_key: str = ""  # API key (for Anthropic, OpenAI, etc.)
    temperature: float = 0.1  # low temperature for deterministic reasoning
    max_tokens: int = 4096  # max output tokens
    top_p: float = 0.9
    repeat_penalty: float = 1.1  # discourage repetition
    timeout: int = 300  # request timeout in seconds
    system_prompt: str = ""  # optional system prompt override
    device: str = "auto"  # for transformers: auto, cpu, cuda, mps
    quantization: Optional[str] = None  # for transformers: 4bit, 8bit, or None


# ---------------------------------------------------------------------------
# Call Logging
# ---------------------------------------------------------------------------


@dataclass
class LLMCallLog:
    """Log entry for a single LLM call."""

    prompt_length: int
    response_length: int
    duration_seconds: float
    model: str
    provider: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        """Convert the log entry to a dictionary."""
        return {
            "prompt_length": self.prompt_length,
            "response_length": self.response_length,
            "duration_seconds": round(self.duration_seconds, 2),
            "model": self.model,
            "provider": self.provider,
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# Base Provider
# ---------------------------------------------------------------------------


class LLMProvider(ABC):
    """Abstract base for all LLM providers."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.call_log: list[LLMCallLog] = []

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a response from the LLM. Must be implemented by subclasses."""

    def __call__(self, prompt: str) -> str:
        """
        Callable interface for the reasoning engine.
        Wraps generate() with timing and logging.
        """
        start = time.time()
        response = self.generate(prompt)
        duration = time.time() - start

        self.call_log.append(
            LLMCallLog(
                prompt_length=len(prompt),
                response_length=len(response),
                duration_seconds=duration,
                model=self.config.model_name,
                provider=self.config.provider,
            )
        )

        return response

    def get_stats(self) -> dict:
        """Return summary statistics for all calls made."""
        if not self.call_log:
            return {"total_calls": 0}

        total_duration = sum(c.duration_seconds for c in self.call_log)
        return {
            "total_calls": len(self.call_log),
            "total_duration_seconds": round(total_duration, 2),
            "avg_duration_seconds": round(total_duration / len(self.call_log), 2),
            "total_prompt_chars": sum(c.prompt_length for c in self.call_log),
            "total_response_chars": sum(c.response_length for c in self.call_log),
            "model": self.config.model_name,
            "provider": self.config.provider,
        }


# ---------------------------------------------------------------------------
# Ollama Provider
# ---------------------------------------------------------------------------


class OllamaProvider(LLMProvider):
    """
    Local LLM via Ollama.

    Ollama runs open-source models locally with a simple REST API.
    Install: https://ollama.com
    Pull a model: ollama pull mistral

    Recommended models for this framework:
    - mistral (7B)     — fast, good reasoning for its size
    - llama3.1 (8B)    — strong instruction following
    - qwen2.5 (7B/14B) — excellent at structured JSON output
    - deepseek-r1 (7B) — strong reasoning capabilities
    - gemma3 (12B)     — good balance of speed and quality
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._session = requests.Session()

    def generate(self, prompt: str) -> str:
        url = f"{self.config.base_url}/api/generate"
        payload = {
            "model": self.config.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
                "top_p": self.config.top_p,
                "repeat_penalty": self.config.repeat_penalty,
            },
        }

        if self.config.system_prompt:
            payload["system"] = self.config.system_prompt

        try:
            response = self._session.post(
                url,
                json=payload,
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")

        except requests.ConnectionError as exc:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.config.base_url}. "
                "Make sure Ollama is running (start with: ollama serve)"
            ) from exc
        except requests.Timeout as exc:
            raise TimeoutError(
                f"Ollama request timed out after {self.config.timeout}s. "
                "The model may be too large or the prompt too long."
            ) from exc
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                raise RuntimeError(
                    f"Model '{self.config.model_name}' not found. "
                    f"Pull it with: ollama pull {self.config.model_name}"
                ) from e
            raise


# ---------------------------------------------------------------------------
# HuggingFace Transformers Provider
# ---------------------------------------------------------------------------


class TransformersProvider(LLMProvider):
    """
    Local LLM via HuggingFace Transformers.

    Loads the model directly into memory. Supports quantization
    for running larger models on consumer hardware.

    Recommended models (HuggingFace IDs):
    - mistralai/Mistral-7B-Instruct-v0.3
    - meta-llama/Meta-Llama-3.1-8B-Instruct
    - Qwen/Qwen2.5-7B-Instruct
    - google/gemma-3-12b-it
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._model = None
        self._tokenizer = None

    def _load_model(self):  # pylint: disable=import-outside-toplevel
        """Lazy-load model and tokenizer on first call."""
        if self._model is not None:
            return

        try:
            import torch  # pylint: disable=import-outside-toplevel
            from transformers import AutoModelForCausalLM, AutoTokenizer  # pylint: disable=import-outside-toplevel
        except ImportError as e:
            raise ImportError(
                "TransformersProvider requires 'torch' and 'transformers' packages. "
                "Install with: pip install torch transformers"
            ) from e

        logger.info("Loading model: %s...", self.config.model_name)
        logger.info("Device: %s", self.config.device)
        if self.config.quantization:
            logger.info("Quantization: %s", self.config.quantization)

        tokenizer = AutoTokenizer.from_pretrained(
            self.config.model_name,
            trust_remote_code=True,
        )

        model_kwargs = {"trust_remote_code": True}

        # Device mapping
        if self.config.device == "auto":
            model_kwargs["device_map"] = "auto"
        elif self.config.device == "cpu":
            model_kwargs["device_map"] = "cpu"
            model_kwargs["torch_dtype"] = torch.float32
        else:
            model_kwargs["device_map"] = self.config.device

        # Quantization
        if self.config.quantization == "4bit":
            try:
                from transformers import BitsAndBytesConfig  # pylint: disable=import-outside-toplevel
            except ImportError as e:
                raise ImportError(
                    "4-bit quantization requires 'bitsandbytes'. "
                    "Install with: pip install bitsandbytes"
                ) from e
            model_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
            )
        elif self.config.quantization == "8bit":
            try:
                from transformers import BitsAndBytesConfig  # pylint: disable=import-outside-toplevel
            except ImportError as e:
                raise ImportError(
                    "8-bit quantization requires 'bitsandbytes'. "
                    "Install with: pip install bitsandbytes"
                ) from e
            model_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_8bit=True,
            )
        else:
            if self.config.device != "cpu":
                model_kwargs["torch_dtype"] = torch.float16

        model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name,
            **model_kwargs,
        )

        self._model = model
        self._tokenizer = tokenizer
        print("Model loaded.")

    def generate(self, prompt: str) -> str:
        self._load_model()

        try:
            import torch  # pylint: disable=import-outside-toplevel
        except ImportError as e:
            raise ImportError(
                "TransformersProvider requires 'torch' package. "
                "Install with: pip install torch"
            ) from e

        inputs = self._tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(self._model.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                repetition_penalty=self.config.repeat_penalty,
                do_sample=self.config.temperature > 0,
                pad_token_id=self._tokenizer.eos_token_id,
            )

        # Decode only the new tokens (skip the prompt)
        new_tokens = outputs[0][inputs["input_ids"].shape[1] :]
        return self._tokenizer.decode(new_tokens, skip_special_tokens=True)


# ---------------------------------------------------------------------------
# OpenAI-Compatible API Provider
# ---------------------------------------------------------------------------


class OpenAICompatibleProvider(LLMProvider):
    """
    Any OpenAI-compatible API endpoint.

    Works with:
    - LM Studio (local)
    - vLLM (local)
    - text-generation-webui (local)
    - Together.ai (remote)
    - Groq (remote)
    - Any server implementing the OpenAI chat completions API
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._session = requests.Session()

    def generate(self, prompt: str) -> str:
        url = f"{self.config.base_url}/v1/chat/completions"

        messages = []
        if self.config.system_prompt:
            messages.append({"role": "system", "content": self.config.system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "top_p": self.config.top_p,
        }

        try:
            response = self._session.post(
                url,
                json=payload,
                timeout=self.config.timeout,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

        except requests.ConnectionError as exc:
            raise ConnectionError(
                f"Cannot connect to API at {self.config.base_url}. "
                "Make sure the server is running."
            ) from exc
        except requests.Timeout as exc:
            raise TimeoutError(
                f"API request timed out after {self.config.timeout}s."
            ) from exc
        except (KeyError, IndexError) as exc:
            raise RuntimeError(
                f"Unexpected API response format: {response.text[:200]}"
            ) from exc


# ---------------------------------------------------------------------------
# Anthropic Provider
# ---------------------------------------------------------------------------


class AnthropicProvider(LLMProvider):
    """
    Anthropic Claude API provider.

    Uses the Anthropic Messages API directly.
    Supports Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku, etc.

    Requires an API key (set via config.api_key or ANTHROPIC_API_KEY env var).
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._api_key = config.api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not self._api_key:
            raise ValueError(
                "Anthropic API key required. Set config.api_key or ANTHROPIC_API_KEY env var."
            )
        self._session = requests.Session()
        self._session.headers.update(
            {
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
        )

    def generate(self, prompt: str) -> str:
        url = "https://api.anthropic.com/v1/messages"

        payload = {
            "model": self.config.model_name,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        # Some models don't allow both temperature and top_p
        # Only include top_p if temperature is not set (or 0)
        if self.config.temperature == 0 and self.config.top_p < 1.0:
            payload["top_p"] = self.config.top_p

        if self.config.system_prompt:
            payload["system"] = self.config.system_prompt

        try:
            response = self._session.post(
                url,
                json=payload,
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            data = response.json()
            # Anthropic returns content as a list of blocks
            content_blocks = data.get("content", [])
            text_parts = [b["text"] for b in content_blocks if b.get("type") == "text"]
            return "".join(text_parts)

        except requests.ConnectionError as exc:
            raise ConnectionError(
                "Cannot connect to Anthropic API. Check your internet connection."
            ) from exc
        except requests.Timeout as exc:
            raise TimeoutError(
                f"Anthropic API request timed out after {self.config.timeout}s."
            ) from exc
        except requests.HTTPError as e:
            status = e.response.status_code
            body = e.response.text[:300]
            if status == 401:
                raise RuntimeError("Anthropic API key is invalid.") from e
            if status == 429:
                raise RuntimeError(
                    "Anthropic rate limit exceeded. Try again later."
                ) from e
            raise RuntimeError(f"Anthropic API error ({status}): {body}") from e


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


class SGLangProvider(OpenAICompatibleProvider):
    """
    SGLang server provider for running large language models locally or remotely.

    SGLang is a fast serving framework for large language models and vision language models.
    It provides OpenAI-compatible API endpoints for chat completions and supports multimodal inputs.

    To start the server for Qwen3.5-397B-A17B model:
        python3 -m sglang.launch_server \\
            --model-path "Qwen/Qwen3.5-397B-A17B" \\
            --host 0.0.0.0 \\
            --port 30000

    The API is fully OpenAI-compatible and supports vision models with image_url content types.
    """

    def __init__(self, config: LLMConfig):
        # Set SGLang-specific defaults if not provided
        if (
            config.base_url == "http://localhost:11434"
        ):  # default Ollama URL, override for SGLang
            config.base_url = "http://localhost:30000"
        if config.model_name == "mistral":  # default model, override for SGLang
            config.model_name = "Qwen/Qwen3.5-397B-A17B"
        super().__init__(config)


class DashScopeProvider(LLMProvider):
    """
    Alibaba Cloud DashScope (Qwen) provider.

    Uses the OpenAI-compatible API endpoint.
    Supports Qwen-Max, Qwen-Plus, Qwen-Turbo, Qwen3 series, etc.
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            }
        )

    DASHSCOPE_URL = (
        "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"
    )

    def generate(self, prompt: str) -> str:
        # Use DashScope URL unless explicitly overridden (ignore default Ollama URL)
        default_base = "http://localhost:11434"
        if self.config.base_url and self.config.base_url != default_base:
            url = self.config.base_url
        else:
            url = self.DASHSCOPE_URL

        payload = {
            "model": self.config.model_name,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": [{"role": "user", "content": prompt}],
        }

        # Qwen3 models require enable_thinking to be set explicitly
        if "qwen3" in self.config.model_name:
            payload["enable_thinking"] = False

        if self.config.system_prompt:
            payload["messages"].insert(
                0, {"role": "system", "content": self.config.system_prompt}
            )

        try:
            response = self._session.post(
                url, json=payload, timeout=self.config.timeout
            )
            data = response.json()

            if response.status_code != 200:
                error_msg = data.get("error", {}).get("message", str(data))
                raise RuntimeError(
                    f"DashScope API error ({response.status_code}): {error_msg}"
                )

            return data["choices"][0]["message"]["content"]

        except requests.ConnectionError as exc:
            raise ConnectionError("Cannot connect to DashScope API.") from exc
        except requests.Timeout as exc:
            raise TimeoutError(
                f"DashScope API timed out after {self.config.timeout}s"
            ) from exc


PROVIDERS = {
    "ollama": OllamaProvider,
    "transformers": TransformersProvider,
    "openai_compatible": OpenAICompatibleProvider,
    "anthropic": AnthropicProvider,
    "dashscope": DashScopeProvider,
    "alibaba": DashScopeProvider,  # alias
    "qwen": DashScopeProvider,  # alias
    "sglang": SGLangProvider,
}


def create_llm(config: Optional[LLMConfig] = None) -> LLMProvider:
    """
    Create an LLM provider from config.

    Returns a callable that satisfies: llm_call(prompt: str) -> str

    Usage:
        config = LLMConfig(provider="ollama", model_name="mistral")
        llm = create_llm(config)
        response = llm("What is justice?")
    """
    if config is None:
        config = LLMConfig()

    provider_class = PROVIDERS.get(config.provider)
    if not provider_class:
        raise ValueError(
            f"Unknown provider '{config.provider}'. "
            f"Available: {', '.join(PROVIDERS.keys())}"
        )

    return provider_class(config)


def create_llm_from_dict(d: dict) -> LLMProvider:
    """Create an LLM provider from a dictionary (e.g., loaded from config file)."""
    config = LLMConfig(
        **{k: v for k, v in d.items() if k in LLMConfig.__dataclass_fields__}
    )  # pylint: disable=no-member
    return create_llm(config)
