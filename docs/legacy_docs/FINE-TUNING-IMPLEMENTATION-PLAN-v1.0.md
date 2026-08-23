# Fine-Tuning Implementation Plan — Al-Furqan
## Supervised Learning with Human Feedback for Quranic Reasoning
### Version 1.0

---

**Project:** Al-Furqan (الفرقان)  
**Date:** March 22, 2026  
**Status:** Plan Only — Execution pending data collection  
**Author:** Arif AI + Muhammad Al-Ashmawy  
**Classification:** Open project  

---

## 1. الهدف

تدريب نسخة من Qwen متخصصة في **التفكير التفسيري** — مش بس تجيب معلومات عن التفسير، بل **تفكر زي ما الشيخ بيفكر**: تربط الآيات ببعضها، ترجع للسيرة، تستخرج السنن الإلهية، وتستنبط الدروس.

**المدخل:** سؤال تفسيري  
**المخرج المطلوب:** إجابة تتبع منهج تفكير محدد (Axiom-guided) مع استخدام مصادر الـ KB  
**المعيار:** Human feedback (correct/wrong) على الإجابات  

---

## 2. الـ Training Pipeline الكامل

```
                    ┌─────────────────────────┐
                    │  Phase 1: Data Collection │
                    │  (Pipeline + Feedback)    │
                    └──────────┬──────────────┘
                               ↓
                    ┌─────────────────────────┐
                    │  Phase 2: Data Curation   │
                    │  (Clean + Format + Split)  │
                    └──────────┬──────────────┘
                               ↓
                    ┌─────────────────────────┐
                    │  Phase 3: SFT             │
                    │  (Supervised Fine-Tuning)  │
                    │  "علّمه الإجابة الصح"      │
                    └──────────┬──────────────┘
                               ↓
                    ┌─────────────────────────┐
                    │  Phase 4: DPO             │
                    │  (Direct Preference        │
                    │   Optimization)            │
                    │  "علّمه يفضّل الصح على     │
                    │   الغلط"                   │
                    └──────────┬──────────────┘
                               ↓
                    ┌─────────────────────────┐
                    │  Phase 5: Evaluation       │
                    │  + Iteration               │
                    └─────────────────────────┘
```

---

## 3. Phase 1: Data Collection (الآن — مستمر)

### 3.1 مصادر البيانات

#### المصدر الأول: Pipeline Responses + Human Feedback
كل سؤال يمر بالـ pipeline ينتج training example:

```json
{
  "question": "إيه علاقة أول أربع آيات بالآية 5؟",
  "system_prompt": "أنت عالم متخصص... [reasoning plan with axioms/gates]",
  "tool_calls": [
    {"name": "search_kb_by_verse", "args": {"verse_ref": "6:5"}, "result": "..."},
    {"name": "search_kb_by_topic", "args": {"topic": "السنة الإلهية"}, "result": "..."}
  ],
  "response": "العلاقة هي مقدمة منطقية تؤدي لحتمية النتيجة...",
  "feedback": {
    "verdict": "correct_notes",
    "notes": "كويس بس ناقص ربط بحديث ابن مسعود",
    "reviewer": "muhammad"
  }
}
```

#### المصدر الثاني: Synthetic Data من الـ KB
نولّد أسئلة وإجابات مثالية من الـ KB entries:

```
KB Entry: 6:5 → يوم بدر (HAS_TAFSIR, confidence 0.95)
  ↓
Generated Q: "ما علاقة الآية الخامسة من سورة الأنعام بيوم بدر؟"
Generated A: (إجابة مبنية على الـ KB entry + reasoning template)
  ↓
Human Review: correct ✅
```

#### المصدر الثالث: Preference Pairs (لـ DPO)
من الـ feedback نبني أزواج (chosen / rejected):

```
Question: "تفسير الآية 6:5"
Chosen:  (response rated "correct" — ذكر بدر + السنة الإلهية + حديث ابن مسعود)
Rejected: (response rated "wrong" — تفسير سطحي بدون KB)
```

### 3.2 الأهداف الكمية

| المرحلة | عدد الأمثلة المطلوبة | المصدر |
|---------|---------------------|--------|
| SFT (أولي) | 500+ | Pipeline responses (correct) + synthetic |
| SFT (كامل) | 2,000+ | + باقي الحلقات + more questions |
| DPO | 300+ أزواج | Pipeline (correct vs wrong pairs) |

### 3.3 تصميم الـ Training Format

#### SFT Format (Conversation):
```json
{
  "conversations": [
    {
      "role": "system",
      "content": "أنت عالم متخصص في تفسير القرآن...\n\n## المسلّمات:\n- Design vs. Accident: ترتيب الآيات مقصود...\n\n## بوابات الجودة:\n- ☐ Source-Integrity: ...\n\n## لديك أدوات بحث في قاعدة معرفة تفسيرية..."
    },
    {
      "role": "user",
      "content": "إيه علاقة أول أربع آيات من سورة الأنعام بالآية رقم 5؟"
    },
    {
      "role": "assistant",
      "content": null,
      "tool_calls": [{"function": {"name": "search_kb_by_verse", "arguments": "{\"verse_ref\": \"6:5\"}"}}]
    },
    {
      "role": "tool",
      "content": "## نتائج البحث عن الآية 6:5:\n[يوم بدر، السنة الإلهية، حديث ابن مسعود...]"
    },
    {
      "role": "assistant",
      "content": "بناءً على البحث في قاعدة المعرفة... العلاقة هي مقدمة منطقية..."
    }
  ]
}
```

#### DPO Format (Preference Pairs):
```json
{
  "prompt": "إيه علاقة أول أربع آيات بالآية 5؟",
  "chosen": "العلاقة هي مقدمة ونتيجة... [مع بدر + السنة الإلهية + حديث ابن مسعود]",
  "rejected": "الآيات مترابطة... [بدون KB, سطحي]"
}
```

---

## 4. Phase 2: Data Curation

### 4.1 Data Pipeline
```
Raw Pipeline Outputs (data/tafsir_feedback/*.json)
      ↓
[Filter: correct + correct_notes only] → SFT candidates
      ↓
[Enhance: add ideal tool calls if missing]
      ↓
[Format: convert to conversation format]
      ↓
[Split: 80% train / 10% val / 10% test]
      ↓
training_data/
├── sft_train.jsonl
├── sft_val.jsonl
├── sft_test.jsonl
├── dpo_train.jsonl
└── dpo_val.jsonl
```

### 4.2 Quality Filters
- **Include:** verdict = correct أو correct_notes
- **Exclude:** verdict = wrong (إلا كـ rejected في DPO)
- **Enhance:** لو الـ response صح بس المودل ماستخدمش tools → نضيف tool calls مثالية
- **Deduplicate:** أسئلة متشابهة → نختار الأفضل

### 4.3 Data Augmentation
- **Paraphrase questions:** نفس السؤال بصياغات مختلفة
- **Vary difficulty:** أسئلة بسيطة (تفسير آية) → معقدة (مقارنة سور)
- **Multi-turn:** أسئلة متتابعة (follow-up questions)

---

## 5. Phase 3: SFT (Supervised Fine-Tuning)

### 5.1 Model Selection

| Model | Parameters | VRAM (Q4) | VRAM (LoRA Train) | Speed | Notes |
|-------|-----------|-----------|-------------------|-------|-------|
| Qwen3.5-9B-OmniCoder-Claude-Polaris | 9B | ~6GB | ~16GB | 50+ tok/s | خفيف — merge, مش reasoning-focused |
| **Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled** | **27B** | **~16.5GB** | **~40GB** | **29-35 tok/s** | **✅ التوصية** |
| Qwen3-32B | 32B | ~20GB | ~48GB | 20-25 tok/s | أصلي بدون distillation |
| Qwen3-30B-A3B (MoE) | 30B (3B active) | ~20GB | ~40GB | سريع | MoE — أقل جودة reasoning |

**التوصية: `Jackrong/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled`**

**ليه هو الأنسب للفرقان:**
1. **Distilled من Claude Opus 4.6** — متدرب على Structured Chain-of-Thought reasoning. بالظبط نفس الأسلوب اللي محتاجينه: "1. حلل السؤال → 2. ابحث → 3. اربط → 4. استنبط"
2. **27B** — أقوى بكتير من الـ 9B في الفهم والاستدلال باللغة العربية والنصوص الشرعية
3. **16.5GB VRAM فقط** مع Q4_K_M quantization — يشتغل على **GPU واحد** (RTX 3090/4090 أو A100 40GB)
4. **262K context window** — يسع أي سؤال معقد + نتايج KB tools
5. **29-35 tok/s** على RTX 3090 — استجابة سريعة للمستخدم
6. **يدعم thinking mode + tool calling** — جاهز للـ pipeline بتاعنا مباشرة
7. **Unsloth-optimized** — سهل الـ fine-tuning مع LoRA/QLoRA
8. **141K downloads + 1K likes** — المجتمع معتمد عليه ومختبر

**المودل كـ base → نعمل عليه SFT + DPO → Furqan-27B**

**HuggingFace:** `Jackrong/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled`  
**GGUF:** `Jackrong/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-GGUF`

### 5.2 Training Framework

**LLaMA-Factory** (مدعوم رسمياً من Qwen):
```yaml
# config/sft_qwen3_14b_tafsir.yaml
model_name_or_path: Qwen/Qwen3-14B
dataset: tafsir_sft
template: qwen3
finetuning_type: lora
lora_rank: 64
lora_alpha: 128
lora_target: all
learning_rate: 1.0e-4
num_train_epochs: 3
per_device_train_batch_size: 2
gradient_accumulation_steps: 8
bf16: true
max_length: 8192
logging_steps: 10
save_steps: 100
eval_steps: 100
```

### 5.3 LoRA vs Full Fine-Tuning

| Method | VRAM | Training Time | Quality | When to use |
|--------|------|---------------|---------|-------------|
| **QLoRA (4-bit)** | ~20GB | ساعات | 85-90% | التجربة الأولى — GPU واحد |
| **LoRA** | ~40GB | ساعات | 90-95% | بعد التجربة الأولى — نتائج أحسن |
| **Full FT** | ~120GB+ | أيام | 100% | لما نكون واثقين من البيانات |

**التوصية:** نبدأ بـ **QLoRA** عشان نجرّب بسرعة، وبعدين **LoRA** للنسخة النهائية.

### 5.4 What the Model Learns in SFT

المودل بيتعلم **3 مهارات**:

1. **إزاي يبحث:** متى يستخدم أي tool ولماذا
   - يشوف السؤال عن آية → `search_kb_by_verse`
   - يشوف كلمة "السنة الإلهية" → `search_kb_by_topic`
   - يحتاج أحاديث → `search_kb_by_relation(verse, "LINKED_HADITH")`

2. **إزاي يفكر:** يتبع الـ reasoning template
   - يبدأ بالسياق → يحدد الموضوع → يربط → يستنبط
   - يطبق الـ Axioms في تحليله
   - يتحقق من الـ Gates قبل الإجابة

3. **إزاي يجاوب:** أسلوب الإجابة المثالي
   - يدمج معرفته مع الـ KB
   - ينسب المعلومات لمصادرها
   - يبني إجابة مرتبة ومنطقية

---

## 6. Phase 4: DPO (Direct Preference Optimization)

### 6.1 لماذا DPO بعد SFT؟

SFT يعلّم المودل **إيه الإجابة الصح**. DPO يعلّمه **يفضّل الصح على الغلط** — يعني يتجنب الأخطاء الشائعة اللي لقيناها في الـ feedback.

### 6.2 بناء Preference Pairs

من الـ feedback data:

```
Same question, two responses:
├── Chosen (correct/correct_notes):
│   "العلاقة تتضح من خلال السنة الإلهية...
│    كما ذكر الشيخ أحمد السيد في ربطه بيوم بدر..."
│
└── Rejected (wrong/wrong_notes):
    "الآيات مترابطة بشكل عام...
     فالآية 5 تكمل ما قبلها..."
```

**مصادر الـ Pairs:**
1. **نفس السؤال — إجابتين مختلفتين** (من runs مختلفة)
2. **Pipeline response vs Zero-shot** (مع KB vs بدون)
3. **Synthetic rejected:** ناخد إجابة صح ونشيل منها الـ KB references

### 6.3 DPO Training Config

```yaml
# config/dpo_qwen3_14b_tafsir.yaml
model_name_or_path: output/sft_checkpoint  # ← start from SFT model
dataset: tafsir_dpo
template: qwen3
finetuning_type: lora
pref_loss: sigmoid  # DPO loss
pref_beta: 0.1
learning_rate: 5.0e-5
num_train_epochs: 1
per_device_train_batch_size: 1
gradient_accumulation_steps: 16
bf16: true
```

### 6.4 What DPO Teaches

| Pattern to Learn | Chosen | Rejected |
|-----------------|--------|----------|
| استخدم الـ KB | ذكر بدر + حديث ابن مسعود | تفسير عام بدون مصادر |
| انسب المصادر | "كما ذكر الشيخ أحمد السيد..." | بدون نسبة |
| اتبع الـ Axioms | ربط بالـ Design + Network Effect | تحليل عشوائي |
| تحقق من Gates | "يحقق بوابة الاتساق الهيكلي..." | بدون self-check |
| استخدم Tools | 5-8 tool calls مناسبة | 0 tool calls أو بحث عشوائي |

---

## 7. Phase 5: Evaluation

### 7.1 Benchmark Suite

نستخدم نفس الـ **12-question benchmark** اللي عملناه + أسئلة جديدة:

| Eval Set | عدد الأسئلة | الغرض |
|----------|-------------|-------|
| Core Benchmark | 12 | المقارنة الأساسية (zero-shot vs SFT vs DPO) |
| KB Coverage | 30 | هل المودل بيستخدم الـ KB صح؟ |
| Tool Usage | 20 | هل بيختار الـ tools الصح؟ |
| Axiom Alignment | 15 | هل بيطبق الـ Axioms في تفكيره؟ |
| Edge Cases | 10 | أسئلة غريبة / مش في الـ KB |

### 7.2 Metrics

| Metric | How | Target |
|--------|-----|--------|
| **Accuracy** | Human review (correct %) | ≥ 85% |
| **KB Usage** | Tool calls per question | ≥ 3 |
| **Alignment** | Human rating 1-5 | ≥ 4.5 |
| **Depth** | Human rating 1-5 | ≥ 4.5 |
| **Source Attribution** | % responses citing sources | ≥ 90% |
| **Gate Compliance** | % responses self-checking gates | ≥ 80% |
| **Latency** | Response time | ≤ 15s (local GPU) |

### 7.3 A/B Testing

```
Same questions, 3 models:
├── Base Qwen3-14B (zero-shot)     → baseline
├── SFT Qwen3-14B (after Phase 3)  → +KB +reasoning
└── DPO Qwen3-14B (after Phase 4)  → +preferences
```

---

## 8. Infrastructure

### 8.1 GPU Requirements

| Phase | GPU | VRAM | Estimated Time | Cost (cloud) |
|-------|-----|------|---------------|-------------|
| SFT (QLoRA) | 1× A100 40GB | 24GB | 2-4 hours | ~$10-20 |
| SFT (LoRA) | 1× A100 80GB | 40GB | 4-8 hours | ~$30-60 |
| DPO (LoRA) | 1× A100 80GB | 40GB | 2-4 hours | ~$20-40 |
| Inference | 1× A100 40GB | 28GB | — | ~$2/hour |
| **Total Training** | | | **~8-16 hours** | **~$60-120** |

### 8.2 Software Stack

```
Training:
├── LLaMA-Factory    — training framework (Qwen-recommended)
├── PEFT             — LoRA/QLoRA adapters
├── DeepSpeed ZeRO-2 — memory optimization
├── bitsandbytes     — 4-bit quantization (for QLoRA)
└── Weights & Biases — experiment tracking

Inference:
├── vLLM             — high-throughput serving
└── SGLang           — alternative (better tool calling support)

Data:
├── proposed_edges.db — KB source
├── tafsir_feedback/  — human reviews
└── training_data/    — formatted datasets
```

### 8.3 On-Premises vs Cloud

| Option | Pros | Cons | Cost |
|--------|------|------|------|
| **Cloud (RunPod/Lambda)** | سهل، مرن، سريع | مؤقت، بيانات على سيرفر خارجي | ~$2-3/hour per A100 |
| **Mjara Cloud (own infra)** | بياناتنا عندنا، مستمر | محتاج setup | استثمار أولي |
| **Colab Pro** | رخيص | GPU ضعيف (T4/A100 40GB) | $10-50/شهر |

**التوصية:** نبدأ بـ **RunPod** (A100 80GB, ~$2.5/hour) للتجارب الأولى، وبعدين ننقل لـ **Mjara Cloud** لما نكون مستعدين للـ production.

---

## 9. Timeline

### Prerequisites (الآن — أسابيع 1-4):
- [ ] تنزيل وتفريغ الحلقات الـ 22 الباقية
- [ ] استخراج الـ KB entries (~1,500+ entry)
- [ ] جمع 100+ human feedback من الـ pipeline
- [ ] هذه المرحلة **لازم تخلص** قبل أي training

### Phase 1: Data Collection (أسابيع 1-6):
- [ ] تشغيل الـ pipeline على أسئلة متنوعة (50+ سؤال/أسبوع)
- [ ] جمع human feedback بالـ 4 verdicts
- [ ] الهدف: **500+ reviewed response**

### Phase 2: Data Curation (أسبوع 7):
- [ ] تنظيف البيانات وتقسيمها
- [ ] بناء preference pairs
- [ ] Validation set مستقل

### Phase 3: SFT Training (أسبوع 8):
- [ ] QLoRA تجربة أولى (Qwen3-14B, 2-4 ساعات)
- [ ] Evaluation على الـ benchmark
- [ ] LoRA لو النتائج واعدة (4-8 ساعات)

### Phase 4: DPO Training (أسبوع 9):
- [ ] بناء preference pairs من الـ feedback
- [ ] DPO training (2-4 ساعات)
- [ ] A/B comparison: Base vs SFT vs DPO

### Phase 5: Evaluation & Iteration (أسبوع 10):
- [ ] Full benchmark (87 سؤال)
- [ ] Error analysis
- [ ] Iteration if needed

### الإجمالي: **~10 أسابيع** من بداية جمع البيانات لأول مودل مُدرّب.

---

## 10. المخاطر والحلول

| المخاطر | الاحتمال | الحل |
|---------|---------|------|
| Data قليلة | عالي | Synthetic data augmentation + paraphrasing |
| الـ 14B مش كفاية | متوسط | جرّب 32B أو MoE 30B-A3B |
| Tool calling يتكسر بعد SFT | متوسط | تدريب محدد على tool format + eval |
| Overfitting على حلقة 1 | عالي | لازم 23 حلقة قبل الـ final model |
| Arabic tokenization ضعيفة | منخفض | Qwen ممتاز في العربي أصلاً |
| Catastrophic forgetting | متوسط | LoRA (يحافظ على المعرفة الأصلية) |
| الأحاديث الضعيفة | متوسط | Source-Integrity Gate + human review |

---

## 11. Success Criteria

| Criterion | Metric | Target |
|-----------|--------|--------|
| النموذج بيستخدم الـ KB | Tool calls / question | ≥ 3 |
| النموذج بيربط بالسيرة | % responses with seerah link | ≥ 70% |
| النموذج بيذكر المصادر | % with source attribution | ≥ 90% |
| النموذج بيتبع الـ Axioms | Axiom alignment score | ≥ 4/5 |
| النموذج أحسن من base | Human preference (win rate) | ≥ 70% vs base |
| سرعة الاستجابة | Time to first token | ≤ 2s (local) |
| Human accuracy | % correct in production | ≥ 85% |

---

## 12. Architecture بعد الـ Fine-Tuning

```
                    Current (API-based)
                    ┌──────────────────┐
User → Engine → │ Qwen API (remote)  │ → Response → Human Review
                    └──────────────────┘
                    Latency: 50+ seconds
                    Cost: per-token pricing
                    
                    
                    After Fine-Tuning (Local)
                    ┌──────────────────┐
User → Engine → │ Furqan-27B (local) │ → Response → Human Review
                    │ (fine-tuned Qwen3.5-27B-Claude-Opus) │
                    └──────────────────┘
                    Latency: 5-15 seconds
                    Cost: GPU only (no per-token)
                    Privacy: البيانات ماتخرجش
```

**الفرق:**
- **أسرع 3-10x** (local GPU vs API)
- **أرخص** (مفيش per-token cost)
- **أدق** (متدرب على منهج الشيخ تحديداً)
- **خصوصية** (البيانات ماتروحش لسيرفر خارجي)
- **متوافق مع QLP v3.0** (Local-First + سيادة رقمية)

---

## 13. الخلاصة

الـ Fine-tuning مش مجرد "نحسّن النتائج" — ده **بنبني نموذج تفكير تفسيري** خاص بينا:

1. **الآن:** نجمع data عالية الجودة من الـ pipeline + human feedback
2. **بعد 500+ example:** SFT — نعلّمه إزاي يجاوب صح
3. **بعد 300+ pair:** DPO — نعلّمه يفضّل الصح على الغلط
4. **النتيجة:** Furqan-27B — نموذج local متخصص في التفكير التفسيري (مبني على Qwen3.5-27B-Claude-Opus-Distilled)

كل سؤال بيتسأل النهارده + كل feedback بيتكتب = **training data** للنموذج بتاعنا بكره.

---

_Document generated: 2026-03-22 | Al-Furqan contributors_
