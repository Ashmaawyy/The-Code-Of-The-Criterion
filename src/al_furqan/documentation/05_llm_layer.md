# LLM Layer — Technical Reference

**File:** `llm_layer.py`
**Role:** The "tongue" of the system. Provides a unified callable interface for any LLM provider to plug into the reasoning engine.

## 1. Design Principle

The reasoning engine depends on a single interface:

```python
llm_call(prompt: str) -> str
```

The LLM layer implements this interface through multiple providers. Each provider is a callable object — when you call `provider("What is justice?")`, it generates a response and returns it as a string.

The reasoning engine has zero knowledge of which model or provider is running. This makes the system fully LLM-agnostic.

## 2. LLMConfig (Dataclass)

Central configuration for all providers.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `provider` | `str` | `"ollama"` | Provider type: `ollama`, `transformers`, `openai_compatible` |
| `model_name` | `str` | `"mistral"` | Model identifier (Ollama name, HuggingFace ID, or API model name) |
| `base_url` | `str` | `"http://localhost:11434"` | API base URL for Ollama or OpenAI-compatible servers |
| `temperature` | `float` | `0.1` | Sampling temperature. Low for deterministic reasoning. |
| `max_tokens` | `int` | `4096` | Maximum output tokens per generation |
| `top_p` | `float` | `0.9` | Nucleus sampling parameter |
| `repeat_penalty` | `float` | `1.1` | Repetition penalty (Ollama/Transformers) |
| `timeout` | `int` | `300` | Request timeout in seconds |
| `system_prompt` | `str` | `""` | Optional system prompt override |
| `device` | `str` | `"auto"` | Transformers only: `auto`, `cpu`, `cuda`, `mps` |
| `quantization` | `Optional[str]` | `None` | Transformers only: `"4bit"`, `"8bit"`, or `None` |

## 3. LLMCallLog (Dataclass)

A log entry recorded for every LLM call.

| Field | Type | Description |
|-------|------|-------------|
| `prompt_length` | `int` | Character count of the prompt |
| `response_length` | `int` | Character count of the response |
| `duration_seconds` | `float` | Wall-clock time for the call |
| `model` | `str` | Model name used |
| `provider` | `str` | Provider type used |
| `timestamp` | `float` | Unix timestamp, auto-set |

## 4. LLMProvider (Abstract Base Class)

All providers inherit from this class.

**Constructor:** `LLMProvider(config: LLMConfig)`

**Abstract method:** `generate(prompt: str) -> str` — Must be implemented by each provider.

**Concrete methods:**

| Method | Description |
|--------|-------------|
| `__call__(prompt)` | The callable interface. Wraps `generate()` with timing and logging. Returns the response string. |
| `get_stats()` | Returns a summary dict: total calls, total/avg duration, total prompt/response chars, model, provider. |

**Call log:** Every call via `__call__` appends an `LLMCallLog` entry to `self.call_log`.

## 5. Providers

### OllamaProvider

**Backend:** Ollama REST API (`/api/generate` endpoint).
**Requirements:** Ollama installed and running (`ollama serve`), model pulled (`ollama pull <name>`).

**API payload structure:**
```json
{
    "model": "mistral",
    "prompt": "...",
    "stream": false,
    "options": {
        "temperature": 0.1,
        "num_predict": 4096,
        "top_p": 0.9,
        "repeat_penalty": 1.1
    }
}
```

**Error handling:**
- `ConnectionError` → "Cannot connect to Ollama. Make sure Ollama is running."
- `TimeoutError` → "Request timed out. Model may be too large."
- HTTP 404 → "Model not found. Pull it with: `ollama pull <name>`."

**Recommended models:**

| Model | Size | Strengths |
|-------|------|-----------|
| `mistral` | 7B | Fast, good reasoning for its size |
| `llama3.1` | 8B | Strong instruction following |
| `qwen2.5` | 7B/14B | Excellent structured JSON output |
| `deepseek-r1` | 7B | Strong reasoning capabilities |
| `gemma3` | 12B | Good balance of speed and quality |

### TransformersProvider

**Backend:** HuggingFace Transformers library. Loads models directly into GPU/CPU memory.
**Requirements:** `torch`, `transformers` packages. Optionally `bitsandbytes` for quantization.

**Key behavior:**
- **Lazy loading:** The model is not loaded on init. It loads on the first `generate()` call. This avoids unnecessary memory allocation if the provider is created but not used.
- **Quantization support:** 4-bit and 8-bit quantization via BitsAndBytesConfig. Enables running larger models on consumer GPUs.
- **Device mapping:** Supports `auto` (let PyTorch decide), `cpu`, `cuda`, and `mps` (Apple Silicon).
- **Token decoding:** Only decodes the newly generated tokens, not the prompt echo.

**Recommended models (HuggingFace IDs):**

| Model ID | Size |
|----------|------|
| `mistralai/Mistral-7B-Instruct-v0.3` | 7B |
| `meta-llama/Meta-Llama-3.1-8B-Instruct` | 8B |
| `Qwen/Qwen2.5-7B-Instruct` | 7B |
| `google/gemma-3-12b-it` | 12B |

### OpenAICompatibleProvider

**Backend:** Any server implementing the OpenAI Chat Completions API (`/v1/chat/completions`).
**Requirements:** `requests` package. Server running and accessible.

**Compatible servers:**
- LM Studio (local)
- vLLM (local)
- text-generation-webui (local)
- Together.ai (remote)
- Groq (remote)

**API payload structure:**
```json
{
    "model": "model-name",
    "messages": [
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."}
    ],
    "temperature": 0.1,
    "max_tokens": 4096,
    "top_p": 0.9
}
```

## 6. Factory Functions

### create_llm(config) -> LLMProvider

Creates a provider instance from an `LLMConfig`. If no config is given, uses defaults (Ollama + Mistral).

Raises `ValueError` for unknown provider names.

### create_llm_from_dict(d) -> LLMProvider

Creates a provider from a plain dictionary. Filters out unknown keys before constructing `LLMConfig`. Used when loading config from YAML/JSON files.

## 7. Provider Registry

```python
PROVIDERS = {
    "ollama": OllamaProvider,
    "transformers": TransformersProvider,
    "openai_compatible": OpenAICompatibleProvider,
}
```

To add a new provider: define a class inheriting `LLMProvider`, implement `generate()`, and add it to this dict.
