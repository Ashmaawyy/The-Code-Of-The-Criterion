# The Criterion: Complete Documentation Index

## Start Here 👈

**New to The Criterion?** Start with: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
**Want the big picture?** Read: [BUILD_SUMMARY.md](BUILD_SUMMARY.md)
**Ready to implement?** Use: [SYSTEM_PROMPT.md](SYSTEM_PROMPT.md)
**Need the why?** See: [ARCHITECTURE_UPGRADE_GUIDE.md](ARCHITECTURE_UPGRADE_GUIDE.md)

---

## Documentation Guide

### 🎯 Core Understanding (Read These First)

1. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - One-page reference card
   - What: The 6 phases, 5 axioms, 4 gates
   - Why: Quick lookup and decision tree
   - Time: 10 minutes
   - Best for: Getting oriented quickly

2. **[BUILD_SUMMARY.md](BUILD_SUMMARY.md)** - What was delivered
   - What: Complete build overview
   - Why: Understand scope of work
   - Time: 15 minutes
   - Best for: Seeing the whole picture

3. **[ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md)** - Visual explanations
   - What: Flowcharts and diagrams
   - Why: See how everything connects
   - Time: 15 minutes
   - Best for: Visual learners

### 🚀 Implementation (Use These to Build)

4. **[SYSTEM_PROMPT.md](SYSTEM_PROMPT.md)** - LLM Operating Manual
   - What: Complete system prompt template
   - Why: Tell LLM how to use The Criterion
   - Time: 30 minutes to integrate
   - Best for: Deploying with Claude/GPT-4/Gemini

5. **[ARCHITECTURE_UPGRADE_GUIDE.md](ARCHITECTURE_UPGRADE_GUIDE.md)** - Why this design
   - What: Design rationale and layer explanation
   - Why: Understand architectural decisions
   - Time: 20 minutes
   - Best for: Technical stakeholders

6. **[INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md)** - Technical deep dive
   - What: Complete technical summary
   - Why: Understand every component
   - Time: 30 minutes
   - Best for: Developers and architects

### ✅ Verification (Use These to Verify)

7. **[COMPLETION_CHECKLIST.md](COMPLETION_CHECKLIST.md)** - What's been done
   - What: Comprehensive completion status
   - Why: Verify all requirements met
   - Time: 10 minutes
   - Best for: Project managers and reviewers

---

## Code Components

### Core Files

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `evaluation/reasoning_engine.py` | 586 | 6-phase reasoning engine | ✅ Complete |
| `evaluation/pipeline.py` | 300+ | Integrated pipeline | ✅ Complete |
| `evaluation/gates.py` | ~100 | 4 survival gates | ✅ Existing |
| `examples/llm_criterion_integration.py` | 250+ | 3 working examples | ✅ Complete |
| `axioms/core_axioms.json` | 5 items | Foundation axioms | ✅ Existing |

### Documentation Files

| File | Type | Purpose |
|------|------|---------|
| QUICK_REFERENCE.md | Guide | One-page reference |
| BUILD_SUMMARY.md | Summary | What was delivered |
| SYSTEM_PROMPT.md | Template | LLM system prompt |
| ARCHITECTURE_UPGRADE_GUIDE.md | Guide | Why this design |
| ARCHITECTURE_DIAGRAMS.md | Visual | Flowcharts & diagrams |
| INTEGRATION_COMPLETE.md | Report | Technical summary |
| COMPLETION_CHECKLIST.md | Checklist | Status verification |
| DOCUMENTATION_INDEX.md | Meta | This file |

---

## Learning Paths

### Path 1: "I Want to Understand The Criterion" (30 min)
1. Read: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) (10 min)
2. See: [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md) (15 min)
3. Skim: [BUILD_SUMMARY.md](BUILD_SUMMARY.md) (5 min)

### Path 2: "I Want to Deploy It" (1 hour)
1. Read: [SYSTEM_PROMPT.md](SYSTEM_PROMPT.md) (20 min)
2. Setup: Copy system prompt to LLM
3. Read: [ARCHITECTURE_UPGRADE_GUIDE.md](ARCHITECTURE_UPGRADE_GUIDE.md) (20 min)
4. Test: Run examples (20 min)

### Path 3: "I Want to Build with It" (2 hours)
1. Read: [INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md) (30 min)
2. Study: [examples/llm_criterion_integration.py](examples/llm_criterion_integration.py) (20 min)
3. Code: Create your first evaluation (30 min)
4. Test: Verify your code (20 min)
5. Plan: Next features (20 min)

### Path 4: "I Need Everything" (3 hours)
1. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Orient (10 min)
2. [BUILD_SUMMARY.md](BUILD_SUMMARY.md) - Context (15 min)
3. [ARCHITECTURE_UPGRADE_GUIDE.md](ARCHITECTURE_UPGRADE_GUIDE.md) - Design (30 min)
4. [SYSTEM_PROMPT.md](SYSTEM_PROMPT.md) - Implementation (30 min)
5. [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md) - Visualization (30 min)
6. [INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md) - Details (30 min)
7. [COMPLETION_CHECKLIST.md](COMPLETION_CHECKLIST.md) - Verification (15 min)

---

## FAQ: Which File Should I Read?

**"What is The Criterion?"**
→ [QUICK_REFERENCE.md](QUICK_REFERENCE.md) sections 1-3

**"How does it work?"**
→ [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md) - complete flow

**"How do I use it?"**
→ [SYSTEM_PROMPT.md](SYSTEM_PROMPT.md) - full operating manual

**"Why was Layer 2 cancelled?"**
→ [ARCHITECTURE_UPGRADE_GUIDE.md](ARCHITECTURE_UPGRADE_GUIDE.md) - complete rationale

**"What was actually built?"**
→ [BUILD_SUMMARY.md](BUILD_SUMMARY.md) - detailed list

**"Is everything done?"**
→ [COMPLETION_CHECKLIST.md](COMPLETION_CHECKLIST.md) - full verification

**"Show me code examples"**
→ [examples/llm_criterion_integration.py](examples/llm_criterion_integration.py) - 3 examples

**"I'm a developer, give me details"**
→ [INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md) - technical deep dive

**"Show me diagrams"**
→ [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md) - visual explanations

**"How do I get started quickly?"**
→ [QUICK_REFERENCE.md](QUICK_REFERENCE.md) "Testing Quick Commands" section

---

## The 6 Phases Explained Across Docs

### PHASE 1: SCAN
- Quick explanation: [QUICK_REFERENCE.md](QUICK_REFERENCE.md#the-6-phases-abbreviated)
- Detailed: [SYSTEM_PROMPT.md](SYSTEM_PROMPT.md#phase-1-scan---domain-identification)
- Code: [evaluation/reasoning_engine.py](evaluation/reasoning_engine.py#L147-L181) line 147-181

### PHASE 2: EXTRACT
- Quick explanation: [QUICK_REFERENCE.md](QUICK_REFERENCE.md#the-6-phases-abbreviated)
- Detailed: [SYSTEM_PROMPT.md](SYSTEM_PROMPT.md#phase-2-extract---assumption-parsing)
- Code: [evaluation/reasoning_engine.py](evaluation/reasoning_engine.py#L201-L275) line 201-275

### PHASE 3: MIRROR
- Quick explanation: [QUICK_REFERENCE.md](QUICK_REFERENCE.md#the-5-axioms-abbreviated)
- Detailed: [SYSTEM_PROMPT.md](SYSTEM_PROMPT.md#phase-3-mirror---axiom-compliance-check)
- Code: [evaluation/reasoning_engine.py](evaluation/reasoning_engine.py#L295-L370) line 295-370

### PHASE 4: GATES
- Quick explanation: [QUICK_REFERENCE.md](QUICK_REFERENCE.md#the-4-gates-abbreviated)
- Detailed: [SYSTEM_PROMPT.md](SYSTEM_PROMPT.md#phase-4-gates---survival-filter)
- Code: [evaluation/reasoning_engine.py](evaluation/reasoning_engine.py#L390-L455) line 390-455

### PHASE 5: CONSEQUENCES
- Quick explanation: [QUICK_REFERENCE.md](QUICK_REFERENCE.md#quick-decision-tree)
- Detailed: [SYSTEM_PROMPT.md](SYSTEM_PROMPT.md#phase-5-consequences---network-effect-tracing)
- Code: [evaluation/reasoning_engine.py](evaluation/reasoning_engine.py#L475-L540) line 475-540

### PHASE 6: VERDICT
- Quick explanation: [QUICK_REFERENCE.md](QUICK_REFERENCE.md#common-verdicts)
- Detailed: [SYSTEM_PROMPT.md](SYSTEM_PROMPT.md#phase-6-verdict---structured-judgment)
- Code: [evaluation/reasoning_engine.py](evaluation/reasoning_engine.py#L550-L600) line 550-600

---

## The 5 Axioms Explained Across Docs

| Axiom | Quick Ref | Full Explanation | System Prompt |
|-------|-----------|------------------|---------------|
| Transcendence Necessity | [Link](QUICK_REFERENCE.md#the-5-axioms-abbreviated) | [Link](ARCHITECTURE_UPGRADE_GUIDE.md#the-5-axioms) | [Link](SYSTEM_PROMPT.md#phase-3-mirror---axiom-compliance-check) |
| Final Court Necessity | [Link](QUICK_REFERENCE.md#the-5-axioms-abbreviated) | [Link](ARCHITECTURE_UPGRADE_GUIDE.md#the-5-axioms) | [Link](SYSTEM_PROMPT.md#phase-3-mirror---axiom-compliance-check) |
| Design vs Accident | [Link](QUICK_REFERENCE.md#the-5-axioms-abbreviated) | [Link](ARCHITECTURE_UPGRADE_GUIDE.md#the-5-axioms) | [Link](SYSTEM_PROMPT.md#phase-3-mirror---axiom-compliance-check) |
| Definition of Normal | [Link](QUICK_REFERENCE.md#the-5-axioms-abbreviated) | [Link](ARCHITECTURE_UPGRADE_GUIDE.md#the-5-axioms) | [Link](SYSTEM_PROMPT.md#phase-3-mirror---axiom-compliance-check) |
| Network Effect | [Link](QUICK_REFERENCE.md#the-5-axioms-abbreviated) | [Link](ARCHITECTURE_UPGRADE_GUIDE.md#the-5-axioms) | [Link](SYSTEM_PROMPT.md#phase-3-mirror---axiom-compliance-check) |

---

## The 4 Gates Explained Across Docs

| Gate | Quick Ref | Full Details | System Prompt |
|------|-----------|--------------|---------------|
| Source Integrity | [Link](QUICK_REFERENCE.md#the-4-gates-abbreviated) | [Link](ARCHITECTURE_UPGRADE_GUIDE.md#the-4-gates) | [Link](SYSTEM_PROMPT.md#phase-4-gates---survival-filter) |
| Structural Consistency | [Link](QUICK_REFERENCE.md#the-4-gates-abbreviated) | [Link](ARCHITECTURE_UPGRADE_GUIDE.md#the-4-gates) | [Link](SYSTEM_PROMPT.md#phase-4-gates---survival-filter) |
| Mediation Zeroing | [Link](QUICK_REFERENCE.md#the-4-gates-abbreviated) | [Link](ARCHITECTURE_UPGRADE_GUIDE.md#the-4-gates) | [Link](SYSTEM_PROMPT.md#phase-4-gates---survival-filter) |
| Origin Aware (MANDATORY) | [Link](QUICK_REFERENCE.md#the-4-gates-abbreviated) | [Link](ARCHITECTURE_UPGRADE_GUIDE.md#the-4-gates) | [Link](SYSTEM_PROMPT.md#phase-4-gates---survival-filter) |

---

## Visual Guides

### Flowcharts
- Complete system flow: [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md#the-complete-flow)
- Phase decision trees: [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md#phase-decision-trees)
- Gate evaluation: [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md#overall-survives-vs-fails)

### Tables & Matrices
- Gate scoring guide: [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md#gate-scoring-guide)
- Verdict matrix: [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md#verdict-classification)
- Phase overview: [INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md#the-6-phases-explained)

---

## Getting Help

**I don't understand the axioms**
→ [SYSTEM_PROMPT.md](SYSTEM_PROMPT.md#phase-3-mirror---axiom-compliance-check) + [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md)

**I don't understand the gates**
→ [SYSTEM_PROMPT.md](SYSTEM_PROMPT.md#phase-4-gates---survival-filter) + [QUICK_REFERENCE.md](QUICK_REFERENCE.md#the-4-gates-abbreviated)

**I don't understand how to use it**
→ [ARCHITECTURE_UPGRADE_GUIDE.md](ARCHITECTURE_UPGRADE_GUIDE.md#how-it-works-in-practice) + [examples/llm_criterion_integration.py](examples/llm_criterion_integration.py)

**I want to extend it**
→ [INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md#next-steps) + [ARCHITECTURE_UPGRADE_GUIDE.md](ARCHITECTURE_UPGRADE_GUIDE.md#next-steps)

**I want to debug something**
→ [QUICK_REFERENCE.md](QUICK_REFERENCE.md#testing-quick-commands) + [BUILD_SUMMARY.md](BUILD_SUMMARY.md#files-at-a-glance)

---

## Document Statistics

| Document | Lines | Read Time | Best For |
|----------|-------|-----------|----------|
| QUICK_REFERENCE.md | 150 | 10 min | Overview |
| BUILD_SUMMARY.md | 200 | 15 min | Context |
| SYSTEM_PROMPT.md | 200 | 20 min | Deployment |
| ARCHITECTURE_UPGRADE_GUIDE.md | 150 | 15 min | Understanding |
| ARCHITECTURE_DIAGRAMS.md | 200 | 15 min | Visual learning |
| INTEGRATION_COMPLETE.md | 200 | 25 min | Technical details |
| COMPLETION_CHECKLIST.md | 250 | 15 min | Verification |
| **Total** | **~1,350** | **~2 hours** | **Full mastery** |

---

## Code Statistics

| Component | Lines | Purpose |
|-----------|-------|---------|
| reasoning_engine.py | 586 | 6-phase reasoning |
| pipeline.py | 300+ | Integration |
| llm_criterion_integration.py | 250+ | Examples |
| gates.py | ~100 | Filters (existing) |
| **Total** | **~1,250** | Production code |

---

## Quick Navigation

### By Role

**Project Manager**
→ [BUILD_SUMMARY.md](BUILD_SUMMARY.md) + [COMPLETION_CHECKLIST.md](COMPLETION_CHECKLIST.md)

**Architect**
→ [ARCHITECTURE_UPGRADE_GUIDE.md](ARCHITECTURE_UPGRADE_GUIDE.md) + [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md)

**Developer**
→ [INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md) + [examples/llm_criterion_integration.py](examples/llm_criterion_integration.py)

**Data Scientist / ML Researcher**
→ [SYSTEM_PROMPT.md](SYSTEM_PROMPT.md) + [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

**End User / LLM Deployer**
→ [SYSTEM_PROMPT.md](SYSTEM_PROMPT.md) + [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

### By Question Type

**What?** → [QUICK_REFERENCE.md](QUICK_REFERENCE.md) or [BUILD_SUMMARY.md](BUILD_SUMMARY.md)
**Why?** → [ARCHITECTURE_UPGRADE_GUIDE.md](ARCHITECTURE_UPGRADE_GUIDE.md)
**How?** → [SYSTEM_PROMPT.md](SYSTEM_PROMPT.md) or [INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md)
**See?** → [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md)
**Check?** → [COMPLETION_CHECKLIST.md](COMPLETION_CHECKLIST.md)

---

## Version Info

- **Build Date**: February 13, 2026
- **Status**: ✅ Complete and Ready
- **Python Version**: 3.8+
- **Dependencies**: None (stdlib only)
- **Lines of Code**: ~1,250 (production) + ~1,350 (documentation)

---

## Next Steps

1. **Choose your path** based on your role (see "By Role" above)
2. **Read the relevant documents** in order
3. **Run the examples** to verify understanding
4. **Deploy or integrate** based on your needs

---

*The Criterion: A framework for teaching LLMs to think according to axioms.*
*Complete documentation available above.*
*Ready to deploy.*
