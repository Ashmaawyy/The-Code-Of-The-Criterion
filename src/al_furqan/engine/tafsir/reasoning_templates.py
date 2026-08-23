"""
Reasoning Templates — خطط تفكير مبنية على الـ Axioms والـ Gates.

Each template guides the LLM on HOW to think about a specific type of question.
The LLM executes the plan and uses KB tools to search for sources.
"""

from al_furqan.kb.tafsir.query_analyzer import QueryType

# --- Axiom Guidelines (translated to Tafsir context) ---

AXIOM_GUIDELINES = {
    "design": "ترتيب الآيات في القرآن مقصود — كل آية في مكانها لحكمة. اسأل: لماذا جاءت هنا؟",
    "network_effect": "كل آية مرتبطة بسياقها — لا تفسّر بمعزل عن ما قبلها وبعدها والسورة ككل.",
    "transcendence": "القرآن مصدر متعالي — التفسير يرجع للنص والحديث الصحيح أولاً، مش الرأي البشري.",  # pylint: disable=line-too-long
    "final_court": "الوعد والوعيد في القرآن حقيقي — ابحث عن تحققه التاريخي إن وُجد.",
}

# --- Gate Checks (as self-check instructions for the LLM) ---

GATE_CHECKS = {
    "source_integrity": "☐ Source-Integrity: هل استندت للنص القرآني والحديث الصحيح؟ لا تنسب للقرآن ما ليس فيه.",  # pylint: disable=line-too-long
    "structural_consistency": "☐ Structural-Consistency: هل الربط بين الآيات متسق ومنطقي؟ لا تربط بدون دليل.",  # pylint: disable=line-too-long
    "mediation_zeroing": "☐ Mediation-Zeroing: هل تجنبت تقديم الرأي البشري على الوحي؟",
    "origin_aware": "☐ Origin-Aware: هل المرجعية هي الوحي (قرآن + سنة)؟",
}

# --- KB Usage Rules ---

KB_USAGE_RULES = """
## قواعد استخدام قاعدة المعرفة:
- لديك أدوات بحث (tools) في قاعدة معرفة تفسيرية من دروس الشيخ أحمد السيد.
- **يجب أن تستخدم هذه الأدوات فعلياً (function calls) قبل الإجابة** — لا تجب مباشرة.
- ابدأ بالبحث في الـ KB أولاً، ثم أجب بناءً على ما وجدته + معرفتك الشاملة.
- الـ KB مصدر مساعد — لو مالقيتش فيه أجب من معرفتك العامة بلا تردد.
- لما تنقل من الشيخ أحمد السيد وضّح ذلك صراحة.
- لا تقتصر على ما في الـ KB — معرفتك الشاملة هي الأساس والـ KB إضافة.
- **مهم: نفّذ الخطوات بالترتيب واستخدم الـ tools المذكورة فيها قبل أن تجيب.**
"""

# --- Templates ---

TEMPLATES = {
    QueryType.TAFSIR: {
        "name": "تفسير آية",
        "axioms": ["design", "network_effect", "transcendence"],
        "gates": ["source_integrity", "structural_consistency", "origin_aware"],
        "steps": [
            'ابحث عن الآية في قاعدة المعرفة: search_kb_by_verse("{verse_ref}")',
            "حدد الموضوع المركزي للآية",
            'ابحث عن السياق: get_verse_context("{verse_ref}")',
            'ابحث عن آيات مرتبطة: search_kb_by_relation("{verse_ref}", "LINKED_VERSE")',
            'ابحث عن أحاديث: search_kb_by_relation("{verse_ref}", "LINKED_HADITH")',
            "استخرج السنة الإلهية أو القاعدة الكلية إن وُجدت",
            "استنبط الدروس والعبر",
            "تحقق من بوابات الجودة قبل الإجابة النهائية",
        ],
    },
    QueryType.VERSE_LINK: {
        "name": "ربط بين آيات",
        "axioms": ["design", "network_effect"],
        "gates": ["source_integrity", "structural_consistency"],
        "steps": [
            'ابحث عن كل آية في قاعدة المعرفة: search_kb_by_verse("{verse_ref}") لكل آية',
            "حدد الموضوع المشترك بين الآيات",
            "تتبع التسلسل المنطقي: كل آية إيه دورها في البناء؟",
            "حدد نقطة التحول: فين الموضوع اتغير أو تطور؟",
            'ابحث عن الموضوع: search_kb_by_topic("{topic}")',
            "ابحث عن الكلمات المفتاحية المشتركة أو المتقابلة",
            "استخرج العلاقة البنيوية (مقدمة→نتيجة / عام→خاص / سبب→أثر)",
            "تحقق من بوابات الجودة",
        ],
    },
    QueryType.ISTINBAT: {
        "name": "استنباط ودروس",
        "axioms": ["transcendence", "network_effect", "final_court"],
        "gates": ["source_integrity", "mediation_zeroing", "origin_aware"],
        "steps": [
            'ابحث عن الآية: search_kb_by_verse("{verse_ref}")',
            "حدد الحكم أو المبدأ الظاهر في الآية",
            "ابحث عن العلة: لماذا جاء هذا الحكم هنا؟",
            'ابحث عن مواضع مشابهة: search_kb_by_topic("{topic}")',
            "قارن بمواضع مشابهة في القرآن من معرفتك",
            "استخرج القاعدة الكلية",
            "طبّق: كيف تنطبق على واقعنا؟",
            "تحقق: هل الاستنباط مبني على الوحي أم على الرأي؟ (Mediation-Zeroing)",
        ],
    },
    QueryType.COMPARISON: {
        "name": "مقارنة بين سور",
        "axioms": ["design", "network_effect"],
        "gates": ["source_integrity", "structural_consistency"],
        "steps": [
            'ابحث في قاعدة المعرفة عن الموضوع: search_kb_by_topic("{topic}")',
            "حدد كيف تناولت سورة الأنعام هذا الموضوع (من قاعدة المعرفة)",
            "قارن بسور أخرى تناولت نفس الموضوع (من معرفتك)",
            "حدد النمط المشترك والاختلافات",
            "استخرج: لماذا اختلف الأسلوب بين السور؟ ما الحكمة؟",
            "استنبط القاعدة الكلية",
            "تحقق من بوابات الجودة",
        ],
    },
    QueryType.SEERAH_LINK: {
        "name": "ربط بالسيرة",
        "axioms": ["final_court", "transcendence", "network_effect"],
        "gates": ["source_integrity", "structural_consistency", "origin_aware"],
        "steps": [
            'ابحث عن الآية: search_kb_by_verse("{verse_ref}")',
            'ابحث عن أحاديث مرتبطة: search_kb_by_relation("{verse_ref}", "LINKED_HADITH")',
            "حدد الحدث التاريخي المرتبط بالآية",
            "اشرح ظروف النزول وملابساتها",
            "كيف كانت الآية تربّي النبي ﷺ والصحابة في تلك اللحظة؟",
            "هل تحقق وعد أو وعيد في الآية لاحقاً؟ متى وكيف؟",
            "ما الدرس السيروي المستفاد؟",
            "تحقق من بوابات الجودة",
        ],
    },
    QueryType.GENERAL: {
        "name": "سؤال عام",
        "axioms": ["transcendence"],
        "gates": ["source_integrity", "origin_aware"],
        "steps": [
            'ابحث في قاعدة المعرفة عن الموضوع: search_kb_by_topic("{topic}")',
            "أجب من معرفتك الشاملة",
            "أضف ما وجدته في قاعدة المعرفة إن كان مرتبطاً",
            "تحقق من بوابات الجودة",
        ],
    },
}


def get_template(query_type: QueryType) -> dict:
    """Get the reasoning template for a query type."""
    return TEMPLATES.get(query_type, TEMPLATES[QueryType.GENERAL])
