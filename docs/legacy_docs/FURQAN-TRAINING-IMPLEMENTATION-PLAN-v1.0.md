# Furqan Model Training — Implementation Plan
## Technical Blueprint for SFT + DPO with Unsloth
### Version 1.0

---

**Project:** Al-Furqan (الفرقان)
**Date:** April 5, 2026
**Companion:** [FURQAN-TRAINING-PRD-v1.0.md](FURQAN-TRAINING-PRD-v1.0.md)
**Classification:** Open project

---

## 1. Architecture Overview

```
┌───────────────────────────────────────────────────────────────────┐
│                    TRAINING PIPELINE                               │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ① Data Sources                                                   │
│  ├── furqan_quran_tokens (ES) ─── 6,236 verses x 5 token levels  │
│  ├── criterion_training_all.jsonl ─── 2,487 training pairs        │
│  ├── DeepSeek-R1 ─── synthetic CoT reasoning traces               │
│  ├── Real-world scenarios ─── 500+ human-curated across 7 domains │
│  └── Pipeline feedback ─── human-reviewed responses                │
│                                                                    │
│  ② Data Preparation                                               │
│  ├── convert_criterion_to_chat.py ─── pairs → chat format         │
│  ├── generate_transition_examples.py ─── tokens → reasoning tasks │
│  ├── generate_synthetic_cot.py ─── R1 teacher → Arabic CoT        │
│  ├── generate_real_world_scenarios.py ─── scenarios → chat format  │
│  └── build_dpo_pairs.py ─── feedback → preference pairs            │
│                                                                    │
│  ③ Training (Two-Stage SFT)                                       │
│  ├── train_sft_stage1.py ─── Tafsir baseline (learn patterns)     │
│  ├── train_sft_stage2.py ─── Real-world transfer (apply patterns) │
│  └── train_dpo.py ─── TRL DPO on Stage 2 checkpoint               │
│                                                                    │
│  ④ Evaluation                                                     │
│  ├── eval_tafsir_benchmark.py ─── 87-question tafsir baseline     │
│  ├── eval_real_world.py ─── 50+ real-world scenario benchmark     │
│  ├── eval_transition_quality.py ─── score against token ground truth│
│  └── eval_ab_test.py ─── base vs Stage1 vs Stage2 vs DPO          │
│                                                                    │
│  ⑤ Deployment                                                     │
│  ├── export_gguf.py ─── merge LoRA + quantize to Q4_K_M          │
│  └── Ollama / vLLM ─── local serving on RTX 4090                 │
│                                                                    │
└───────────────────────────────────────────────────────────────────┘
```

---

## 2. Project Structure (New Directories)

```
al-furqan/
├── training/                          # NEW — all training code
│   ├── configs/
│   │   ├── sft_stage1_qwen35_27b.yaml # SFT Stage 1 (tafsir baseline)
│   │   ├── sft_stage2_qwen35_27b.yaml # SFT Stage 2 (real-world transfer)
│   │   ├── sft_qwen35_9b.yaml        # Prototype config (local GPU)
│   │   ├── dpo_qwen35_27b.yaml       # DPO training config
│   │   └── eval_benchmark.yaml        # Evaluation config
│   ├── data/
│   │   ├── convert_criterion_to_chat.py
│   │   ├── generate_transition_examples.py
│   │   ├── generate_synthetic_cot.py
│   │   ├── generate_real_world_scenarios.py  # Real-world scenario builder
│   │   ├── build_dpo_pairs.py
│   │   └── data_stats.py              # Dataset statistics & validation
│   ├── train_sft_stage1.py            # SFT Stage 1: tafsir baseline
│   ├── train_sft_stage2.py            # SFT Stage 2: real-world transfer
│   ├── train_dpo.py                   # DPO training script
│   ├── eval/
│   │   ├── tafsir_benchmark.py        # Tafsir baseline benchmark
│   │   ├── real_world_benchmark.py    # Real-world scenario benchmark
│   │   ├── transition_scorer.py       # Score output against token ground truth
│   │   ├── ab_test.py                 # Base vs Stage1 vs Stage2 vs DPO
│   │   └── questions/
│   │       ├── tafsir_core_12.jsonl   # Core tafsir questions
│   │       ├── tafsir_extended_75.jsonl
│   │       └── real_world_50.jsonl    # Real-world scenarios benchmark
│   ├── export/
│   │   ├── merge_and_export.py        # Merge LoRA + GGUF export
│   │   └── deploy_ollama.sh           # Ollama model registration
│   └── requirements.txt               # Training-specific dependencies
├── data/
│   └── training/                      # NEW — prepared training data
│       ├── sft_train.jsonl
│       ├── sft_val.jsonl
│       ├── sft_test.jsonl
│       ├── dpo_train.jsonl
│       ├── dpo_val.jsonl
│       └── synthetic_cot.jsonl
```

---

## 3. Phase 1: Data Preparation

### 3.1 Convert Criterion Pairs to Chat Format

**Script:** `training/pipeline/converters/criterion_to_chat.py`

**Input:** `data/lessons/training_pairs/criterion_training_all.jsonl` (2,487 pairs)

**Output:** `data/training/sft_train.jsonl` (chat format)

**Conversion logic:**

Each Criterion pair (scan/mirror/verdict) becomes a multi-turn conversation:

```json
{
  "conversations": [
    {
      "role": "system",
      "content": "أنت عالم متخصص في تفسير القرآن الكريم...\n\n## المسلمات (Axioms)\n- Design vs. Accident: ترتيب الآيات مقصود لا عشوائي\n- Dependency Lock: كل آية تعتمد على سياق ما قبلها\n- Structural Consistency: البنية المنطقية متسقة\n- Origin-Aware: المصدر متعالٍ\n\n## بوابات الجودة (Gates)\n- Source-Integrity: هل المعلومات من مصادر موثقة؟\n- Structural-Consistency: هل التحليل متسق منطقياً؟\n- Mediation-Zeroing: هل تم تجنب التأويل الذاتي؟\n- Origin-Aware: هل تم الرجوع للمصدر الأصلي؟\n\n## الأدوات المتاحة\n- search_kb_by_verse(verse_ref) — البحث في قاعدة المعرفة بالآية\n- search_kb_by_topic(topic) — البحث بالموضوع\n- search_kb_by_relation(verse_ref, relation_type) — البحث بنوع العلاقة\n- get_verse_context(verse_ref, range) — السياق المحيط بالآية"
    },
    {
      "role": "user",
      "content": "حلل العلاقة بين الآية [6:80] والآية [6:81] من سورة الأنعام"
    },
    {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {"function": {"name": "search_kb_by_verse", "arguments": "{\"verse_ref\": \"6:80\"}"}}
      ]
    },
    {
      "role": "tool",
      "content": "## نتائج البحث عن 6:80\n[scan.source_text data + tafsir_context]"
    },
    {
      "role": "assistant",
      "content": "[mirror.reasoning_from_scholar + verdict with relation_type, confidence, evidence_basis]"
    }
  ]
}
```

**Key decisions:**
- System prompt includes axioms, gates, and tool definitions (always present)
- Tool calls are synthesized from the scan data (what tools SHOULD have been called)
- Tool responses are built from the scan context (tafsir, verse text)
- Final response combines mirror reasoning + verdict

### 3.2 Generate Transition-Aware Examples

**Script:** `training/pipeline/generators/transition_examples.py`

**Input:** `furqan_quran_tokens` ES index

**Output:** Appended to `data/training/sft_train.jsonl`

Creates training examples that teach the model HOW the Quran transitions
between ideas.  For each verse with interesting transitions:

```json
{
  "conversations": [
    {
      "role": "system",
      "content": "[same system prompt]"
    },
    {
      "role": "user",
      "content": "كيف ينتقل القرآن من فكرة الألوهية إلى فكرة الخلق في الآية 6:1؟"
    },
    {
      "role": "assistant",
      "content": "## تحليل الانتقال\n\nالانتقال من **الألوهية** (divinity) إلى **الخلق** (creation) يتم عبر:\n\n1. **نوع الانتقال:** pivot (انتقال موضوعي) — الفاء السببية تربط بين الحمد لله والخلق\n2. **البنية المنطقية:** مقدمة (الحمد) → دليل (الخلق) → نتيجة (الهداية)\n3. **عمق الخطاب:** المستوى 0 (بداية السورة) → يتصاعد مع تراكم الأدلة\n4. **السلاسة:** 1.0 — انتقال سلس تماماً لأن الخلق دليل على استحقاق الحمد\n\nهذا النمط (pivot من divinity إلى creation) يتكرر في القرآن كنمط استدلالي أساسي."
    }
  ]
}
```

**Transition patterns to extract:**
- Verses with `transition_type != "continuation"` (interesting shifts)
- Verses with `returns_to != -1` (callbacks to earlier ideas)
- Verses with `discourse_depth > 0` (nested arguments)
- Cross-verse semantic field changes (source_idea != target_idea)

**Target:** 500-1,000 transition-focused examples.

### 3.3 Generate Synthetic CoT Traces

**Script:** `training/pipeline/generators/synthetic_cot.py`

**Input:** Questions about verse relationships + KB data

**Generator:** DeepSeek-R1-Distill-Qwen-32B (via Ollama or API)

**Output:** `data/training/synthetic_cot.jsonl`

**Process:**
1. Generate diverse questions from KB entries (67 entries → 5-10 questions each)
2. For each question, prompt R1 with the KB context and axioms
3. R1 produces Arabic chain-of-thought reasoning
4. Filter: keep only responses that cite sources and follow axiom structure
5. Convert to chat format with tool calls

**Target:** 1,000+ high-quality synthetic traces.

### 3.4 Generate Real-World Scenarios

**Script:** `training/pipeline/generators/real_world.py`

**Input:** Human-curated scenario templates + Quranic reasoning patterns

**Generator:** DeepSeek-R1 for initial drafts, heavy human curation

**Output:** `data/training/real_world_scenarios.jsonl`

**Process:**
1. Define 7+ domains: economics, governance, ethics, social systems,
   philosophy, justice, science claims
2. For each domain, write 10-20 base scenarios (human-authored)
3. For each scenario, identify which Quranic reasoning pattern applies
   (from the tokenized transition/logic types)
4. Use DeepSeek-R1 to generate the full analysis following the pattern:
   - Identify the reasoning pattern (e.g., "restriction", "reductio", "contrast")
   - Build the logical chain using that pattern's operators
   - Apply relevant gates (Source-Integrity, Structural-Consistency, etc.)
   - Reference the pattern (NOT specific verses) as the analytical framework
5. Human review: verify logical soundness, pattern correctness, gate application
6. Augment: paraphrase scenarios, vary complexity, add edge cases

**Example conversation:**

```json
{
  "conversations": [
    {
      "role": "system",
      "content": "[Axioms + Gates + reasoning patterns]"
    },
    {
      "role": "user",
      "content": "حلل نظاماً اقتصادياً يعتمد على الدَّين بالفائدة كآلية أساسية لخلق النقود"
    },
    {
      "role": "assistant",
      "content": "## نمط التحليل: تقييد (restriction pattern — ما...إلا)\n\n### البنية المنطقية:\n\n1. **المقدمة (premise):** النظام يدّعي أنه يخلق قيمة اقتصادية\n2. **التقييد (restriction):** لكن آلية الخلق هي الدين — أي أن القيمة المُنتَجة مشروطة بالتزام مستقبلي\n3. **الفحص (evidence_shift):** إذا تتبعنا السلسلة: قرض → فائدة → قرض لسداد الفائدة → فائدة أعلى...\n4. **النتيجة (consequence):** تسلسل لانهائي — النظام يتطلب نمواً لا نهائياً في بيئة محدودة\n\n### تطبيق البوابات:\n- **بوابة 2 (Structural Consistency):** فشل — النظام لا يستطيع تفسير كيف تُسدَّد كل الديون إذا كان المال نفسه مُستدان\n- **بوابة 3 (Mediation Zeroing):** تحذير — الاعتماد على \"ثقة السوق\" كوسيط معرفي بشري\n\n### النمط القرآني المُطبَّق:\nنمط التقييد (ما...إلا) يكشف أن ما يبدو نظاماً مفتوحاً هو في الحقيقة مقيَّد ببنية واحدة — الدَّين. هذا النمط يُستخدم قرآنياً لكشف الادعاءات التي تبدو شاملة لكنها في الحقيقة مُقيَّدة بشرط مخفي."
    }
  ]
}
```

**Target:** 500+ scenarios (70+ per domain).

### 3.5 Build DPO Preference Pairs

**Script:** `training/pipeline/generators/dpo_pairs.py`

**Input:** Human feedback (correct vs wrong responses)

**Output:** `data/training/dpo_train.jsonl`

**Pair sources:**
1. Same question, two pipeline runs → one correct, one wrong
2. With-KB response vs without-KB response (same question)
3. Correct response vs synthetically degraded version (strip citations, remove tool calls)

**Format:**
```json
{
  "prompt": "ما علاقة الآية 6:5 بيوم بدر؟",
  "chosen": "[response with KB, citations, axiom reasoning]",
  "rejected": "[response without KB, generic, no sources]"
}
```

**Target:** 300+ preference pairs.

---

## 4. SFT Training (Two Stages)

### 4.1 Prototype on Qwen3.5-9B (Local GPU)

**Config:** `training/configs/sft_qwen35_9b.yaml`

```yaml
# Prototype — validate pipeline before scaling to 27B
model_name: "unsloth/Qwen3.5-9B"
max_seq_length: 8192
load_in_4bit: true

# LoRA
lora_r: 32
lora_alpha: 64
lora_target_modules: ["q_proj", "k_proj", "v_proj", "o_proj",
                       "gate_proj", "up_proj", "down_proj"]
lora_dropout: 0.05

# Training
num_train_epochs: 3
per_device_train_batch_size: 2
gradient_accumulation_steps: 4
learning_rate: 2.0e-4
lr_scheduler_type: "cosine"
warmup_ratio: 0.05
weight_decay: 0.01
bf16: true
logging_steps: 10
save_steps: 100
eval_steps: 100

# Data
dataset_path: "data/training/sft_train.jsonl"
val_dataset_path: "data/training/sft_val.jsonl"
chat_template: "qwen3"
```

**Hardware:** 1x RTX 4090 (24GB), ~2-4 hours
**Purpose:** Validate data pipeline, chat format, tool-call format, loss curve

### 4.2 SFT Stage 1: Tafsir Baseline (Cloud GPU)

**Config:** `training/configs/sft_stage1_qwen35_27b.yaml`

```yaml
# Stage 1 — Learn Quranic reasoning patterns from tafsir data
model_name: "unsloth/Qwen3.5-27B"
max_seq_length: 8192
load_in_4bit: false   # 16-bit LoRA (higher quality than QLoRA)

# LoRA
lora_r: 64
lora_alpha: 128
lora_target_modules: ["q_proj", "k_proj", "v_proj", "o_proj",
                       "gate_proj", "up_proj", "down_proj"]
lora_dropout: 0.0

# Training
num_train_epochs: 3
per_device_train_batch_size: 2
gradient_accumulation_steps: 8
learning_rate: 1.0e-4
lr_scheduler_type: "cosine"
warmup_ratio: 0.05
weight_decay: 0.01
bf16: true

# Data — tafsir + CoT + transition examples ONLY
dataset_path: "data/training/sft_stage1_train.jsonl"
val_dataset_path: "data/training/sft_stage1_val.jsonl"
chat_template: "qwen3"
```

**Hardware:** 1x A100 80GB, 4-8 hours (~$10-20)
**Gate:** Must score >= 70% on tafsir benchmark before proceeding to Stage 2.

### 4.3 SFT Stage 2: Real-World Transfer (Cloud GPU)

**Config:** `training/configs/sft_stage2_qwen35_27b.yaml`

```yaml
# Stage 2 — Apply learned patterns to real-world scenarios
model_name: "output/furqan-27b-stage1"   # ← start from Stage 1 checkpoint
max_seq_length: 8192
load_in_4bit: false

# LoRA — same architecture, continue from Stage 1
lora_r: 64
lora_alpha: 128

# Training — lower LR for refinement (don't overwrite Stage 1 patterns)
num_train_epochs: 2
per_device_train_batch_size: 2
gradient_accumulation_steps: 8
learning_rate: 5.0e-5           # ← half of Stage 1 LR
lr_scheduler_type: "cosine"
bf16: true

# Data — real-world scenarios MIXED with tafsir (prevent forgetting)
# Mix ratio: 60% real-world, 40% tafsir
dataset_path: "data/training/sft_stage2_train.jsonl"
val_dataset_path: "data/training/sft_stage2_val.jsonl"
chat_template: "qwen3"
```

**Hardware:** 1x A100 80GB, 3-6 hours (~$8-15)
**Gate:** Must correctly identify reasoning patterns in unseen real-world scenarios.

### 4.3 Training Script

**Script:** `training/train_sft.py`

```python
# Core training loop (pseudocode — full script in implementation)
from unsloth import FastLanguageModel
from trl import SFTTrainer

# 1. Load model with Unsloth
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=config.model_name,
    max_seq_length=config.max_seq_length,
    load_in_4bit=config.load_in_4bit,
)

# 2. Apply LoRA
model = FastLanguageModel.get_peft_model(
    model,
    r=config.lora_r,
    lora_alpha=config.lora_alpha,
    target_modules=config.lora_target_modules,
    lora_dropout=config.lora_dropout,
)

# 3. Load dataset
dataset = load_dataset("json", data_files={
    "train": config.dataset_path,
    "validation": config.val_dataset_path,
})

# 4. Train
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset["train"],
    eval_dataset=dataset["validation"],
    args=training_args,
)
trainer.train()

# 5. Save
model.save_pretrained("output/furqan-27b-sft")
```

---

## 5. Phase 3: DPO Training

### 5.1 DPO Config

**Config:** `training/configs/dpo_qwen35_27b.yaml`

```yaml
# DPO — preference optimization on SFT checkpoint
model_name: "output/furqan-27b-sft"   # start from SFT model
max_seq_length: 4096

# LoRA (same architecture, fresh adapter)
lora_r: 32
lora_alpha: 64

# DPO-specific
beta: 0.1                              # KL penalty coefficient
loss_type: "sigmoid"

# Training
num_train_epochs: 1
per_device_train_batch_size: 1
gradient_accumulation_steps: 16
learning_rate: 5.0e-5
lr_scheduler_type: "cosine"
bf16: true

# Data
dataset_path: "data/training/dpo_train.jsonl"
val_dataset_path: "data/training/dpo_val.jsonl"
```

**Hardware:** 1x A100 80GB, 2-4 hours

### 5.2 DPO Script

**Script:** `training/train_dpo.py`

Uses `trl.DPOTrainer` on the SFT checkpoint with preference pairs.

---

## 6. Evaluation (Two Tracks)

### 6.1 Track A: Tafsir Benchmark (Baseline)

**Script:** `training/eval/tafsir_benchmark.py`

**Questions:** 87 total (same as before — this is the easy baseline)

| Category | Count | Tests |
|----------|-------|-------|
| Core (verse relationships) | 12 | Basic tafsir Q&A accuracy |
| KB Coverage | 30 | Does the model use KB tools correctly? |
| Tool Usage | 20 | Does it select the right tool? |
| Axiom Alignment | 15 | Does it apply axioms? |
| Edge Cases | 10 | Questions outside KB |

**Expected:** >= 85% after Stage 1 SFT.  This should be the easy part.

### 6.2 Track B: Real-World Benchmark (The Real Test)

**Script:** `training/eval/real_world_benchmark.py`

**Questions:** 50+ real-world scenarios across 7+ domains

| Domain | Count | Example |
|--------|-------|---------|
| Economics | 8 | Evaluate interest-based monetary creation |
| Governance | 8 | Analyze accountability-free power structures |
| Ethics | 7 | Assess normalization of incremental compromise |
| Social systems | 7 | Evaluate individualism as operating principle |
| Philosophy | 7 | Can empiricism ground moral obligations? |
| Justice | 7 | Equal application of law across wealth classes |
| Science claims | 6 | Self-caused universe, random emergence of order |

**Metrics per response:**
- `pattern_identified` — did the model name the correct reasoning pattern?
- `logical_chain_valid` — is the premise→evidence→conclusion chain sound?
- `gates_applied` — which gates were invoked and were they appropriate?
- `pattern_not_verse` — does it cite the pattern, not just a verse?
- `no_generic_platitudes` — does it reason structurally, not moralistically?

**Cross-domain transfer test:** 10 additional scenarios from domains NOT
in the training set (e.g., technology ethics, environmental policy,
education systems).  This tests whether the model learned the *patterns*
or just memorized domain-specific answers.

### 6.3 Transition Quality Scorer

**Script:** `training/eval/transition_scorer.py`

Compares the model's reasoning structure against the tokenized ground truth:

```python
def score_transition_quality(response: str, verse_key: str) -> float:
    """Score a model response against the verse's transition tokens."""
    tokens = es.get(index="furqan_quran_tokens", id=verse_key)
    transitions = tokens["_source"]["transition_tokens"]
    logic = tokens["_source"]["logic_tokens"]
    # Score: transition type accuracy, semantic field shifts,
    #        discourse depth maintenance, callback recognition
    ...
```

### 6.4 A/B Testing

**Script:** `training/eval/ab_test.py`

Runs the same questions through 4 models:

```
Model A: Qwen3.5-27B base (zero-shot)
Model B: Furqan-27B Stage 1 (tafsir only)
Model C: Furqan-27B Stage 2 (+ real-world transfer)
Model D: Furqan-27B DPO (+ preference alignment)

Same question → 4 responses → human picks best
Expected win rate: D > C > B >> A
```

**Critical test:** On real-world scenarios, Stage 2 (C) should massively
outperform Stage 1 (B), because Stage 1 only learned patterns in their
Quranic context while Stage 2 learned to transfer them.

---

## 7. Phase 5: Export & Deployment

### 7.1 Merge LoRA & Export GGUF

**Script:** `training/export/merge_and_export.py`

```bash
# 1. Merge LoRA weights into base model
python training/export/merge_and_export.py \
  --base-model Qwen/Qwen3.5-27B \
  --lora-path output/furqan-27b-sft \
  --output-dir output/furqan-27b-merged

# 2. Convert to GGUF (via llama.cpp)
python llama.cpp/convert_hf_to_gguf.py \
  output/furqan-27b-merged \
  --outfile output/furqan-27b.gguf

# 3. Quantize to Q4_K_M
llama.cpp/llama-quantize \
  output/furqan-27b.gguf \
  output/furqan-27b-Q4_K_M.gguf Q4_K_M
```

### 7.2 Deploy to Ollama

**Script:** `training/export/deploy_ollama.sh`

```bash
# Create Ollama Modelfile
cat > Modelfile <<EOF
FROM ./output/furqan-27b-Q4_K_M.gguf

PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER num_ctx 8192

SYSTEM """أنت عالم متخصص في تفسير القرآن الكريم. تستخدم المسلمات الأربع وبوابات الجودة في تحليلك.
لا تولد نصاً قرآنياً. ركز على البنية المنطقية والانتقالات بين الأفكار."""
EOF

# Register with Ollama
ollama create furqan-27b -f Modelfile

# Test
ollama run furqan-27b "ما العلاقة بين الآية الأولى والثانية من سورة الفاتحة؟"
```

### 7.3 Integration with FastAPI

Update `config.yaml` to use the local model:

```yaml
llm:
  provider: "ollama"
  model: "furqan-27b"
  base_url: "http://localhost:11434"
  temperature: 0.1
  max_tokens: 4096
```

No code changes needed in the orchestrator — it already supports Ollama.

---

## 8. Training Dependencies

**File:** `training/requirements.txt`

```
# Core training
unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git
peft>=0.12.0
trl>=0.12.0
bitsandbytes>=0.44.0
transformers>=4.46.0
datasets>=2.21.0
accelerate>=1.0.0

# Experiment tracking
wandb>=0.18.0

# Export
llama-cpp-python>=0.3.0

# Evaluation
rouge-score>=0.1.2
sacrebleu>=2.4.0
```

**Installation:**

```bash
# Create training venv (separate from main project)
python -m venv .venv-training
source .venv-training/bin/activate

# Install Unsloth (must be first — patches torch)
pip install unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git

# Install remaining
pip install -r training/requirements.txt

# Install project in editable mode (for ES access, tokenizer)
pip install -e ".[all]"
```

---

## 9. Cloud Training Playbook

### RunPod Setup

```bash
# 1. Launch A100 80GB pod on RunPod
#    Template: PyTorch 2.5 + CUDA 12.4
#    Storage: 100GB persistent volume

# 2. Clone repo
git clone https://github.com/Ashmaawyy/Al-Furqan.git
cd al-furqan

# 3. Install dependencies
pip install unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git
pip install -r training/requirements.txt
pip install -e ".[all]"

# 4. Upload training data
# (scp or rsync from local machine)
scp -r data/training/ runpod:/workspace/al-furqan/data/training/

# 5. Run SFT
python training/train_sft.py --config training/configs/sft_qwen35_27b.yaml

# 6. Run DPO (after human feedback collection)
python training/train_dpo.py --config training/configs/dpo_qwen35_27b.yaml

# 7. Download artifacts
scp -r runpod:/workspace/al-furqan/output/ ./output/
```

**Cost estimate:** A100 80GB on RunPod = ~$2.50/hour. Total: ~$25-50 for SFT+DPO.

---

## 10. Checkpoints & Milestones

| Milestone | Gate Criteria | Week |
|-----------|--------------|------|
| **M1: Tafsir Data Ready** | >= 3,000 chat-format tafsir examples | 2 |
| **M2: Real-World Data Ready** | >= 500 human-curated real-world scenarios | 3 |
| **M3: 9B Prototype** | Loss converges, tool calls work, Arabic coherent | 4 |
| **M4: Stage 1 SFT** | Tafsir benchmark >= 70%, KB usage >= 2/question | 5 |
| **M5: Stage 2 SFT** | Real-world pattern identification >= 60% | 7 |
| **M6: DPO Complete** | Win rate vs Stage 2 >= 60% on real-world scenarios | 9 |
| **M7: Benchmark Pass** | All success criteria from PRD met (both tracks) | 11 |
| **M8: Deployed** | GGUF running on Ollama, integrated with FastAPI | 12 |

**Go/No-Go decisions:**
- **M3 → M4:** If 9B prototype shows broken data/format — fix before 27B
- **M4 → M5:** If Stage 1 fails tafsir baseline — fix patterns before real-world
- **M5 → M6:** If Stage 2 can't transfer patterns — need more/better scenario data

---

## 11. Model Card (Template)

To be filled after training:

```
# Furqan-27B Model Card

## Model Details
- Base: Qwen3.5-27B
- Fine-tuning: SFT + DPO via Unsloth (16-bit LoRA)
- Training data: X examples (Y Criterion pairs + Z synthetic CoT + W transition examples)
- Training compute: N GPU-hours on A100 80GB

## Intended Use
- Quranic reasoning and tafsir analysis
- KB-grounded question answering with tool calling
- Axiom-anchored logical analysis

## Limitations
- Trained primarily on Surat Al-An'am (Episode 1 KB data)
- Does NOT generate Quranic text
- Arabic-only responses
- Requires Elasticsearch backend for KB tools

## Evaluation Results
| Metric | Value |
|--------|-------|
| Accuracy | TBD |
| KB Usage | TBD |
| Transition Quality | TBD |
| Win Rate vs Base | TBD |

## Training Hyperparameters
- LoRA rank: 64, alpha: 128
- Learning rate: 1e-4
- Epochs: 3 (SFT) + 1 (DPO)
- Batch size: 2, gradient accumulation: 8
```

---

_Document generated: April 5, 2026 | Al-Furqan contributors_
