"""Structural schema for sira events — the controlled vocabulary used for
analogical matching between historical precedent and modern scenarios.

Every event in the events DB is tagged along SIX axes. Together these tags
form the event's "structural fingerprint." Two events are analogically
equivalent iff their fingerprints overlap on a minimum threshold of axes
(policy decided by the analogy generator / retriever, not here).

Why six axes and not one big taxonomy:
  - Orthogonality: each axis captures an independent dimension of the
    situation, so a single event can combine tags from different axes
    without creating combinatorial explosion.
  - Retrieval: ES keyword filters can narrow candidates on any axis
    before scoring, keeping top-k hybrid retrieval cheap.
  - Training: the model learns to emit tags per-axis rather than memorizing
    compound labels, which generalizes to unseen situations.

Each axis is closed-vocabulary. Adding a new value is a deliberate
decision — the generator and the retriever both assume the vocabulary
is finite and stable. If a new situation doesn't fit, first consider
whether an existing tag is adequate before extending.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# AXIS 1 — pressure_type
# What kind of adversarial force is operating on the parties?
# A single event may carry multiple tags when the pressure is compound
# (e.g. both social_exclusion and economic_siege during Shi'b Abi Talib).
# ---------------------------------------------------------------------------

PRESSURE_TYPE: dict[str, str] = {
    "physical_persecution": "العنف الجسدي والتعذيب والتهديد بالقتل",
    "social_exclusion":     "المقاطعة والنبذ والإخراج من الجماعة",
    "economic_siege":       "الحصار الاقتصادي، مصادرة الأموال، قطع الرزق",
    "verbal_attack":        "السخرية، الاتهام، القذف، الافتراء",
    "intellectual_challenge": "طلب البرهان، الجدل العقلي، تحدي الحجة",
    "political_pressure":   "إكراه السلطة، فرض الإرادة بقوة الدولة",
    "legal_coercion":       "استعمال القانون أو العرف سلاحاً للإضرار",
    "moral_temptation":     "الإغراء بالمال أو المنصب أو التسوية على حساب المبدأ",
    "internal_betrayal":    "خيانة من داخل الصف، نفاق، تسريب",
    "family_pressure":      "ضغط الأقارب، معارضة الأهل للمبدأ",
    "psychological_pressure": "الحزن، اليأس، الوحدة، الإحباط",
    "existential_threat":   "تهديد وجودي للفرد أو الجماعة",
    "moral_failure_by_self": "سقوط أخلاقي من المؤمن نفسه، لا من خصم",
    "none":                 "لا ضغط عدائي — موقف تشريعي أو إرشادي خالص",
}

# ---------------------------------------------------------------------------
# AXIS 2 — parties
# Who is up against whom? The power asymmetry matters for analogy.
# ---------------------------------------------------------------------------

PARTIES: dict[str, str] = {
    "principled_minority_vs_powerful_majority": "أقلية على الحق في مواجهة أكثرية ذات قوة",
    "individual_vs_majority":                   "فرد واحد يواجه جماعة",
    "ally_vs_ally_dispute":                     "خلاف بين حلفاء/إخوة في نفس الصف",
    "leader_vs_follower":                       "توتر بين قائد وتابع",
    "insider_hypocrite_vs_sincere":             "منافق داخل الصف ضد مؤمن صادق",
    "believer_vs_unbeliever":                   "مواجهة عقدية مباشرة",
    "kin_vs_kin":                               "نزاع داخل الأسرة الممتدة",
    "spouse_vs_spouse":                         "نزاع بين زوجين",
    "parent_vs_child":                          "توتر بين الوالد والولد",
    "ruler_vs_ruled":                           "سلطة سياسية في مواجهة رعية",
    "claimant_vs_accused":                      "خصومة قضائية بين مدّعٍ ومدّعى عليه",
    "debtor_vs_creditor":                       "علاقة مديونية ذات توتر",
    "community_vs_outsider":                    "جماعة مقابل دخيل/غريب",
    "self_vs_self":                             "صراع داخلي في النفس الواحدة",
    "teacher_vs_student":                       "توتر بين معلم ومتعلم",
    "none":                                     "بلا أطراف متقابلة — سرد أو تشريع عام",
    "family_pressure":                          "ضغط الأسرة (طرف متعدد)",
}

# ---------------------------------------------------------------------------
# AXIS 3 — stakes
# What is on the line? What would be lost if the wrong move is made?
# ---------------------------------------------------------------------------

STAKES: dict[str, str] = {
    "physical_safety":        "الحياة والسلامة الجسدية",
    "livelihood":             "الرزق ومصادر العيش",
    "reputation_honor":       "السمعة والعرض",
    "community_cohesion":     "وحدة الجماعة واستقرارها",
    "religious_freedom":      "حرية التدين والعبادة",
    "truth_vs_falsehood":     "بقاء الحق ظاهراً أمام الباطل",
    "justice_vs_privilege":   "تحقيق العدل أمام المحاباة",
    "property_rights":        "حقوق الملكية والتصرف",
    "family_integrity":       "تماسك الأسرة ووحدتها",
    "personal_dignity":       "الكرامة الفردية",
    "collective_survival":    "بقاء الجماعة من الانقراض",
    "spiritual_integrity":    "سلامة القلب والنية",
    "generational_legacy":    "ما يُترك للأجيال التالية",
    "knowledge_access":       "إمكانية الوصول إلى المعرفة والحقيقة",
    "trust_between_parties":  "الثقة الاجتماعية بين الأطراف",
    "divine_acceptance":      "القبول عند الله — الآخرة",
}

# ---------------------------------------------------------------------------
# AXIS 4 — response_category
# The type of action the Quranic response prescribed or validated.
# This is what the model will look up when it needs to prescribe.
# ---------------------------------------------------------------------------

RESPONSE_CATEGORY: dict[str, str] = {
    "endurance_without_retaliation":    "الصبر دون ردّ بالمثل",
    "strategic_withdrawal":             "الانسحاب التكتيكي / الهجرة",
    "intellectual_rebuttal":            "الرد بالحجة العقلية",
    "legal_innovation":                 "تشريع حكم جديد يعالج الوضع",
    "moral_rebuke":                     "توبيخ أخلاقي علني",
    "consolation_and_thabaat":          "التسلية وتثبيت القلب",
    "confrontation_with_truth":         "المواجهة المباشرة بالحق",
    "compromise_for_larger_goal":       "التنازل التكتيكي لمصلحة أعلى",
    "active_resistance":                "المقاومة النشطة المسلحة",
    "organizational_response":          "بناء مؤسسة أو نظام جديد",
    "forgiveness_from_power":           "العفو من موقع القدرة",
    "refusal_to_compromise":            "رفض التنازل في الثوابت",
    "seeking_allies":                   "البحث عن حلفاء وداعمين",
    "private_counsel":                  "النصح في السر لا في العلن",
    "public_declaration":               "الإعلان العلني للموقف",
    "self_correction":                  "مراجعة النفس والتوبة",
    "deferral_of_judgement":            "تأجيل الحكم حتى تتضح البينة",
    "silence_as_answer":                "السكوت حجة",
    "transfer_of_domain":               "نقل المعركة من ميدان إلى آخر",
    "witnessing_and_documentation":     "التوثيق والشهادة",
    # Cross-axis aliases — values that double as response categories
    "accountability_proportional_to_power": "المحاسبة بقدر السلطة",
    "clarification":                    "الإيضاح وإزالة اللبس",
    "consistency_public_and_private":   "الاتساق في العلن والسر",
    "consultation_before_decision":     "الشورى قبل القرار",
    "dispute_resolution_by_neutral":    "الفصل بطرف محايد",
    "gradualism_in_hard_change":        "التدرج في التغيير الصعب",
    "refuge_with_god_against_despair":  "الالتجاء إلى الله",
    "refusing_to_legitimize_falsehood": "رفض إضفاء الشرعية على الباطل",
    "scaling_principle_to_context":     "تطبيق المبدأ بحسب السياق",
    "solidarity_around_principle":      "التضامن حول المبدأ",
    "teaching_through_demonstration":   "التعليم بالقدوة",
    "warning_against_arrogance":        "التحذير من الكبر",
    "wealth_as_trust_not_ownership":    "المال أمانة لا ملك",
}

# ---------------------------------------------------------------------------
# AXIS 5 — principle_class
# The transferable principle extracted from the event. This is the axis
# most directly useful for cross-domain analogy: two events with different
# surface features but the same principle_class are strong candidates
# for shared verse application.
# ---------------------------------------------------------------------------

PRINCIPLE_CLASS: dict[str, str] = {
    "patience_under_collective_punishment": "الصبر على العقوبة الجماعية الظالمة",
    "source_integrity_over_popularity":     "تقديم صدق المصدر على قبول الناس",
    "truth_before_kinship":                 "الحق مقدّم على صلة القرابة",
    "justice_requires_documentation":       "العدل يستلزم التوثيق",
    "mercy_as_strategic_choice":            "الرحمة خيار استراتيجي لا ضعف",
    "gradualism_in_hard_change":            "التدرج في التغيير الصعب",
    "honesty_over_expedience":              "الصدق مقدّم على المنفعة الآنية",
    "principled_refusal_to_transgress":     "رفض التنازل عن الثوابت مهما كان الثمن",
    "leadership_accountability":            "مسؤولية القائد أشد",
    "economic_justice_as_worship":          "العدل الاقتصادي جزء من العبادة",
    "sincerity_over_performance":           "النية قبل الشكل",
    "chosen_hardship_over_compromise":      "اختيار المشقة على التنازل",
    "correction_of_self_first":             "إصلاح النفس قبل إصلاح الغير",
    "solidarity_around_principle":          "التضامن حول المبدأ لا حول الأشخاص",
    "protection_of_the_weak":               "حماية الضعيف معيار صحة المجتمع",
    "boundaries_in_intimate_relations":     "الحدود في العلاقات الخاصة",
    "knowledge_before_action":              "العلم قبل العمل",
    "consultation_before_decision":         "الشورى قبل القرار",
    "divine_testing_mechanism":             "الابتلاء سنّة التمحيص لا عقوبة",
    "intention_determines_value":           "النية تحدد قيمة العمل",
    "warning_against_arrogance":            "الكبر هلاك للفرد والجماعة",
    "balance_between_fear_and_hope":        "التوازن بين الخوف والرجاء",
    "rejection_of_blind_imitation":         "رفض التقليد الأعمى",
    "consistency_public_and_private":       "الاتساق بين العلن والسر",
    "repentance_as_open_door":              "التوبة باب مفتوح دائماً",
    "refuge_with_god_against_despair":      "الالتجاء إلى الله عند اليأس",
    "truth_is_independent_of_carrier":      "الحق يُقبل ولو من خصم، ويُرد ولو من قريب",
    "collective_obligation_above_personal": "الواجب الجماعي مقدّم على المصلحة الفردية",
    "procedural_justice_over_outcome":      "عدالة الإجراء قبل عدالة النتيجة",
    "preserving_channels_of_return":        "إبقاء أبواب العودة مفتوحة للمخالف",
    "scaling_principle_to_context":         "تطبيق المبدأ بحسب قدرة المخاطب",
    "no_coercion_in_conviction":            "لا إكراه في الاعتقاد",
    "distinguishing_enemy_from_outsider":   "التفريق بين الخصم والغريب المسالم",
    "accountability_proportional_to_power": "المحاسبة تتناسب مع القدرة",
    "trust_is_earned_by_consistency":       "الثقة تُبنى بالاتساق الطويل",
    "wealth_as_trust_not_ownership":        "المال أمانة لا تملك مطلق",
    "forgiveness_without_surrender":        "العفو لا يعني التخلي عن الحق",
    "dispute_resolution_by_neutral":        "فصل النزاع يحتاج طرفاً محايداً",
    "refusing_to_legitimize_falsehood":     "رفض إضفاء الشرعية على الباطل",
    "teaching_through_demonstration":       "التعليم بالقدوة أبلغ من الفتوى",
    "limits_of_personal_discretion":        "حدود الاجتهاد الشخصي أمام النص",
    "public_good_over_private_comfort":     "المصلحة العامة فوق الراحة الخاصة",
    "testing_loyalty_under_stress":         "الضغط يفرز الصفوف",
    "legitimacy_follows_method":            "الغاية لا تبرر الوسيلة",
    "signs_require_reflection_not_proof":   "الآيات للتأمل لا للتحدي",
    # Cross-axis aliases — values that double as principles
    "compromise_for_larger_goal":           "التنازل التكتيكي لمصلحة أعلى",
    "confronting_falsehood_even_posthumously": "مواجهة الباطل حتى بعد الموت",
    "justice_vs_privilege":                 "العدل قبل المحاباة",
    "public_declaration":                   "الإعلان العلني",
    "seeking_allies":                       "السعي للحلفاء",
    "witnessing_and_documentation":         "الشهادة والتوثيق",
}

# ---------------------------------------------------------------------------
# AXIS 6 — polarity
# The illocutionary force of the Quranic response — what speech-act
# the revelation performed on this situation.
# ---------------------------------------------------------------------------

POLARITY: dict[str, str] = {
    "command":        "أمر بفعل شيء",
    "prohibition":    "نهي عن فعل شيء",
    "praise":         "ثناء على موقف",
    "rebuke":         "ذم وتوبيخ",
    "warning":        "تحذير من عاقبة",
    "promise":        "وعد بخير",
    "consolation":    "تسلية وتثبيت",
    "argument":       "إقامة حجة عقلية",
    "story":          "سرد قصصي للعبرة",
    "legislation":    "تشريع حكم جديد",
    "clarification":  "إزالة لبس أو سؤال",
    "rhetorical_question": "سؤال لتحريك التفكير",
    "oath":           "قسم لتوكيد معنى",
}


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

ALL_AXES: dict[str, dict[str, str]] = {
    "pressure_type":     PRESSURE_TYPE,
    "parties":           PARTIES,
    "stakes":            STAKES,
    "response_category": RESPONSE_CATEGORY,
    "principle_class":   PRINCIPLE_CLASS,
    "polarity":          POLARITY,
}


def validate_tags(tags: dict[str, Any]) -> list[str]:
    """Return list of validation errors (empty = valid).

    Each axis in `tags` must be either a single string value or a list
    of strings, and every value must exist in the controlled vocabulary
    for that axis. Unknown axes are errors.
    """
    errors: list[str] = []
    for axis, value in tags.items():
        if axis not in ALL_AXES:
            errors.append(f"unknown axis: {axis}")
            continue
        vocab = ALL_AXES[axis]
        values = value if isinstance(value, list) else [value]
        for v in values:
            if v not in vocab:
                errors.append(f"{axis}: unknown value '{v}'")
    return errors


def summarize_tags_ar(tags: dict[str, Any]) -> str:
    """Render a tags dict as a one-line Arabic summary (for training answers)."""
    parts: list[str] = []
    labels = {
        "pressure_type":     "نوع الضغط",
        "parties":           "الأطراف",
        "stakes":            "المخاطر",
        "response_category": "الاستجابة",
        "principle_class":   "المبدأ",
        "polarity":          "وظيفة الخطاب",
    }
    for axis, label in labels.items():
        if axis not in tags:
            continue
        val = tags[axis]
        values = val if isinstance(val, list) else [val]
        vocab = ALL_AXES[axis]
        rendered = "، ".join(vocab.get(v, v) for v in values)
        parts.append(f"{label}: {rendered}")
    return " | ".join(parts)


# Minimal required axes — every event MUST have these, the rest are optional.
REQUIRED_AXES: tuple[str, ...] = (
    "pressure_type",
    "parties",
    "stakes",
    "response_category",
    "principle_class",
    "polarity",
)
