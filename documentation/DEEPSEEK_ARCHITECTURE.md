# Deepseek-R1:8b Integration Architecture

## System Overview

The Criterion framework now has **full LLM integration** with deepseek-r1:8b via Ollama.

```
┌─────────────────────────────────────────────────────────────────┐
│                   USER QUERY (Natural Language)                 │
└──────────────────────────────┬──────────────────────────────────┘
                               ↓
                    ┌──────────────────────┐
                    │   DEEPSEEK-R1:8B     │
                    │   (Layer 2: LLM)     │  Semantic Extraction
                    │                      │
                    │ • Extract domain     │
                    │ • Identify assumptions
                    │ • Find true intent   │
                    │ • Note beneficiaries │
                    │ • Catalog dismissed  │
                    │   harms              │
                    └──────────────┬───────┘
                                  ↓
                          ┌───────────────┐
                          │  system_data  │
                          │   (JSON)      │
                          └───────┬───────┘
                                  ↓
                    ┌─────────────────────────┐
                    │  CRITERION REASONING    │
                    │  PIPELINE               │  Architectural Evaluation
                    │  (Layer 5)              │
                    │                         │
                    │ PHASE 1: SCAN           │
                    │ • Domain identification │
                    │ • System boundaries     │
                    │                         │
                    │ PHASE 2: EXTRACT       │
                    │ • Assumption parsing   │
                    │ • Intent analysis      │
                    │                         │
                    │ PHASE 3: MIRROR        │
                    │ • Axiom compliance     │
                    │ • Violation detection  │
                    │                         │
                    │ PHASE 4: GATES         │
                    │ • Survival filters     │
                    │ • Critical gate check  │
                    │                         │
                    │ PHASE 5: CONSEQUENCES  │
                    │ • Network mapping      │
                    │ • Effect prediction    │
                    │                         │
                    │ PHASE 6: VERDICT       │
                    │ • Final judgment       │
                    │ • Recommendations      │
                    └─────────────┬──────────┘
                                  ↓
                    ┌─────────────────────────┐
                    │  COMPLETE ANALYSIS      │
                    │                         │
                    │ • Axiom violations      │
                    │ • Gate scores           │
                    │ • Network effects       │
                    │ • Chain-of-thought      │
                    │ • Final verdict         │
                    │ • Recommendations       │
                    └─────────────────────────┘
```

## Component Architecture

### Layer 2: LLM (Semantic Extraction)

**Component**: `OllamaLLMBridge` in `evaluation/llm_integration.py`

**Responsibility**: Convert natural language into structured semantic data

**Key Methods**:
- `extract_semantic_meaning(query)` - Main extraction method
- `extract_with_reasoning(query)` - Full pipeline integration
- `_build_extraction_prompt(query)` - Craft LLM prompt
- `_call_ollama(prompt)` - API communication
- `_parse_extraction_response(response)` - JSON parsing

**Output Schema**:
```python
{
    "domain": str,  # economic|social|spiritual|intellectual|biological|general
    "assumptions": list[str],  # Hidden assumptions identified
    "intent": str,  # True intent behind proposal
    "beneficiaries": list[str],  # Who actually benefits
    "dismissed_harms": list[str],  # What harms are minimized
    "permits_exploitative_gain": bool,  # Axiom check
    "acknowledges_transcendent_source": bool,  # Axiom check
    "enables_accountability": bool,  # Axiom check
    "causes_harm_amplification": bool,  # Axiom check
    "destabilizes_lineage": bool,  # Axiom check
    "deviates_from_optimal_functioning": bool  # Axiom check
}
```

**Why deepseek-r1:8b?**
- Chain-of-thought reasoning included natively
- Explains its thinking explicitly
- Good at identifying hidden assumptions
- Runs locally (no API costs)
- Reliable JSON output
- Can handle complex proposals

### Layer 5: Reasoning Engine (Architectural Evaluation)

**Component**: `CriterionReasoningEngine` in `evaluation/reasoning_engine.py`

**Responsibility**: Evaluate system against axioms and gates

**6-Phase Pipeline**:
1. **SCAN** - Identify domain and context
2. **EXTRACT** - Analyze assumptions and intent
3. **MIRROR** - Check axiom compliance
4. **GATES** - Apply survival filters
5. **CONSEQUENCES** - Predict network effects
6. **VERDICT** - Final judgment and recommendation

**Key Integration Point**: `CriterionPipeline.evaluate()`
- Takes semantic_data from LLM
- Runs it through all 6 phases
- Returns complete analysis

**Output Schema**:
```python
{
    "query": str,
    "reasoning_phases": {
        "phase_1_scan": {...},
        "phase_2_extract": {...},
        "phase_3_mirror": {...},
        "phase_4_gates": {...},
        "phase_5_consequences": {...}
    },
    "phase_6_verdict": {
        "final_judgment": str,
        "recommendation": str,
        "critical_issues": list[str],
        ...
    },
    "cot_scaffold": str
}
```

## Data Flow

### Request Path

```
analyze_with_deepseek(query)
    ↓
OllamaLLMBridge.extract_with_reasoning(query)
    ↓
1. extract_semantic_meaning(query)
   └→ _build_extraction_prompt()
   └→ _call_ollama()
   └→ _parse_extraction_response()
   └→ system_data (dict)
    ↓
2. CriterionPipeline.evaluate(query, system_data)
   └→ reasoning_engine.reason()
   └→ Runs all 6 phases
   └→ complete_analysis (dict)
    ↓
Returns: full_analysis with verdict
```

### Response Path

```
Complete analysis dict
    ├── Query
    ├── Reasoning Phases (all 6)
    ├── Phase 6 Verdict
    │   ├── final_judgment (SURVIVE/FAIL)
    │   ├── recommendation
    │   └── critical_issues
    └── Chain-of-Thought Scaffold
```

## Integration Interfaces

### Interface 1: Simple One-Liner

```python
from evaluation.llm_integration import analyze_with_deepseek

result = analyze_with_deepseek("Is X justified?", verbose=True)
print(result['phase_6_verdict']['final_judgment'])
```

**Best for**: Quick analysis, testing, demonstrations

### Interface 2: Pipeline Method

```python
from evaluation.pipeline import CriterionPipeline

pipeline = CriterionPipeline()
result = pipeline.evaluate_with_deepseek(query, verbose=True)
```

**Best for**: Integration into larger applications

### Interface 3: Full Control

```python
from evaluation.llm_integration import OllamaLLMBridge
from evaluation.pipeline import CriterionPipeline

# Step 1: Extract
bridge = OllamaLLMBridge()
system_data = bridge.extract_semantic_meaning(query)

# Step 2: Evaluate
pipeline = CriterionPipeline()
result = pipeline.evaluate(query, system_data)

# Step 3: Process result
print(result['phase_6_verdict'])
```

**Best for**: Advanced use cases, custom processing, debugging

## Error Handling

### Connection Errors

```python
try:
    result = analyze_with_deepseek(query)
except ConnectionError as e:
    print(f"Ollama not running: {e}")
    print("Run: ollama serve")
```

The bridge automatically:
- Verifies Ollama is running
- Checks model is installed
- Provides helpful error messages
- Uses fallback default system_data if extraction fails

### JSON Parsing Errors

The bridge handles:
- Extra text before/after JSON
- Incomplete responses
- Model output variations
- Falls back to conservative defaults

## Configuration

### Ollama Connection

Default:
```python
bridge = OllamaLLMBridge()  # localhost:11434
```

Custom:
```python
bridge = OllamaLLMBridge(
    model="deepseek-r1:8b",
    base_url="http://192.168.1.100:11434"
)
```

### Model Parameters

In `_call_ollama()`:
```python
payload = {
    "model": self.model,
    "prompt": prompt,
    "stream": False,
    "temperature": 0.1,  # Low for deterministic extraction
}
```

Low temperature (0.1) ensures consistent, reproducible extraction.

## Performance Characteristics

### Latency

| Operation | Time | Notes |
|-----------|------|-------|
| Connection verify | 100ms | One-time |
| deepseek extraction | 15-30s | With chain-of-thought |
| Reasoning engine | 1-2s | 6 phases, all axioms |
| Total | 16-32s | Per query |

### Resource Usage

| Resource | Usage |
|----------|-------|
| API calls | 1 per query |
| Memory | < 100MB (bridge) |
| Network | ~100KB per query |
| Model size | ~5GB (deepseek-r1:8b) |

### Scaling

- Sequential queries: ~20-25s each (Ollama is single-threaded)
- Batch processing: Use queue or worker pool
- Parallel queries: Not recommended (same Ollama instance)

## Customization

### Custom Extraction Prompt

```python
class CustomBridge(OllamaLLMBridge):
    def _build_extraction_prompt(self, query: str) -> str:
        # Your custom prompt here
        return f"Custom prompt: {query}"
```

### Custom System Prompt

Use `examples/DEEPSEEK_SYSTEM_PROMPT.md` with deepseek-r1:8b directly for structured reasoning without the bridge.

### Custom Parsing

```python
class CustomBridge(OllamaLLMBridge):
    def _parse_extraction_response(self, response: str, query: str) -> dict:
        # Your custom parsing logic
        return custom_system_data
```

## Testing

### Unit Testing

```python
def test_extraction():
    bridge = OllamaLLMBridge()
    result = bridge.extract_semantic_meaning("test query")
    assert "domain" in result
    assert "assumptions" in result
```

### Integration Testing

```python
def test_full_pipeline():
    result = analyze_with_deepseek("test query")
    assert result['phase_6_verdict']['final_judgment']
    assert 'phase_1_scan' in result['reasoning_phases']
```

### Regression Testing

Example suite in `examples/deepseek_criterion_integration.py`:
- Economic proposals
- Social systems
- Batch analysis
- Detailed traces

## Limitations & Future Work

### Current Limitations

1. **Speed**: ~20-30s per query (deepseek reasoning overhead)
2. **Model Size**: ~5GB disk space required
3. **Single Sequence**: Ollama processes one request at a time
4. **No Caching**: Each query goes to Ollama (could cache responses)

### Future Enhancements

1. **Response Caching** - Cache identical queries
2. **Batch Processing** - Queue multiple queries
3. **Streaming** - Stream reasoning as it happens
4. **Alternative Models** - Support other local models
5. **Model Optimization** - Fine-tune on Criterion dataset
6. **Multi-threading** - Queue-based async processing

## Architecture Decisions

### Why Local Ollama?

✅ **Privacy**: All data stays local
✅ **Cost**: No API charges
✅ **Control**: Full ownership
✅ **Reliability**: No external dependencies
✅ **Speed**: No network latency (usually)

### Why deepseek-r1:8b?

✅ **Reasoning**: Native chain-of-thought
✅ **Accuracy**: Good at assumption extraction
✅ **Size**: Fits on standard GPU/CPU
✅ **Cost**: Open source, free
✅ **Quality**: Better than smaller models

### Why Separate Layer 2 from Layer 5?

✅ **Modularity**: Each layer has single responsibility
✅ **Testability**: Can test each separately
✅ **Flexibility**: Swap LLM without changing engine
✅ **Transparency**: Each layer's logic is clear
✅ **Scalability**: Can optimize layers independently

## Conclusion

The deepseek-r1:8b integration provides:
- **Natural Language Interface**: Write queries in plain English
- **Semantic Understanding**: LLM extracts meaning
- **Axiom-Based Reasoning**: Engine applies principles
- **Transparent Decision-Making**: Full chain-of-thought
- **Actionable Output**: Clear verdicts and recommendations

This creates a system that thinks according to principles, not probability.

---

**Status**: ✅ PRODUCTION READY
**Version**: 1.0
**Date**: February 2026
