# Furqan Model Training — Product Requirements Document
## Training on Tokenized Quran Data with Unsloth
### Version 1.0

---

**Project:** Al-Furqan (الفرقان) — Axiom-Anchored Reasoning Engine
**Document Type:** Product Requirements Document (PRD)
**Version:** 1.0
**Date:** April 5, 2026
**Author:** Muhammad Al-Ashmawy + Arif AI
**Classification:** Open project
**Status:** Approved for Implementation

---

## 1. Executive Summary

We are training a specialized open-source LLM — **Furqan-27B** — that learns
the Quran's *reasoning architecture*: how it transitions between ideas, builds
arguments, and maintains logical robustness across topics.  The model does NOT
learn to mimic the Quran's text or sound.

**Input:** 5-level tokenized Quran data (6,236 verses x 5 token layers) +
2,487 Criterion training pairs from lesson transcripts.

**Output:** A local, private, fast reasoning model that has internalized
the Quran's logical patterns (transitions, argument structures, evidence
chains) and can **apply them to real-world scenarios** — evaluating
policies, systems, claims, and human situations through the same
reasoning architecture the Quran uses.

**Method:** Supervised Fine-Tuning (SFT) + Direct Preference Optimization
(DPO) via Unsloth on Qwen3.5-27B, deployed locally on consumer GPU.

---

## 2. Problem Statement

### What Exists Today

- A 5-level Quran tokenizer producing ground-truth tokens at certainty=1.0
- 2,487 Criterion training pairs (scan/mirror/verdict format)
- 67 KB entries for Surat Al-An'am Episode 1
- A complete RAG pipeline with 4 KB search tools
- Human feedback system (4 verdicts)

### What's Missing

- No fine-tuned model — all reasoning done via external API (Claude/Qwen)
- API calls are slow (50+ seconds), expensive (per-token), and privacy-leaking
- The LLM doesn't understand *how* the Quran reasons — it just follows prompts
- No model that has internalized the logical transition patterns

### What This Solves

A fine-tuned Furqan-27B model that:
1. **Thinks like the Quran reasons** — internalizes transition patterns,
   argument structures, evidence chains from the tokenized ground truth
2. **Applies these patterns to the real world** — evaluates human-world
   scenarios (economic policies, social systems, philosophical claims,
   ethical dilemmas) using the same logical chain the Quran uses
3. **Uses KB tools natively** — trained on tool-calling examples
4. **Runs locally** — 5-15s response time on RTX 4090, zero API cost
5. **Preserves privacy** — data never leaves the machine

---

## 3. Core Training Objective

> Teach the LLM the Quran's reasoning architecture — specifically how it
> transitions between ideas with smooth logical robustness — then train it
> to **apply those same patterns to real-world human scenarios**.
>
> Tafsir questions are the easy baseline (Phase 1).  The real test is
> whether the model can evaluate a modern economic policy, a social system,
> or a philosophical claim using the same logical chain it learned from
> the Quran's tokenized structure.

### What the Model MUST Learn

| Capability | Source | Weight in Reward |
|------------|--------|-----------------|
| **Idea transitions** — how to move between concepts smoothly | TransitionToken (Level 3) | 25% |
| **Logical structure** — premise → evidence → conclusion | LogicToken (Level 2C) | 25% |
| **Semantic coherence** — staying on domain, not drifting | SemanticToken (Level 2B) | 20% |
| **Root/meaning consistency** — shared roots = shared meaning | RootToken (Level 2A) | 20% |
| **Surface coherence** — natural word flow | WordToken (Level 1) | 10% |

### What the Model MUST NOT Learn

- Phonetic patterns (tajweed, IPA, pronunciation) — **removed from tokenizer**
- Surface-level text mimicry of Quranic verses
- Generating text that could be confused with Quran

---

## 4. Model Selection

### Primary: Qwen3.5-27B

| Attribute | Value |
|-----------|-------|
| **Parameters** | 27B (dense) |
| **Context window** | 262,144 tokens (native) |
| **Arabic capability** | #1 on Open Arabic LLM Leaderboard |
| **Reasoning** | Built-in thinking mode with chain-of-thought |
| **Tool calling** | Native function calling (Qwen3-Coder XML format) |
| **License** | Apache 2.0 (fully permissive, commercial) |
| **Unsloth support** | First-class (Unsloth + Qwen team collaboration) |
| **VRAM (training)** | ~40GB with 16-bit LoRA on A100 80GB |
| **VRAM (inference)** | ~16GB at Q4_K_M (fits RTX 4090) |
| **Speed (inference)** | 29-35 tok/s on RTX 3090 |

**Why Qwen3.5-27B:**
1. Best Arabic of any open model — critical for Classical Quranic Arabic
2. 262K context handles full surahs + KB results + reasoning chains
3. Native thinking mode aligns with axiom-guided structured reasoning
4. Apache 2.0 — no usage caps, no restrictions
5. Proven Unsloth ecosystem — 16-bit LoRA, not lossy QLoRA
6. Fits on consumer hardware for inference (RTX 4090)

### Alternative: Qwen3.5-9B (Budget / Rapid Iteration)

| Attribute | Value |
|-----------|-------|
| **Parameters** | 9B (dense) |
| **VRAM (training)** | ~16GB QLoRA (fits RTX 4090) |
| **VRAM (inference)** | ~6GB at Q4_K_M |
| **Use case** | Fast prototyping, validate pipeline before scaling to 27B |

### Alternative: Gemma 4 31B (Best Tool Calling)

| Attribute | Value |
|-----------|-------|
| **Parameters** | 31B (dense) |
| **Context** | 256K |
| **License** | Apache 2.0 |
| **Strength** | Best-in-class native tool calling |
| **Weakness** | Arabic weaker than Qwen; Unsloth support just released (April 2) |
| **Use case** | If tool-calling quality is the bottleneck after Qwen fine-tuning |

### Reasoning Teacher: DeepSeek-R1-Distill-Qwen-32B

| Attribute | Value |
|-----------|-------|
| **Parameters** | 32B (dense, Qwen 2.5 base) |
| **License** | Apache-2.0 |
| **Strength** | Best reasoning in 32B class (outperforms o1-mini) |
| **Use case** | Generate Arabic chain-of-thought traces as synthetic training data |

### Rejected Models

| Model | Reason |
|-------|--------|
| Llama 4 Scout (109B) | ~71GB VRAM for QLoRA at 2K context — impractical |
| Llama 4 Maverick (400B) | Cannot fine-tune on available hardware |
| DeepSeek V3.2 (671B) | Cannot fine-tune; API-only |
| Mistral Small 3.1 (24B) | Arabic weaker than Qwen at same size |

---

## 5. Training Data

### Data Source 1: Tokenized Quran (Ground Truth)

| Metric | Value |
|--------|-------|
| **Verses** | 6,236 |
| **Token levels** | 5 (Word, Root, Semantic, Logic, Transition) |
| **Certainty** | 1.0 (immutable ground truth) |
| **ES index** | `furqan_quran_tokens` |
| **Fields per verse** | ~125+ across all token levels |

**Used for:** Reward signal computation during DPO, and for generating
transition-aware training examples.

### Data Source 2: Criterion Training Pairs

| Metric | Value |
|--------|-------|
| **Total pairs** | 2,487 |
| **Format** | JSONL (scan/mirror/verdict structure) |
| **Types** | verse-verse (cross-surah), verse-verse (intra-surah), verse-hadith |
| **Relation types** | 9 (EXPLAINS, SUPPORTS, RESTRICTS, CONTEXTUALIZES, etc.) |
| **Source** | 17 lesson transcripts + tafsir integration |
| **File** | `data/lessons/training_pairs/criterion_training_all.jsonl` (9 MB) |

**Used for:** SFT conversation examples (converted to chat format).

### Data Source 3: Pipeline Responses + Human Feedback (To Collect)

| Metric | Target |
|--------|--------|
| **SFT examples** | 500+ reviewed (correct/correct_notes) |
| **DPO pairs** | 300+ (correct vs wrong for same question) |
| **Source** | Live pipeline usage + human review |

**Used for:** Phase 2 SFT enhancement and Phase 3 DPO training.

### Data Source 4: Synthetic Reasoning Traces (To Generate)

| Metric | Target |
|--------|--------|
| **Arabic CoT traces** | 1,000+ |
| **Generator** | DeepSeek-R1-Distill-Qwen-32B |
| **Topics** | Quran verse relationships, logical patterns, KB-grounded questions |

**Used for:** Reasoning quality enhancement in SFT (Phase 1 — tafsir baseline).

### Data Source 5: Real-World Scenario Evaluations (To Generate)

This is the **most important data source** — it is what separates Furqan
from a tafsir chatbot.

| Metric | Target |
|--------|--------|
| **Real-world scenarios** | 500+ |
| **Domains** | Economics, governance, ethics, social systems, philosophy, science claims, justice |
| **Format** | Scenario → Quranic logical analysis → verdict with gate scores |
| **Generator** | Human-curated scenarios + DeepSeek-R1 reasoning + human review |

**Used for:** Teaching the model to transfer Quranic reasoning patterns to
novel human-world situations.

**Example domains and scenario types:**

| Domain | Example Scenario | Quranic Pattern Applied |
|--------|-----------------|----------------------|
| **Economics** | "Evaluate a debt-based monetary system where money is created through interest" | Restriction pattern (ما...إلا) → what is excluded reveals the flaw |
| **Governance** | "Analyze a system where legislative power has no accountability mechanism" | Condition-response (إذا...ف) → if power then accountability must follow |
| **Ethics** | "A society normalizes small lies for social harmony" | Escalation pattern (تصعيد) → small compromise leads to systemic corruption |
| **Social** | "Evaluate individualism as a social operating system" | Contrast pattern (مقابلة) → individual vs collective, evidence from both sides |
| **Philosophy** | "Can pure empiricism account for moral obligations?" | Evidence-shift → from observation to ought requires a bridge (logical gap) |
| **Justice** | "A legal system where the wealthy receive lighter sentences" | Adversative (بل/لكن) → stated principle vs actual practice |
| **Science claims** | "The universe is self-caused" | Reductio (assume P → contradiction → not P) → infinite regress |

**Scenario format:**

```json
{
  "scenario": "A government proposes a policy where...",
  "domain": "governance",
  "analysis": {
    "transition_pattern": "condition → evidence_shift → contrast → conclusion",
    "logical_chain": [
      {"step": "premise", "operator": "condition", "content": "If a system claims X..."},
      {"step": "evidence", "operator": "evidence_shift", "content": "But the observable outcome is Y..."},
      {"step": "contrast", "operator": "adversative", "content": "This contradicts the stated principle because..."},
      {"step": "conclusion", "operator": "consequence", "content": "Therefore the system fails Gate 2 (Structural Consistency)"}
    ],
    "gates_applied": ["source_integrity", "structural_consistency"],
    "axioms_invoked": ["design_vs_accident", "dependency_lock"],
    "quranic_parallel": "This follows the same reasoning pattern as 6:80-81 where..."
  },
  "verdict": "The policy fails Structural Consistency because..."
}
```

**Key principle:** Every real-world analysis must trace back to a specific
Quranic reasoning *pattern* (transition type, logical operator chain) — not
to a specific verse.  The model learns the **architecture**, then applies it.

---

## 6. Training Approach

### Phase 1: Data Preparation (Weeks 1-3)

**Stage A — Tafsir Baseline Data:**
- Convert 2,487 Criterion pairs to Unsloth chat format
- Generate 1,000+ synthetic CoT traces using DeepSeek-R1
- Build transition-aware examples from tokenized Quran (verse-pair reasoning)

**Stage B — Real-World Scenario Data:**
- Curate 500+ real-world scenarios across 7+ domains (economics, governance,
  ethics, social, philosophy, justice, science claims)
- For each scenario, map the analysis to specific Quranic reasoning patterns
  (transition types, logical operator chains, gate evaluations)
- Generate with DeepSeek-R1 + heavy human curation (scenarios must be realistic)
- Each scenario traces to a Quranic reasoning *pattern* — not a specific verse

**Split:** 80% train / 10% validation / 10% test (stratified by domain)

### Phase 2: SFT Stage 1 — Tafsir Baseline (Weeks 4-5)

- Train on Criterion pairs + CoT traces + transition examples
- 16-bit LoRA via Unsloth on A100 80GB
- This teaches the model the Quran's reasoning patterns in their native context
- **Gate:** Model must score >= 70% on tafsir benchmark before proceeding

### Phase 3: SFT Stage 2 — Real-World Transfer (Weeks 6-7)

- Continue SFT on real-world scenario data (mixed with tafsir to prevent forgetting)
- Lower learning rate (5e-5) for this stage — refine, don't overwrite
- This teaches the model to *apply* the patterns it learned to novel domains
- **Gate:** Model must correctly identify reasoning patterns in unseen scenarios

### Phase 4: DPO Alignment (Weeks 8-9)

- Build preference pairs from both tafsir AND real-world feedback
- DPO pairs include: strong analysis (with gate scores, pattern identification,
  Quranic parallel) vs weak analysis (generic, no logical chain, no gates)
- DPO with beta=0.1, 1 epoch on the Stage 2 SFT checkpoint

### Phase 5: Evaluation & Iteration (Weeks 10-11)

- **Tafsir benchmark:** 87 questions (baseline — should be easy by now)
- **Real-world benchmark:** 50+ unseen scenarios across all domains
- **Transfer test:** Scenarios in domains NOT seen during training
- A/B comparison: base Qwen3.5 vs SFT-Stage1 vs SFT-Stage2 vs DPO
- Human evaluation on: pattern identification, logical robustness, gate application

### Phase 6: Deployment (Week 12)

- Export to GGUF Q4_K_M for local inference
- Deploy via Ollama or vLLM on RTX 4090
- Integrate with existing FastAPI orchestrator

---

## 7. Reward Signal Formula

The model's reasoning output is scored against the Quran's 5-level
tokenization ground truth:

```
Score = 0.10*S_word + 0.20*S_root + 0.20*S_semantic + 0.25*S_logic + 0.25*S_transition

where:
  S_word       = sequence coherence (natural word flow)
  S_root       = root+pattern match (concept consistency)
  S_semantic   = semantic field coherence (staying on domain)
  S_logic      = logical structure match (argument quality)
  S_transition = idea-transition quality (smooth flow between concepts)
```

**50% of the reward** comes from logic + transition.  This forces the model
to learn reasoning architecture, not surface patterns.

---

## 8. Infrastructure Requirements

### Training Hardware

| Phase | GPU | VRAM | Time | Cloud Cost |
|-------|-----|------|------|-----------|
| Data prep | CPU | — | 2-4 hours | — |
| SFT (16-bit LoRA, 27B) | 1x A100 80GB | ~40GB | 4-8 hours | $30-60 |
| SFT (QLoRA, 9B prototype) | 1x RTX 4090 | ~16GB | 2-4 hours | — (local) |
| DPO (LoRA, 27B) | 1x A100 80GB | ~40GB | 2-4 hours | $20-40 |
| **Total training** | | | **8-16 hours** | **$50-100** |

### Inference Hardware

| Setup | GPU | VRAM | Speed |
|-------|-----|------|-------|
| Primary (27B Q4_K_M) | RTX 4090 | ~16GB | 29-35 tok/s |
| Budget (9B Q4_K_M) | RTX 3060 12GB | ~6GB | 50+ tok/s |
| Server (27B FP16) | A100 40GB | ~32GB | 40+ tok/s |

### Software Stack

| Component | Tool |
|-----------|------|
| Fine-tuning framework | Unsloth (16-bit LoRA) |
| LoRA adapters | PEFT (HuggingFace) |
| Quantization | bitsandbytes (4-bit for QLoRA path) |
| DPO training | TRL (HuggingFace) |
| Experiment tracking | Weights & Biases |
| Inference serving | Ollama / vLLM / SGLang |
| GGUF export | llama.cpp |

---

## 9. Success Criteria

### Quantitative — Tafsir Baseline

| Metric | Target | How Measured |
|--------|--------|-------------|
| Tafsir accuracy | >= 85% | Human review on 87-question benchmark |
| KB tool usage | >= 3 calls/question | Automated counting |
| Source attribution | >= 90% of responses | Automated check for citations |
| Transition quality | >= 4/5 | Human rating on idea flow |

### Quantitative — Real-World Application (The Real Test)

| Metric | Target | How Measured |
|--------|--------|-------------|
| Pattern identification | >= 80% | Does the model correctly identify which Quranic reasoning pattern applies? |
| Logical chain quality | >= 4/5 | Human rating: is the premise→evidence→conclusion chain valid? |
| Gate application | >= 75% | Does the model correctly apply survival gates to the scenario? |
| Cross-domain transfer | >= 70% | Accuracy on domains NOT seen during training |
| Axiom alignment | >= 4.5/5 | Human rating: are axioms invoked correctly and naturally? |
| Win rate vs base | >= 75% | Human preference (DPO vs base Qwen on real-world scenarios) |
| Latency (local) | <= 15 seconds | Time to complete response on RTX 4090 |

### Qualitative

- Model identifies the **reasoning pattern** before diving into analysis
- Model applies Quranic logical chains (condition→response, restriction,
  escalation, contrast) naturally to real-world situations
- Model self-checks against gates (Source-Integrity, Structural-Consistency,
  Mediation-Zeroing, Origin-Aware) as part of its reasoning
- Model cites the **pattern** it's applying, not just verses
  (e.g., "This follows a restriction pattern (ما...إلا)" not just "as in verse X")
- Model transitions between ideas smoothly — the same smoothness score (1.0)
  it learned from Quranic ground truth carries over to its own reasoning
- Model does NOT fall back to generic ethical platitudes — it reasons structurally

---

## 10. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| Data too small for 27B | High | Medium | Start with 9B prototype; use synthetic augmentation |
| Tool calling breaks after SFT | Medium | High | Dedicated tool-call training examples; eval at each phase |
| Arabic quality degrades | Low | High | Freeze early layers; validate on Arabic benchmarks |
| Overfitting to Al-An'am | High | Medium | Need episodes 2-23 before final model |
| Catastrophic forgetting | Medium | High | LoRA preserves base weights; test general Arabic after SFT |
| Transition scoring too coarse | Medium | Medium | Iterate on scoring function; add human evaluation |
| Cloud GPU unavailable | Low | Medium | RunPod / Lambda Labs / Vast.ai as backup providers |

---

## 11. Non-Goals (Explicit Exclusions)

- **No phonetic/tajweed training** — deliberately removed from tokenizer
- **No Quran text generation** — model must not generate Quranic verses
- **No multi-modal** — text-only (no audio/image for v1.0)
- **No real-time serving** — batch inference acceptable for v1.0
- **No multi-language** — Arabic-only responses for v1.0

---

## 12. Dependencies

| Dependency | Owner | Status |
|-----------|-------|--------|
| Tokenized Quran in ES (`furqan_quran_tokens`) | Encoder pipeline | Done |
| 2,487 Criterion training pairs | Lesson pipeline | Done |
| QAC morphology in ES | qac_extractor | Done |
| Elasticsearch running | Infrastructure | Done |
| A100 80GB access (cloud) | Engineering | Needed |
| Human reviewers for feedback | Research team | Needed |
| Episodes 2-23 transcripts | Research team | Needed for full model |

---

## 13. Timeline

| Week | Phase | Deliverable |
|------|-------|------------|
| 1-2 | Data Prep (Tafsir) | Criterion pairs → chat format, CoT traces, transition examples |
| 3 | Data Prep (Real-World) | 500+ real-world scenarios across 7+ domains, human-curated |
| 4 | Prototype | Furqan-9B prototype (Qwen3.5-9B, QLoRA, local GPU) |
| 5 | SFT Stage 1 | Furqan-27B tafsir baseline (A100, 16-bit LoRA) |
| 6-7 | SFT Stage 2 | Real-world transfer training (mixed data) |
| 8-9 | DPO | Preference pairs from both tafsir + real-world feedback |
| 10-11 | Evaluation | Tafsir benchmark + real-world benchmark + cross-domain transfer |
| 12 | Deployment | GGUF export, Ollama integration, model card |

**Total: ~12 weeks** from start to deployed local model.

---

## 14. Glossary

| Term | Definition |
|------|-----------|
| **SFT** | Supervised Fine-Tuning — teaching the model correct responses |
| **DPO** | Direct Preference Optimization — teaching the model to prefer correct over incorrect |
| **LoRA** | Low-Rank Adaptation — parameter-efficient fine-tuning |
| **QLoRA** | Quantized LoRA — LoRA on 4-bit quantized model (lower VRAM, slightly lower quality) |
| **Unsloth** | Open-source framework for fast LoRA training (2-5x speedup) |
| **GGUF** | File format for quantized LLM inference (used by llama.cpp/Ollama) |
| **TransitionToken** | Level 3 token capturing idea-to-idea flow in Quranic discourse |
| **Criterion** | The formal reasoning framework (scan/mirror/verdict) of Al-Furqan |

---

_Document generated: April 5, 2026 | Al-Furqan contributors_