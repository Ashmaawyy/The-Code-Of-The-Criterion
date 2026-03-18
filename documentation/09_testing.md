# Testing — Technical Reference

**Directory:** `unit_tests/`
**Framework:** pytest
**Total tests:** ~102

## 1. Test Structure

```
unit_tests/
├── __init__.py                  # Package marker
├── conftest.py                  # Shared fixtures and mock LLM responses
├── test_reasoning_engine.py     # 30 tests
├── test_verdict_store.py        # 22 tests
├── test_llm_layer.py            # 18 tests
├── test_config.py               # 15 tests
└── test_human_review.py         # 17 tests
```

## 2. Running Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest unit_tests/ -v

# Run a specific test file
pytest unit_tests/test_reasoning_engine.py -v

# Run a specific test class
pytest unit_tests/test_reasoning_engine.py::TestVerdict -v

# Run a specific test
pytest unit_tests/test_reasoning_engine.py::TestVerdict::test_from_dict_roundtrip -v
```

## 3. Fixtures (conftest.py)

### Mock LLM Responses

Pre-built JSON responses simulating a complete evaluation flow:

| Constant | Simulates |
|----------|-----------|
| `MOCK_SCAN_RESPONSE` | Phase 1 output: economic system, 2 friction points |
| `MOCK_MIRROR_RESPONSE` | Phase 2 output: all 4 gates scoring 70-90, all Survive |
| `MOCK_VERDICT_RESPONSE` | Phase 3 output: consequences, reasoning, judgment, score 85 |
| `MOCK_CORRECTION_SOUND` | Self-correction: verdict is sound, no changes |
| `MOCK_CORRECTION_WITH_FIX` | Self-correction: 1 contradiction found, score corrected to 90 |

### make_mock_llm(responses)

Creates a mock LLM callable that returns predefined responses in sequence. Each call returns the next response in the list. If more calls are made than responses provided, the last response is repeated.

### Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `mock_llm` | function | Default mock LLM (Scan → Mirror → Verdict → Sound correction) |
| `engine` | function | ReasoningEngine wired to the mock LLM |
| `sample_verdict` | function | Fully populated Verdict object for testing |
| `tmp_store` | function | VerdictStore using pytest's `tmp_path` (isolated, auto-cleaned) |

## 4. Test Coverage by Module

### test_reasoning_engine.py (30 tests)

**Data structures:**
- `TestSystemType` — enum values, string construction, invalid value handling
- `TestGateResult` — enum values
- `TestGateScore` — `to_dict()` serialization, fail result handling
- `TestVerdict` — `to_dict()`, `to_log()`, `from_dict()` roundtrip, default handling, invalid system type recovery, string score coercion, auto-timestamp

**Prompt builders:**
- `TestPromptBuilders` — question inclusion, context injection, context omission, scan result embedding, pass number display

**JSON parsing:**
- `TestJSONParsing` — clean JSON, markdown fences, surrounding text, code fences without language tag, invalid JSON error, nested structures

**Engine pipeline:**
- `TestReasoningEnginePipeline` — individual phase execution (scan, mirror, verdict, self_correct), full `evaluate()` flow, correction application, context passing, max passes enforcement, `_build_verdict_object` with normal/unknown/None system types, `_build_gate_scores` with valid and missing data

### test_verdict_store.py (22 tests)

**Store & retrieve:**
- JSON file creation, content verification, ChromaDB indexing for approved/corrected/rejected, empty store retrieval, result structure, relevance ordering, n_results limiting, system type filtering, get by ID (found and not found)

**Context formatting:**
- Empty store returns empty string, context contains headers/content, None distance handling

**Status updates:**
- Reject removes from index, file status updates, needs_review removes from index, re-approve re-indexes, nonexistent ID returns False, corrected verdict supersedes original

**Cascade invalidation:**
- Removes original, flags later similar verdicts, does not flag earlier verdicts, handles nonexistent IDs

**Statistics:**
- Empty store, multi-status counts

**Collection name:**
- Custom name, default name

### test_llm_layer.py (18 tests)

**LLMConfig:**
- Default values, custom value construction

**LLMCallLog:**
- `to_dict()` serialization, auto-timestamp

**LLMProvider base:**
- Callable interface, call logging per invocation, duration recording, empty stats, stats after multiple calls

**Factory functions:**
- `create_llm()` for each provider type, default config, unknown provider error, `create_llm_from_dict()` with valid/extra/empty keys

**Provider registry:**
- All three providers registered, all are LLMProvider subclasses

### test_config.py (15 tests)

**Defaults:**
- AppConfig, EngineConfig, StoreConfig, ReviewConfig default values

**Serialization:**
- `to_dict()` structure, custom values reflected

**Load config:**
- Missing file returns defaults, full YAML loading, partial YAML (missing sections default), empty YAML, unknown keys ignored

**Save config:**
- Save and reload roundtrip

**Generate default:**
- File creation, contains all sections, generated file is loadable

### test_human_review.py (17 tests)

**Display functions:**
- Question, system, gate scores, origin gate, consequences, judgment displayed correctly
- Fail marker `[X]` displayed for failed gates
- Stored verdict dict display

**Input helpers:**
- Valid choice, retry until valid, case insensitivity
- Text input, retry on empty, allow empty
- Integer input, retry on invalid/out of range, boundary values
- List input, empty list

**Review flows:**
- Approve: stores verdict, sets status to approved
- Reject: stores with rejection reason
- Correct with score change: corrected verdict stored
- Correct then decline then approve: loops back correctly

## 5. Testing Strategy

- **No real LLM calls** — all LLM interactions are mocked with predefined JSON responses.
- **No real network calls** — providers are tested for correct instantiation and interface compliance, not API connectivity.
- **Isolated storage** — verdict store tests use pytest's `tmp_path` fixture, creating temporary directories that are auto-cleaned.
- **Mocked input** — all CLI input functions are tested via `unittest.mock.patch("builtins.input")`.
- **Output capture** — display functions are tested via pytest's `capsys` fixture.
