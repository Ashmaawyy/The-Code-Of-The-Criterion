# Deepseek-R1:8b Integration - Visual Diagrams

## Complete System Architecture

```
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                    THE CRITERION + DEEPSEEK-R1:8B                         ║
║                     Complete Reasoning System                             ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER INPUT LAYER                                  │
│                                                                             │
│  Natural Language Query:                                                    │
│  "Should we eliminate all privacy regulations to reduce costs?"            │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
                      ╔═══════════════════╗
                      ║   OLLAMA SERVER   ║
                      ║  (localhost:11434)║
                      ╚═════════┬═════════╝
                               │
                               ▼
        ╔══════════════════════════════════════════════════════════════╗
        ║                    LAYER 2: LLM SEMANTIC EXTRACTION          ║
        ║                      deepseek-r1:8b                         ║
        ║                                                              ║
        ║  OllamaLLMBridge                                             ║
        ║  ├─ extract_semantic_meaning(query)                          ║
        ║  ├─ _build_extraction_prompt()                               ║
        ║  ├─ _call_ollama()                                           ║
        ║  └─ _parse_extraction_response()                             ║
        ║                                                              ║
        ║  Input: Natural language query                               ║
        ║  Process: Chain-of-thought reasoning                         ║
        ║  Output: Structured system_data                              ║
        ║                                                              ║
        ║  Extracts:                                                   ║
        ║  ✓ Domain (economic/social/spiritual/etc)                   ║
        ║  ✓ Hidden assumptions                                        ║
        ║  ✓ True intent behind proposal                               ║
        ║  ✓ Real beneficiaries                                        ║
        ║  ✓ Dismissed harms                                           ║
        ╚══════════════════════════════┬═══════════════════════════════╝
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │   SYSTEM DATA (JSON)    │
                         │                         │
                         │  {                      │
                         │    "domain": "economic" │
                         │    "assumptions": [...] │
                         │    "intent": "..."      │
                         │    "beneficiaries": [...│
                         │    "dismissed_harms":[..│
                         │  }                      │
                         └────────┬────────────────┘
                                  │
                                  ▼
        ╔════════════════════════════════════════════════════════════╗
        ║          LAYER 5: CRITERION REASONING ENGINE               ║
        ║                  6-Phase Pipeline                          ║
        ║                                                            ║
        ║  ┌──────────────────────────────────────────────────────┐ ║
        ║  │ PHASE 1: SCAN                                        │ ║
        ║  │ Domain identification and context detection          │ ║
        ║  │ Output: Primary & secondary domains, reasoning      │ ║
        ║  └──────────────────────────────────────────────────────┘ ║
        ║                         ↓                                  ║
        ║  ┌──────────────────────────────────────────────────────┐ ║
        ║  │ PHASE 2: EXTRACT                                     │ ║
        ║  │ Deep assumption analysis and intent parsing          │ ║
        ║  │ Output: Assumption types, inferred intent            │ ║
        ║  └──────────────────────────────────────────────────────┘ ║
        ║                         ↓                                  ║
        ║  ┌──────────────────────────────────────────────────────┐ ║
        ║  │ PHASE 3: MIRROR (Axiom Compliance)                  │ ║
        ║  │ Check against 5 foundational axioms                  │ ║
        ║  │ Output: Violations, critical issues                  │ ║
        ║  │                                                       │ ║
        ║  │ Axioms:                                              │ ║
        ║  │ 1. Transcendence Necessity                           │ ║
        ║  │ 2. Final Court Necessity                             │ ║
        ║  │ 3. Design vs Accident                                │ ║
        ║  │ 4. Definition of Normal                              │ ║
        ║  │ 5. Network Effect                                    │ ║
        ║  └──────────────────────────────────────────────────────┘ ║
        ║                         ↓                                  ║
        ║  ┌──────────────────────────────────────────────────────┐ ║
        ║  │ PHASE 4: GATES (Survival Filters)                   │ ║
        ║  │ Apply 4 critical gates                               │ ║
        ║  │ Output: Gate scores, pass/fail status                │ ║
        ║  │                                                       │ ║
        ║  │ Gates:                                               │ ║
        ║  │ 1. Source Integrity    (Gate 1: 0/10)               │ ║
        ║  │ 2. Structural Consistency (Gate 2: 3/10)            │ ║
        ║  │ 3. Mediation Zeroing   (Gate 3: 5/10)               │ ║
        ║  │ 4. Origin Aware        (Gate 4: CRITICAL - FAIL)    │ ║
        ║  └──────────────────────────────────────────────────────┘ ║
        ║                         ↓                                  ║
        ║  ┌──────────────────────────────────────────────────────┐ ║
        ║  │ PHASE 5: CONSEQUENCES (Network Effects)             │ ║
        ║  │ Predict ripple effects through systems               │ ║
        ║  │ Output: Affected domains, harm scale, tipping points │ ║
        ║  └──────────────────────────────────────────────────────┘ ║
        ║                         ↓                                  ║
        ║  ┌──────────────────────────────────────────────────────┐ ║
        ║  │ PHASE 6: VERDICT (Final Judgment)                   │ ║
        ║  │ Synthesize all phases into judgment                  │ ║
        ║  │ Output: SURVIVE/FAIL, reasoning, recommendations     │ ║
        ║  └──────────────────────────────────────────────────────┘ ║
        ║                                                            ║
        ╚════════════════════════════┬═════════════════════════════╝
                                     │
                                     ▼
        ╔═══════════════════════════════════════════════════════════╗
        ║              COMPLETE ANALYSIS OUTPUT                     ║
        ║                                                           ║
        ║  ✓ All 6 phases completed                                ║
        ║  ✓ Axiom violations identified (3 found)                 ║
        ║  ✓ Gate status evaluated (1 critical fail)               ║
        ║  ✓ Network effects predicted                              ║
        ║  ✓ Chain-of-thought reasoning included                   ║
        ║                                                           ║
        ║  Final Verdict: FAIL                                     ║
        ║  Reason: Violates axiom 2 (Final Court) & axiom 4        ║
        ║          (Definition of Normal)                          ║
        ║  Critical Issue: Creates unaccountable data access       ║
        ║  Recommendation: Implement robust privacy regulations    ║
        ║                                                           ║
        ╚═══════════════════════════════════════════════════════════╝
```

## Data Flow Diagram

```
┌──────────────────────┐
│   User Query         │
│   (Natural Language) │
└──────────┬───────────┘
           │
           ▼
    ╔──────────────╗
    │  Ollama API  │
    ║  deepseek    ║
    ║  -r1:8b      ║
    ╚──────┬───────╝
           │
           ▼
    ┌─────────────────┐
    │  Extraction     │
    │  Prompt         │
    │                 │
    │  "Extract:      │
    │   - domain      │
    │   - assumptions │
    │   - intent      │
    │   - etc..."     │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  LLM Thinking   │
    │  (Chain of      │
    │   Thought)      │
    │                 │
    │  deepseek-r1:8b │
    │  reasons        │
    │  through the    │
    │  proposal...    │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  JSON Response  │
    │  {              │
    │   "domain":"..  │
    │   "assumptions" │
    │   "intent":"... │
    │  }              │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────────────────────────────┐
    │  OllamaLLMBridge._parse_extraction()   │
    │  Validate & structure response          │
    └────────┬────────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────────┐
    │  system_data dict                       │
    │  (Structured, validated, ready)         │
    └────────┬────────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────────┐
    │  CriterionPipeline.evaluate()           │
    │  Pass to reasoning engine               │
    └────────┬────────────────────────────────┘
             │
             ├─→ Phase 1: SCAN
             │   (domain identification)
             │
             ├─→ Phase 2: EXTRACT
             │   (assumption analysis)
             │
             ├─→ Phase 3: MIRROR
             │   (axiom checking)
             │
             ├─→ Phase 4: GATES
             │   (survival filtering)
             │
             ├─→ Phase 5: CONSEQUENCES
             │   (network effects)
             │
             └─→ Phase 6: VERDICT
                 (final judgment)
             │
             ▼
    ┌─────────────────────────────────────────┐
    │  Complete Analysis Dict                 │
    │  - Reasoning phases (all 6)             │
    │  - Axiom violations                     │
    │  - Gate scores & status                 │
    │  - Network effect predictions           │
    │  - Chain-of-thought reasoning           │
    │  - Final verdict & recommendations      │
    └─────────────────────────────────────────┘
```

## Interface Stack

```
┌────────────────────────────────────────────────────────┐
│                   APPLICATION CODE                    │
│                                                        │
│  Your program using Criterion + deepseek             │
└──────────────┬─────────────────────────────────────────┘
               │
               ▼
        ┌──────────────────────────────────────────┐
        │  INTERFACE LAYER (3 options)             │
        │                                          │
        │  1) analyze_with_deepseek(query)        │
        │     One-liner, simple usage              │
        │                                          │
        │  2) pipeline.evaluate_with_deepseek()   │
        │     Integration-friendly                 │
        │                                          │
        │  3) Direct bridge + pipeline             │
        │     Full control, step-by-step           │
        │                                          │
        └──────────────┬───────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────────┐
        │         INTEGRATION LAYER                │
        │                                          │
        │  • OllamaLLMBridge                       │
        │  • CriterionPipeline                     │
        │  • Error handling & fallbacks            │
        │                                          │
        └──────────────┬───────────────────────────┘
                       │
                       ├─→ Ollama API
                       │   (deepseek-r1:8b)
                       │
                       └─→ Reasoning Engine
                           (All 6 phases)
```

## Execution Timeline

```
Timeline: Query to Verdict

T+0s:     User calls: analyze_with_deepseek(query)
          ↓
T+0.1s:   OllamaLLMBridge initialized
          Ollama connection verified ✓
          ↓
T+0.2s:   Extraction prompt built
          ↓
T+0.3s:   API call to Ollama
          deepseek-r1:8b begins reasoning...
          ↓
T+15s:    deepseek-r1:8b outputs reasoning
          (includes chain-of-thought)
          ↓
T+15.1s:  JSON response parsed
          Validation & structure ✓
          ↓
T+15.2s:  system_data ready
          ↓
T+15.3s:  CriterionPipeline.evaluate() called
          ↓
T+15.4s:  Phase 1 SCAN completes
          ↓
T+15.5s:  Phase 2 EXTRACT completes
          ↓
T+15.6s:  Phase 3 MIRROR (axiom check) completes
          ↓
T+15.7s:  Phase 4 GATES (filters) completes
          ↓
T+15.8s:  Phase 5 CONSEQUENCES (effects) completes
          ↓
T+15.9s:  Phase 6 VERDICT (judgment) completes
          ↓
T+16.0s:  Complete analysis dict returned
          ↓
T+16.1s:  Result ready for user

Total Time: ~16 seconds

Breakdown:
- LLM Extraction: 15 seconds (95%)
- Reasoning: 1 second (5%)
```

## Integration Points Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    YOUR APPLICATION                         │
└────────────────────┬─────────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
         ▼           ▼           ▼
     Interface Options:
     
     ┌──────────────────────────────────────┐
     │  analyze_with_deepseek()             │
     │  Simple, recommended for quick use   │
     │  Returns: complete analysis dict     │
     └──────────────┬───────────────────────┘
                    │
                    ▼
     ┌──────────────────────────────────────┐
     │  CriterionPipeline                   │
     │  .evaluate_with_deepseek()           │
     │  Recommended for application code    │
     │  Returns: complete analysis dict     │
     └──────────────┬───────────────────────┘
                    │
                    ▼
     ┌──────────────────────────────────────┐
     │  OllamaLLMBridge + Pipeline          │
     │  Direct usage, full control          │
     │  Best for custom processing          │
     └──────────────┬───────────────────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
         ▼                     ▼
    ┌──────────────┐    ┌──────────────────┐
    │  Ollama API  │    │  Reasoning       │
    │              │    │  Engine          │
    │ deepseek     │    │                  │
    │ -r1:8b       │    │ 6 phases         │
    │              │    │ 5 axioms         │
    │              │    │ 4 gates          │
    └──────────────┘    └──────────────────┘
```

## Error Handling Flow

```
User Query
    ↓
    ├─→ Try: Connect to Ollama
    │   ├─ Success? Continue ✓
    │   └─ Fail? ConnectionError
    │       └─ Message: "Ollama not running"
    │       └─ Suggestion: "Run: ollama serve"
    │       └─ Fallback: Return default system_data
    │
    ├─→ Try: Extract semantics
    │   ├─ Success? Continue ✓
    │   ├─ JSON parse fail? 
    │   │   └─ Fallback: Conservative defaults
    │   └─ Timeout? 
    │       └─ Return partial result + error message
    │
    └─→ Try: Run reasoning
        ├─ Success? Return complete analysis ✓
        └─ Fail? 
            └─ Return best-effort result + error
```

## Deployment Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   PRODUCTION DEPLOYMENT                 │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Your Application                         │  │
│  │         (Uses The Criterion Framework)           │  │
│  └──────────┬───────────────────────────────────────┘  │
│             │                                           │
│             ▼                                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │  The Criterion Framework                        │  │
│  │  ├─ evaluation/llm_integration.py               │  │
│  │  ├─ evaluation/pipeline.py                      │  │
│  │  ├─ evaluation/reasoning_engine.py              │  │
│  │  └─ evaluation/gates.py                         │  │
│  └──────────┬───────────────────────────────────────┘  │
│             │                                           │
│  ┌──────────┴──────────────────────────────────────┐   │
│  │                                                 │    │
│  ▼                                                 ▼    │
│  ┌──────────────────────┐        ┌──────────────┐     │
│  │   Ollama Server      │        │ Local Files  │     │
│  │ (port 11434)         │        │ axioms.json  │     │
│  │                      │        │ gates.py     │     │
│  │ deepseek-r1:8b       │        └──────────────┘     │
│  │ (running in Docker   │                             │
│  │  or native)          │                             │
│  └──────────────────────┘                             │
│                                                        │
└──────────────────────────────────────────────────────────┘

All components run locally (no external API calls)
No data sent outside the machine
Zero API costs
Complete control and privacy
```

---

These diagrams show:
- **Complete System**: Full flow from query to verdict
- **Data Flow**: Step-by-step processing
- **Interface Stack**: How code connects layers
- **Execution Timeline**: What takes the most time
- **Integration Points**: Where to plug in your code
- **Error Handling**: How failures are managed
- **Deployment**: How it all fits together in production
