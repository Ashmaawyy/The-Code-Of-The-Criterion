# The Criterion + Deepseek-R1:8b Integration

## 🚀 What's New

**Deepseek-R1:8b integration is complete!**

The Criterion reasoning framework now has full integration with deepseek-r1:8b (via Ollama) as its semantic extraction layer.

```
Natural Language Query
        ↓
deepseek-r1:8b (Semantic Extraction)
        ↓
Criterion Reasoning Engine (6-phase pipeline)
        ↓
Complete Verdict with Chain-of-Thought
```

---

## ⚡ Quick Start

### 1. Install Ollama (5 minutes)
```bash
# Download from https://ollama.ai
# Install and run
```

### 2. Get the Model (10 minutes)
```bash
ollama pull deepseek-r1:8b
```

### 3. Start Ollama Server
```bash
ollama serve
# Runs on localhost:11434
```

### 4. Install Python Deps (1 minute)
```bash
pip install requests
```

### 5. Test It
```python
from evaluation.llm_integration import analyze_with_deepseek

result = analyze_with_deepseek(
    "Is deception in business justified by efficiency gains?",
    verbose=True
)
```

**Done!** You now have deepseek-r1:8b integrated with The Criterion framework.

---

## 📚 Documentation

| Document | Purpose | Read Time |
|----------|---------|-----------|
| [DEEPSEEK_SUMMARY.md](DEEPSEEK_SUMMARY.md) | One-page overview | 5 min |
| [DEEPSEEK_INTEGRATION.md](DEEPSEEK_INTEGRATION.md) | Setup & quick start | 15 min |
| [DEEPSEEK_ARCHITECTURE.md](DEEPSEEK_ARCHITECTURE.md) | Deep architecture | 30 min |
| [DEEPSEEK_DIAGRAMS.md](DEEPSEEK_DIAGRAMS.md) | Visual guides | 10 min |
| [DEEPSEEK_INDEX.md](DEEPSEEK_INDEX.md) | Navigation guide | 5 min |

---

## 💻 Code

### Main Integration
- **[evaluation/llm_integration.py](evaluation/llm_integration.py)** - LLM bridge to Ollama

### Examples
- **[examples/deepseek_criterion_integration.py](examples/deepseek_criterion_integration.py)** - 5 working examples

### System Prompt
- **[examples/DEEPSEEK_SYSTEM_PROMPT.md](examples/DEEPSEEK_SYSTEM_PROMPT.md)** - For standalone deepseek use

---

## 🎯 How It Works

### Three Ways to Use It

**Option 1: Simple (One Line)**
```python
from evaluation.llm_integration import analyze_with_deepseek
result = analyze_with_deepseek("your query", verbose=True)
```

**Option 2: Pipeline (Recommended)**
```python
from evaluation.pipeline import CriterionPipeline
pipeline = CriterionPipeline()
result = pipeline.evaluate_with_deepseek("your query", verbose=True)
```

**Option 3: Full Control**
```python
from evaluation.llm_integration import OllamaLLMBridge
from evaluation.pipeline import CriterionPipeline

bridge = OllamaLLMBridge()
system_data = bridge.extract_semantic_meaning("your query")
pipeline = CriterionPipeline()
result = pipeline.evaluate("your query", system_data)
```

---

## 📖 Example Output

```
Query: "Should we eliminate all financial regulations?"

DEEPSEEK EXTRACTION:
├─ Domain: economic
├─ Assumptions: markets self-regulate, deception is impossible
├─ Intent: reduce business costs
└─ Dismissed harms: systemic collapse risk, consumer protection loss

CRITERION ANALYSIS:
├─ Axiom violations: 3 critical
│  ├─ Axiom 2: No accountability mechanism
│  ├─ Axiom 4: Redefines "safe market"
│  └─ Axiom 5: Creates systemic instability
├─ Gate status:
│  ├─ Source Integrity: FAIL
│  ├─ Structural Consistency: FAIL
│  ├─ Mediation Zeroing: PASS
│  └─ Origin Aware: CRITICAL FAIL
├─ Network effects: Creates unstable system amplified across economy
└─ Verdict: FAIL

RECOMMENDATION: Improve regulations rather than eliminate them
```

---

## ✨ Key Features

✅ **Natural Language Input** - Write proposals in plain English
✅ **Semantic Extraction** - deepseek-r1:8b identifies hidden assumptions
✅ **Axiom-Based Reasoning** - 5 foundational axioms checked
✅ **Survival Filters** - 4 critical gates all proposals must pass
✅ **Network Prediction** - Maps cascading consequences
✅ **Transparent Reasoning** - Full chain-of-thought visible
✅ **Local Execution** - Zero API costs, complete privacy
✅ **Production Ready** - Fully tested and documented

---

## 🔧 System Requirements

- **RAM**: 8GB+ recommended
- **Disk**: 4-5GB for deepseek-r1:8b model
- **CPU**: 2+ cores
- **Python**: 3.8+
- **Ollama**: Latest version

---

## ⏱️ Performance

- **Semantic Extraction**: 15-30 seconds (with reasoning)
- **Reasoning Pipeline**: 1-2 seconds
- **Total per Query**: ~20-35 seconds

The wait is worth it—you get transparent, axiom-based reasoning.

---

## 📁 What Was Added

### Code Files
- `evaluation/llm_integration.py` (296 lines)
- `examples/deepseek_criterion_integration.py` (400+ lines)

### Documentation Files
- `DEEPSEEK_SUMMARY.md`
- `DEEPSEEK_INTEGRATION.md`
- `DEEPSEEK_ARCHITECTURE.md`
- `DEEPSEEK_DIAGRAMS.md`
- `DEEPSEEK_INDEX.md`
- `DEEPSEEK_COMPLETION_CHECKLIST.md`
- `examples/DEEPSEEK_SYSTEM_PROMPT.md`

### Configuration
- `requirements.txt`

### Modified Files
- `evaluation/pipeline.py` - Added `evaluate_with_deepseek()` method

---

## 🚨 Troubleshooting

### "Cannot connect to Ollama"
```bash
# Make sure Ollama is running
ollama serve

# In another terminal
ollama list  # Should show deepseek-r1:8b
```

### "Model not found"
```bash
ollama pull deepseek-r1:8b
```

### "Timeout"
- deepseek-r1:8b with reasoning can be slow (30-60 seconds)
- This is normal and necessary for quality reasoning
- Default timeout is 300 seconds (5 minutes)

**More troubleshooting** → [DEEPSEEK_INTEGRATION.md](DEEPSEEK_INTEGRATION.md#troubleshooting)

---

## 🎓 Learning Path

1. **Start** → Read [DEEPSEEK_SUMMARY.md](DEEPSEEK_SUMMARY.md) (5 min)
2. **Setup** → Follow [DEEPSEEK_INTEGRATION.md](DEEPSEEK_INTEGRATION.md) (5 min)
3. **Run** → Execute [examples/deepseek_criterion_integration.py](examples/deepseek_criterion_integration.py) (10 min)
4. **Learn** → Read [DEEPSEEK_ARCHITECTURE.md](DEEPSEEK_ARCHITECTURE.md) (30 min)
5. **Build** → Use examples as templates for your project

---

## 📚 Next Steps

### Immediate
- [ ] Install Ollama
- [ ] Pull deepseek-r1:8b
- [ ] Install Python deps
- [ ] Run examples

### Short Term
- [ ] Test with real proposals
- [ ] Integrate into your project
- [ ] Fine-tune if needed

### Medium Term
- [ ] Build Layer 3: VectorDB
- [ ] Implement learning loop
- [ ] Add pattern storage

### Long Term
- [ ] Fine-tune deepseek on Criterion data
- [ ] Multi-model support
- [ ] Advanced learning strategies

---

## 🎯 Use Cases

✅ Policy evaluation
✅ Business proposal analysis
✅ Technology impact assessment
✅ Institutional change review
✅ System design validation
✅ Educational framework testing
✅ Ethical analysis
✅ Consequence prediction

---

## 💡 Why This Integration?

### Deepseek-R1:8b Advantages
- ✅ Chain-of-thought reasoning native to the model
- ✅ Explains its thinking explicitly
- ✅ Good at identifying hidden assumptions
- ✅ Runs locally (no API costs)
- ✅ Reliable JSON output
- ✅ Can be self-hosted

### The Criterion Advantages
- ✅ 5 foundational axioms operationalized
- ✅ 4 survival gates to catch bad proposals
- ✅ Network effect prediction
- ✅ Transparent reasoning at every step
- ✅ Based on proven principles

### Together
- ✅ Natural language input
- ✅ Semantic understanding
- ✅ Axiom-based judgment
- ✅ Actionable recommendations
- ✅ Complete transparency

---

## 📞 Support

**Installation help** → [DEEPSEEK_INTEGRATION.md](DEEPSEEK_INTEGRATION.md)

**Architecture questions** → [DEEPSEEK_ARCHITECTURE.md](DEEPSEEK_ARCHITECTURE.md)

**Code examples** → [examples/deepseek_criterion_integration.py](examples/deepseek_criterion_integration.py)

**Visual guide** → [DEEPSEEK_DIAGRAMS.md](DEEPSEEK_DIAGRAMS.md)

**Everything** → [DEEPSEEK_INDEX.md](DEEPSEEK_INDEX.md)

---

## ✅ Status

| Component | Status |
|-----------|--------|
| LLM Bridge | ✅ COMPLETE |
| Pipeline Integration | ✅ COMPLETE |
| Examples | ✅ COMPLETE (5) |
| Documentation | ✅ COMPLETE |
| Testing | ✅ COMPLETE |
| Production Ready | ✅ YES |

---

## 🎉 You're Ready

Everything is set up and ready to use.

**Next**: Pick an example from [examples/deepseek_criterion_integration.py](examples/deepseek_criterion_integration.py) and run it!

---

**Version**: 1.0  
**Date**: February 14, 2026  
**Status**: Production Ready  
**Quality**: Fully Tested & Documented
