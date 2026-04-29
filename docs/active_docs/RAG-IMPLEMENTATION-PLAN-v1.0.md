# RAG Implementation Plan — Al-Furqan Tafsir KB
## Engine-Guided Reasoning with Retrieval-Augmented Generation
### Version 1.0

---

**Project:** Al-Furqan (الفرقان)  
**Date:** March 22, 2026  
**Status:** Draft — Pending Review  
**Author:** Arif AI + Muhammad Al-Ashmawy  
**Classification:** Internal — Variiance R&D  

---

## 1. الرؤية

### الهدف الأساسي:
**تعليم المودل يفكر أحسن** — مش بس يجيب معلومات.

الـ KB مش مخزن بيانات بنسحب منه إجابات جاهزة. الـ KB هو **منهج تفكير** — طريقة الشيخ أحمد السيد في ربط الآيات ببعضها وبالسيرة والأحاديث والسنن الإلهية. هدفنا إن الـ Engine يعلّم المودل **نفس طريقة التفكير دي**.

### الفلسفة:
```
الـ Engine = المعلّم    (يوجّه التفكير ويتحقق من النتيجة)
الـ KB = المنهج          (المصادر + أنماط التفكير المستخرجة من الشيخ)
الـ LLM = الطالب         (بيفكر ويجاوب بتوجيه المعلّم)
```

**مش:**
- ❌ الـ Engine يفكر بدل المودل (Pipeline RAG — الطالب بيحفظ مش بيفهم)
- ❌ المودل يفكر لوحده (Agentic RAG — الطالب بيذاكر من غير منهج)

**بل:**
- ✅ الـ Engine يوجّه تفكير المودل بالمصادر الصح + أسئلة التفكير الصح (Engine-Guided Reasoning)

---

## 2. المشكلة الحالية

| المقياس | حالياً | المشكلة |
|---------|--------|---------|
| طريقة تمرير الـ KB | System prompt كامل | المودل بيستلم كل حاجة — مش بيتعلم يبحث |
| حجم الـ context | ~28K حرف (67 entry) | مش هيشيل 23 حلقة (~600K+) |
| توجيه التفكير | مفيش | المودل بيجاوب من غير منهج تفسيري |
| التحقق | مفيش | مفيش verification للإجابة |
| الـ KB كمصدر | المصدر الوحيد | المفروض يكون مصدر مساعد مش بديل |

---

## 3. الحل: Engine-Guided Reasoning Pipeline

### 3.1 الـ Flow الكامل

```
                        User Question
                              ↓
                 ┌────────────────────────┐
            ①   │    Query Analyzer       │  Engine
                 │    تحليل السؤال        │
                 └───────────┬────────────┘
                              ↓
                 ┌────────────────────────┐
            ②   │  Reasoning Plan Builder │  Engine
                 │  بناء خطة التفكير      │
                 │  (Axioms + Gates +     │
                 │   Template + KB Tools) │
                 └───────────┬────────────┘
                              ↓
                 ┌────────────────────────┐
            ③   │   LLM Execution        │  LLM
                 │   ينفذ الخطة بنفسه:   │
                 │   • يبحث في الـ KB     │  ← search_kb()
                 │   • يفكر ويربط       │
                 │   • يجاوب             │
                 └───────────┬────────────┘
                              ↓
                 ┌────────────────────────┐
            ④   │  Response Evaluation    │  Engine
                 │  تقييم ضد الـ Axioms   │
                 │  + Gates + Scoring     │
                 └────────────────────────┘
```

**المبدأ الأساسي:**
- الـ **Engine** يبني الخطة ويقيّم النتيجة (المعلّم)
- الـ **LLM** ينفذ الخطة ويبحث بنفسه (الطالب)
- الـ **KB** أدوات بحث في يد المودل (المكتبة)

### 3.2 تفصيل كل مرحلة

---

## 4. المرحلة ①: Query Analyzer (محلل السؤال)

### الوظيفة:
يحلل سؤال المستخدم ويستخرج:
- الآيات المذكورة صراحة وضمنياً
- المواضيع والمفاهيم
- نوع السؤال (يحدد أي reasoning template يُستخدم)

### الـ Output:
```python
@dataclass
class QueryAnalysis:
    original_query: str
    verse_refs: list[str]           # ["6:1", "6:2", "6:3", "6:4", "6:5"]
    topics: list[str]               # ["السنة الإلهية", "الوعيد"]
    query_type: QueryType           # أحد الأنواع التالية
    search_keywords_ar: list[str]   # كلمات بحث
    needs_external_knowledge: bool  # هل محتاج معرفة برا الـ KB؟

class QueryType(Enum):
    TAFSIR = "tafsir"               # تفسير آية أو مجموعة آيات
    VERSE_LINK = "verse_link"       # ربط بين آيات
    ISTINBAT = "istinbat"           # استنباط ودروس
    COMPARISON = "comparison"       # مقارنة بين سور أو مواضع
    SEERAH_LINK = "seerah_link"    # ربط بالسيرة
    GENERAL = "general"             # سؤال عام
```

### التنفيذ:
- **المرحلة الأولى:** Regex + Rules (سريع، deterministic)
- **Fallback:** LLM call خفيف للأسئلة المعقدة
- مثال: "إيه علاقة أول 4 آيات بالآية 5" → `verse_refs=[6:1..6:5]`, `query_type=VERSE_LINK`

---

## 5. المرحلة ②: Reasoning Plan Builder (بنّاء خطة التفكير)

### الوظيفة:
يبني **خطة تفكير كاملة** للمودل بناءً على:
- نوع السؤال (من الـ Query Analyzer)
- الـ **Axioms** (المسلّمات الثابتة)
- الـ **Four Gates** (بوابات التحقق)
- **Reasoning Template** المناسب

الخطة بتتبعت للمودل مع **أدوات البحث في الـ KB** — المودل هو اللي بينفذ الخطة ويبحث بنفسه.

### 5.1 الـ Axioms في سياق التفسير

الـ Axioms الموجودة في الـ Engine بتتترجم لقواعد تفسيرية:

| Axiom | التطبيق التفسيري |
|-------|-----------------|
| **Transcendence Necessity** | القرآن مصدر متعالي — التفسير يرجع للنص أولاً مش للرأي البشري |
| **Final Court Necessity** | الوعد والوعيد في القرآن حقيقي — يجب ربطه بتحققه التاريخي |
| **Design vs. Accident** | ترتيب الآيات مقصود — كل آية في مكانها لحكمة |
| **The Network Effect** | كل آية مرتبطة بما قبلها وبعدها وبالسورة ككل — لا تفسير بمعزل |

### 5.2 الـ Four Gates في سياق التفسير

| Gate | التطبيق التفسيري |
|------|-----------------|
| **Source-Integrity** | التزم بالنص القرآني والحديث الصحيح — لا تحرّف ولا تختزل |
| **Structural-Consistency** | الربط بين الآيات لازم يكون منطقي ومتسق — مش عشوائي |
| **Mediation-Zeroing** | الرأي البشري ليس حجة — ارجع للمصادر الموثوقة |
| **Origin-Aware** | المرجعية هي الوحي — مش الفلسفة أو الثقافة |

### 5.3 الـ Reasoning Plan

الـ Engine بيبني plan كامل ويبعتها للمودل:

```python
@dataclass
class ReasoningPlan:
    query_analysis: QueryAnalysis
    axiom_guidelines: list[str]       # قواعد من الـ Axioms مترجمة للسياق
    gate_checks: list[str]            # بوابات التحقق اللي المودل يلتزم بيها
    reasoning_template: str           # خطوات التفكير حسب نوع السؤال
    kb_tools: list[ToolDefinition]    # أدوات البحث المتاحة للمودل
    output_format: str                # شكل الإجابة المطلوب
```

### 5.4 KB Tools (أدوات البحث المتاحة للمودل)

المودل بيستلم الأدوات دي ويستخدمها بنفسه أثناء التفكير:

#### Tool 1: `search_kb_by_verse(verse_ref)`
```python
# يبحث بالآية المركزية ويرجع كل الـ edges المرتبطة
search_kb_by_verse("6:5")
→ [يوم بدر, حديث ابن مسعود, السنة الإلهية, 6:112, 6:123, ...]
```

#### Tool 2: `search_kb_by_topic(topic)`
```python
# يبحث بالموضوع (semantic search)
search_kb_by_topic("محاجة المشركين")
→ [edges مرتبطة بالمحاجة من كل الآيات المركزية]
```

#### Tool 3: `search_kb_by_relation(verse_ref, relation_type)`
```python
# يبحث عن نوع علاقة محدد
search_kb_by_relation("6:5", "LINKED_HADITH")
→ [حديث ابن مسعود, حديث سلا الجزور]
```

#### Tool 4: `get_verse_context(verse_ref, range=5)`
```python
# يجيب الآيات المحيطة بالآية + تفسيرها
get_verse_context("6:5", range=3)
→ [6:2, 6:3, 6:4, 6:5, 6:6, 6:7, 6:8 + تفاسير متاحة]
```

### 5.5 Reasoning Templates (مدمجة مع الـ Axioms)

#### Template: تفسير آية (`TAFSIR`)
```
## خطة التفكير

### المسلّمات (Axioms):
- ترتيب الآيات مقصود — لماذا جاءت هذه الآية هنا؟ (Design)
- كل آية مرتبطة بسياقها — لا تفسّر بمعزل (Network Effect)

### بوابات الجودة (Gates):
- ☐ Source-Integrity: هل استندت للنص القرآني والحديث الصحيح؟
- ☐ Structural-Consistency: هل الربط بين الآيات متسق ومنطقي؟
- ☐ Mediation-Zeroing: هل تجنبت الرأي البشري بدون دليل؟
- ☐ Origin-Aware: هل المرجعية هي الوحي؟

### خطوات التنفيذ:
1. ابحث عن الآية في الـ KB: search_kb_by_verse("{verse_ref}")
2. حدد الموضوع المركزي للآية
3. ابحث عن السياق: get_verse_context("{verse_ref}")
4. ابحث عن الروابط: search_kb_by_relation("{verse_ref}", "LINKED_VERSE")
5. ابحث عن الأحاديث: search_kb_by_relation("{verse_ref}", "LINKED_HADITH")
6. استخرج السنة الإلهية أو القاعدة الكلية
7. استنبط الدروس

### القواعد:
- أجب من معرفتك الشاملة + ما تجده في الـ KB
- الـ KB مصدر مساعد — لو مالقيتش فيه أجب من معرفتك
- لما تنقل من الشيخ أحمد السيد وضّح ذلك
```

#### Template: ربط آيات (`VERSE_LINK`)
```
## خطة التفكير

### المسلّمات:
- ترتيب الآيات مقصود (Design)
- الربط بين الآيات جزء من فهم المعنى (Network Effect)

### بوابات الجودة:
- ☐ Source-Integrity: التزم بالنص
- ☐ Structural-Consistency: الربط منطقي ومتسق

### خطوات التنفيذ:
1. ابحث عن كل آية: search_kb_by_verse("{verse_ref}") لكل آية
2. حدد الموضوع المشترك
3. تتبع التسلسل المنطقي
4. ابحث عن الموضوع: search_kb_by_topic("{topic}")
5. حدد نقطة التحول بين المواضيع
6. استخرج العلاقة البنيوية
```

#### Template: مقارنة (`COMPARISON`)
```
## خطة التفكير

### المسلّمات:
- القرآن يتناول المواضيع من زوايا مختلفة حسب السياق (Design)
- التكرار في القرآن ليس تكراراً — كل موضع له حكمة (Network Effect)

### خطوات التنفيذ:
1. ابحث في الـ KB عن الموضوع: search_kb_by_topic("{topic}")
2. حدد كيف تناولته سورة الأنعام
3. قارن بسور أخرى من معرفتك
4. حدد النمط المشترك والاختلاف
5. استنبط الحكمة من الاختلاف
```

_(Templates مشابهة لـ ISTINBAT و SEERAH_LINK)_

---

## 6. المرحلة ③: LLM Execution (تنفيذ المودل)

### الوظيفة:
المودل يستلم الـ **Reasoning Plan** الكامل + **أدوات الـ KB** وينفذ بنفسه:

```
المودل يستلم:
├── خطة التفكير (reasoning template + axioms + gates)
├── أدوات البحث (search_kb_by_verse, search_kb_by_topic, ...)
└── السؤال الأصلي

المودل ينفّذ:
├── يبحث في الـ KB (tool calls)
├── يفكر ويربط (بتوجيه الخطة)
├── يتحقق من الـ gates (self-check)
└── يجاوب
```

### الـ System Prompt:
```
أنت عالم متخصص في تفسير القرآن الكريم.

لديك أدوات بحث في قاعدة معرفة تفسيرية (من دروس الشيخ أحمد السيد).
استخدم هذه الأدوات أثناء تفكيرك للبحث عن مصادر تُثري إجابتك.

{reasoning_plan}  ← الخطة الكاملة من الـ Engine

قواعد:
1. اتبع خطوات التفكير المطلوبة بالترتيب
2. استخدم أدوات البحث للعثور على مصادر مرتبطة
3. أجب من معرفتك الشاملة + ما تجده في الـ KB
4. الـ KB مصدر مساعد — لو مالقيتش أجب من معرفتك
5. التزم ببوابات الجودة (Gates) المذكورة
6. لما تنقل من الشيخ أحمد السيد وضّح ذلك
```

### مثال تنفيذ (السؤال: "إيه علاقة أول 4 آيات بالآية 5"):

```
المودل يفكر:
→ الخطة تقول: ابحث عن الآية 6:5 أولاً
→ Tool call: search_kb_by_verse("6:5")
→ نتيجة: [يوم بدر, حديث ابن مسعود, السنة الإلهية]
→ الخطة تقول: ابحث عن السياق
→ Tool call: get_verse_context("6:5", range=4)
→ نتيجة: [آيات 6:1-6:8 + تفاسير]
→ الخطة تقول: ابحث عن العلاقات
→ Tool call: search_kb_by_relation("6:5", "LINKED_VERSE")  
→ نتيجة: [6:112, 6:123]
→ الخطة تقول: تحقق من الـ Gates
→ ☑ Source-Integrity: استندت للآيات والحديث ✓
→ ☑ Structural-Consistency: الربط منطقي ✓
→ دلوقتي أجاوب...
```

---

## 7. المرحلة ④: Human Review + Feedback Loop

### 7.1 الفلسفة:
التقييم **حالياً** بشري — أنتم اللي بتقيّموا الإجابات. الـ Engine evaluation الأوتوماتيكي ييجي **لاحقاً** لما تتجمّع بيانات كفاية من تقييماتكم.

### 7.2 الـ Flow:

```
LLM Response
      ↓
┌──────────────────────────────┐
│  Human Reviewer               │
│  (Muhammad / Team)            │
│                               │
│  يقيّم على 3 محاور:          │
│  • accuracy (1-5)             │
│  • depth (1-5)                │
│  • alignment مع الشيخ (1-5)   │
│  + ملاحظات نصية               │
│  + تصنيف: ✅ صح / ⚠️ جزئي / ❌ غلط │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│  Feedback Store               │  ← موجود فعلاً في المشروع
│  (data/feedback/)             │
│                               │
│  يخزّن لكل response:          │
│  • السؤال الأصلي              │
│  • الـ reasoning plan          │
│  • الـ KB tools اللي اتستخدمت │
│  • إجابة المودل               │
│  • تقييم الـ reviewer          │
│  • الملاحظات                  │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│  Pattern Learning             │
│                               │
│  من الـ feedback المتراكم:    │
│  • أنماط صح (patterns ✅)     │
│  • أنماط غلط (patterns ❌)    │
│  • تحسين الـ templates         │
│  • تحسين الـ KB tools          │
└──────────────────────────────┘
```

### 7.3 الـ Feedback Schema:

```python
@dataclass
class TafsirFeedback:
    # === الـ Input ===
    question: str                    # السؤال الأصلي
    query_analysis: QueryAnalysis    # تحليل السؤال
    reasoning_plan: ReasoningPlan    # الخطة اللي اتبعتت للمودل
    kb_tools_used: list[dict]        # الـ tool calls اللي المودل عملها
    kb_results: list[dict]           # نتايج البحث من الـ KB
    
    # === الـ Output ===
    llm_response: str                # إجابة المودل
    
    # === الـ Human Review ===
    reviewer: str                    # مين قيّم
    accuracy: int                    # 1-5 — الإجابة صح؟
    depth: int                       # 1-5 — فيها تفصيل وتحليل؟
    alignment: int                   # 1-5 — توافق مع منهج الشيخ؟
    verdict: str                     # "correct" / "partial" / "wrong"
    notes: str                       # ملاحظات حرة
    
    # === Pattern Tags ===
    good_patterns: list[str]         # إيه اللي المودل عمله صح
    bad_patterns: list[str]          # إيه اللي المودل عمله غلط
    # مثال good: ["ربط تاريخي دقيق", "استخدم حديث ابن مسعود صح"]
    # مثال bad: ["تجاهل السنة الإلهية", "مذكرش مصدر الحديث"]
```

### 7.4 كيف الـ Feedback بيحسّن النظام:

#### تحسين الـ Reasoning Templates:
```
لو أغلب الـ feedback بيقول:
  ❌ "المودل مش بيربط بالسيرة كويس"
→ نضيف في الـ TAFSIR template:
  "تأكد من ربط الآية بالحدث التاريخي المرتبط بها"
```

#### تحسين الـ KB Tools:
```
لو أغلب الـ feedback بيقول:
  ❌ "المودل ماستخدمش search_kb_by_relation"
→ نضيف في الخطة:
  "ابحث عن الأحاديث المرتبطة: search_kb_by_relation(verse, 'LINKED_HADITH')"
```

#### بناء Pattern Library:
```
من الـ feedback المتراكم:

✅ Patterns صح (يتكرروا):
- "لما الشيخ يذكر آية وعيد → ربطها بتحقق تاريخي"
- "لما يذكر قصة نبي → ربطها بموقف النبي ﷺ"
- "لما يشرح حكم → رجع للسنة الإلهية"

❌ Patterns غلط (يتفادوا):
- "تفسير الآية بمعزل عن سياقها"
- "ذكر حديث بدون تخريج"
- "خلط بين آراء المفسرين والنص القرآني"
```

#### الهدف طويل المدى:
لما تتجمّع **100+ feedback entry** بتقييمات بشرية → نقدر نبني **automated evaluator** يحاكي حكمكم:
- يتدرب على الـ patterns الصح والغلط
- يقدر يعمل pre-screening قبل ما يوصلكم
- بس القرار النهائي يفضل بشري

### 7.5 التكامل مع الـ FeedbackStore الموجود:

الـ `store/feedback_store.py` موجود فعلاً في المشروع ويدعم:
- `submit(feedback)` — تخزين تقييم
- `get_by_verdict(verdict_id)` — جلب تقييمات لإجابة معينة
- `list_all()` — كل التقييمات
- Ratings: `agree` / `disagree` / `partial` / `flag`

هنوسّعه ليدعم الـ `TafsirFeedback` schema الجديد مع الـ pattern tags.

---

## 9. التكامل مع البنية الحالية

### الملفات الموجودة:
| الملف | الدور الحالي | الدور الجديد |
|-------|-------------|-------------|
| `kb/retriever.py` | بحث Quran/Hadith/Fiqh | + بحث في Tafsir KB |
| `kb/embeddings.py` | MiniLM embeddings | يخدم semantic search |
| `kb/knowledge_linker.py` | Graph traversal | يخدم graph retrieval |
| `kb/graph/store.py` | Graph storage | يخزن tafsir edges |
| `engine/pipeline.py` | Scan→Mirror→Verdict | يخدم Response Verifier |
| `engine/prompts.py` | Engine prompts | + Reasoning Templates |
| `engine/chains/` | Guided Reasoning | + Tafsir reasoning chains |

### الملفات الجديدة:
```
src/al_furqan/
├── kb/
│   └── tafsir/
│       ├── __init__.py
│       ├── query_analyzer.py         # ① تحليل السؤال
│       ├── kb_tools.py               # أدوات البحث (search_kb_by_verse, etc.)
│       ├── vector_store.py           # تخزين embeddings للـ semantic search
│       └── tool_executor.py          # ينفذ الـ tool calls من المودل
├── engine/
│   └── tafsir/
│       ├── __init__.py
│       ├── reasoning_plan_builder.py # ② بناء خطة التفكير (Axioms + Gates)
│       ├── reasoning_templates.py    # Templates حسب نوع السؤال
│       ├── response_evaluator.py     # ④ تقييم ضد Axioms + Gates
│       └── correction_loop.py        # Self-correction عند فشل Gate
```

---

## 10. Data Pipeline

### من الحلقة للـ Engine-Guided RAG:

```
YouTube Episode
      ↓
[Whisper Transcription]          ← موجود
      ↓
lesson_XX_transcript.json
      ↓
[Transcript Chunker]             ← موجود
      ↓
[Relationship Extractor]         ← موجود (prompt معدّل)
      ↓
proposed_edges.db                ← موجود
      ↓
[Human Review]                   ← موجود (confirm/reject)
      ↓
┌──────────────────────────────────────────┐
│  NEW: Indexing Pipeline                  │
│                                          │
│  1. Embed كل edge (reasoning + sheikh   │
│     words)                               │
│  2. خزّن في vector store                │
│  3. حدّث الـ graph store                 │
│  4. استخرج reasoning patterns            │  ← جديد
│     (أنماط تفكير الشيخ)                  │
└──────────────────────────────────────────┘
      ↓
Engine-Guided RAG Ready ✅
```

### Reasoning Pattern Extraction (استخراج أنماط التفكير):

من الـ KB نقدر نستخرج **أنماط** تفكير الشيخ:
- "لما الشيخ يفسر آية وعيد → بيربطها بتحقق تاريخي"
- "لما يذكر قصة نبي → بيربطها بموقف النبي ﷺ المشابه"
- "لما يشرح حكم → بيرجع للسنة الإلهية الكلية"

هذه الأنماط تغذي الـ Reasoning Templates وتخليها أدق مع الوقت.

---

## 11. خطة التنفيذ (Sprints)

### Sprint 1: Query Analyzer + KB Tools (أسبوع 1)
- [ ] `query_analyzer.py` — تحليل السؤال (regex + rules + LLM fallback)
- [ ] `kb_tools.py` — الـ 4 أدوات: search_kb_by_verse, search_kb_by_topic, search_kb_by_relation, get_verse_context
- [ ] `tool_executor.py` — ينفذ الـ tool calls ويرجع النتايج
- [ ] `vector_store.py` — embedding + FAISS للـ semantic search
- [ ] Tests: 10+ test cases لكل tool
- [ ] اختبار يدوي: المودل يقدر يستخدم الأدوات صح

### Sprint 2: Reasoning Plan Builder + Templates (أسبوع 2)
- [ ] `reasoning_plan_builder.py` — يبني خطة التفكير من Axioms + Gates + Template
- [ ] `reasoning_templates.py` — الـ 5 templates مدمجة مع Axioms و Gates
- [ ] ترجمة الـ Axioms + Gates لسياق تفسيري (كقواعد واضحة)
- [ ] Integration: المودل يستلم الخطة + الأدوات وينفذ بنفسه
- [ ] Tests: كل template مع 3+ أسئلة
- [ ] **A/B test**: full-KB vs Engine-Guided (alignment + depth + reasoning quality)

### Sprint 3: Response Evaluator + Gate Scoring (أسبوع 3)
- [ ] `response_evaluator.py` — تقييم ضد الـ 4 Gates + KB usage + reasoning steps
- [ ] Scoring system (gate scores + bonuses + penalties)
- [ ] `correction_loop.py` — self-correction عند فشل gate (max 3 محاولات)
- [ ] Integration مع Scan→Mirror→Verdict pipeline
- [ ] Tests: evaluation accuracy tests

### Sprint 4: Full Pipeline + Benchmark (أسبوع 4)
- [ ] End-to-end pipeline: Query → Plan → LLM+Tools → Evaluate
- [ ] Full benchmark: 12+ سؤال × 3 modes (zero-shot / full-KB / Engine-Guided)
- [ ] Measure: accuracy, depth, alignment, gate scores, KB tool usage, latency
- [ ] Reasoning pattern extraction (أولي)
- [ ] Documentation update + PDF

---

## 12. معايير النجاح

| المقياس | Full-KB (حالي) | Engine-Guided (المطلوب) |
|---------|---------------|----------------------|
| Alignment مع الشيخ | ~4.8/5 | ≥ 4.8/5 (يحافظ أو يتحسن) |
| Depth (عمق التفكير) | ~4.9/5 | ≥ 5.0/5 (يتحسن بالتوجيه) |
| Context size | 28K+ حرف | ≤ 8K حرف |
| Scalability | ❌ | ✅ (يشيل أي عدد حلقات) |
| Reasoning structure | عشوائي | **منظّم بخطوات** |
| Source attribution | ضعيف | **واضح** (يوضح لما ينقل من الشيخ) |
| External knowledge | محدود بالـ KB | **حر** (KB مساعد مش حد) |

---

## 13. المخاطر والحلول

| المخاطر | الاحتمال | الحل |
|---------|---------|------|
| الـ templates مش مناسبة لكل أنواع الأسئلة | متوسط | Template GENERAL كـ fallback + تحسين مستمر |
| الـ Query Analyzer يختار template غلط | متوسط | LLM fallback + logging لمراجعة القرارات |
| Semantic search ضعيف بالعربي | متوسط | CamelBERT بدل MiniLM + fine-tuning |
| المودل يتجاهل خطوات التفكير | منخفض | Response Verifier يرصد ده + re-prompt |
| فقدان معلومة بسبب الـ retrieval | منخفض | Fallback: لو confidence منخفض → وسّع البحث |

---

## 14. التطور المستقبلي

### Phase 2 (بعد الـ 4 sprints):
- **Adaptive Templates** — الـ Engine يتعلم من الـ feedback أي template أفضل لأي نوع سؤال
- **Reasoning Pattern Library** — مكتبة أنماط تفكير مستخرجة تلقائياً من كل الحلقات
- **Multi-Scholar Support** — نفس الـ pipeline لشيوخ ومفسرين تانيين
- **Student Progress Tracking** — يتتبع مستوى المستخدم ويكيّف عمق الإجابة

### Phase 3 (طويل المدى):
- **الـ Engine يولّد templates جديدة** من أنماط الشيخ المكتشفة
- **Fine-tuning** — نستخدم الـ benchmark data لـ fine-tune مودل متخصص
- **Cross-Surah Reasoning** — لما تتوفر KBs من سور متعددة

---

## 15. Capacity Planning & Performance

### 15.1 تحليل أداء كل مرحلة

| المرحلة | العملية | الوقت المتوقع | الموارد |
|---------|--------|--------------|---------|
| ① Query Analyzer | Regex/Rules | ~5ms | CPU فقط |
| ② KB Retriever (Verse) | SQLite query | ~10ms | Disk I/O بسيط |
| ② KB Retriever (Semantic) | Embedding + FAISS search | ~50-100ms | RAM (embeddings محمّلة) |
| ② KB Retriever (Graph) | Graph traversal | ~20ms | RAM |
| ③ Reasoning Architect | Template selection + formatting | ~5ms | CPU فقط |
| ④ **LLM Generation** | API call (Qwen/DashScope) | **~5-15 ثانية** ⚠️ | **الـ bottleneck** |
| ⑤ Response Verifier | Rule checks + optional LLM | ~1-8 ثانية | LLM call إضافي |

**المراحل ①-③:** أقل من 200ms مجتمعة → تستحمل آلاف الـ queries/ثانية.
**الـ Bottleneck الوحيد:** مرحلة ④ الـ LLM API.

### 15.2 حدود الـ LLM API (DashScope/Qwen)

| المقياس | القيمة |
|---------|-------|
| وقت رد الـ LLM | 5-15 ثانية/query |
| Rate limit | ~60 RPM (request/minute) |
| Concurrent queries | ~4-5 في نفس الوقت |
| عند تجاوز الحد | 429 Too Many Requests (timeout مش crash) |

### 15.3 سيناريوهات التحمّل

| السيناريو | الحالة | وقت الاستجابة | ملاحظات |
|-----------|--------|--------------|---------|
| 👤 1-5 users متزامنين | ✅ مريح | 5-15 ثانية | الوضع الطبيعي |
| 👥 10-20 users متزامنين | ⚠️ بطء | 30-60 ثانية | Queue بيطوّل |
| 👥👥 50+ users متزامنين | ❌ مشكلة | timeout/فشل | Rate limit، بعض الـ queries بتفشل |

### 15.4 نقاط الفشل المحتملة والحلول

| المشكلة | السبب | الحل |
|---------|-------|------|
| Out of Memory | Embeddings كتير في الـ RAM | Lazy loading + FAISS memory-mapped |
| SQLite lock | كتابة وقراءة متزامنة | WAL mode (موجود) → PostgreSQL لاحقاً |
| LLM timeout | API بطيء تحت الضغط | Retry with backoff + request queue |
| Context too large | سؤال معقد → retrieval كبير | Hard cap (8K حرف max) |
| Embedding model crash | مودل كبير على RAM صغير | MiniLM (خفيف) → CamelBERT لاحقاً |

### 15.5 خطة التوسع (Scaling Phases)

#### Phase 1: MVP (حالي — 1-5 users)
```
SQLite + DashScope API + Single Server
التكلفة: ~$0 (free tier) أو ~$10/شهر
```
- كفاية للـ development والـ testing
- مفيش infrastructure إضافي

#### Phase 2: Small Scale (10-50 users)
```
+ Request Queue (Redis/Celery)
+ LLM Response Cache
+ Multiple API Keys
التكلفة: ~$50-100/شهر
```
- **Request Queue:** الـ queries بتتحط في queue وتتنفذ بالترتيب — المستخدم يستنى بدل ما يجيله error
- **Response Cache:** نفس السؤال (أو سؤال شبهه) → نفس الإجابة من الـ cache بدون LLM call
- **Multiple API Keys:** نوزع الـ load على أكتر من key → نضاعف الـ rate limit

#### Phase 3: Medium Scale (50-500 users)
```
+ Local LLM (Qwen على GPU)
+ PostgreSQL بدل SQLite
+ Horizontal Scaling (multiple workers)
التكلفة: ~$200-500/شهر (GPU server)
```
- **Local LLM:** لا rate limit → الـ throughput بيتحدد بالـ GPU بس
- على GPU واحد (A100/H100): ~20-30 queries/دقيقة
- **PostgreSQL:** يستحمل concurrent connections أكتر من SQLite
- **Workers:** كل worker بيخدم pipeline كامل → horizontal scaling

#### Phase 4: Large Scale (500+ users)
```
+ Fine-tuned Model (أصغر وأسرع)
+ Edge Caching للأسئلة الشائعة
+ Distributed Inference (multiple GPUs)
+ CDN للـ static responses
التكلفة: ~$1000+/شهر
```
- **Fine-tuned model:** مودل أصغر (7B-14B) متدرب على الـ tafsir → أسرع 5-10x من مودل عام كبير
- **Edge caching:** الأسئلة الشائعة (80% من الـ traffic) بيترد عليها فوراً
- **Distributed inference:** Multiple GPUs → 100+ queries/دقيقة

### 15.6 ملخص الـ Capacity

| المرحلة | Users متزامنين | Queries/دقيقة | التكلفة/شهر |
|---------|---------------|--------------|------------|
| Phase 1 (MVP) | 1-5 | ~4-5 | ~$0-10 |
| Phase 2 (Queue+Cache) | 10-50 | ~15-20 | ~$50-100 |
| Phase 3 (Local LLM) | 50-500 | ~30-60 | ~$200-500 |
| Phase 4 (Distributed) | 500+ | 100+ | ~$1000+ |

**القاعدة:** النظام **مش هيـ crash** — هيـ **slow down**. الـ queue بيحمي من الفشل، والـ cache بيقلل الحمل. كل phase بنضيفها لما نحتاجها — مش من الأول.

---

## 16. الخلاصة

الفرق بين هذا الـ approach والـ RAG التقليدي:

| RAG تقليدي | Engine-Guided Reasoning |
|------------|------------------------|
| يجيب معلومات | **يعلّم طريقة تفكير** |
| المصادر = الإجابة | المصادر = **مادة خام** للتفكير |
| المودل ينسخ | المودل **يفكر بتوجيه** |
| Static retrieval | **Dynamic reasoning plan** |
| One-size-fits-all | **Template per question type** |

الـ Engine بيعمل زي ما الشيخ أحمد السيد بيعمل بالظبط:
- مش بيقول "احفظ التفسير"
- بيقول "**شوف الآية دي... ربطها بدي... لاحظ السنة الإلهية... دلوقتي استنبط**"

---

_Document generated: 2026-03-22 | Al-Furqan R&D_
