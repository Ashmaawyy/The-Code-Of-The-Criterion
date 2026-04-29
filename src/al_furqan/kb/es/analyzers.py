"""Arabic text analyzer definitions for Elasticsearch.

The ``arabic_furqan`` analyzer replicates the exact normalization behavior of
``text_utils.normalize_arabic()`` but executes at index time — once per
document — rather than at query time on every comparison.

Normalization steps (applied as char_filters before tokenization):
    1. Strip diacritics (tashkeel): fatha, damma, kasra, sukun, shadda, etc.
    2. Normalize alef variants (إ أ آ ٱ) → ا
    3. Normalize taa marbouta (ة) → haa (ه)
    4. Normalize alef maqsura (ى) → yaa (ي)
    5. Strip tatweel (kashida)
    6. Strip Quranic decoration marks (﴿ ﴾ ۝ ۞ etc.)

No stemming is applied — Quranic text is sacred and precise. Stems would
conflate words that are theologically distinct.
"""

# -- Char filters (each performs one normalization step) ----------------------

CHAR_FILTER_STRIP_DIACRITICS = {
    "type": "pattern_replace",
    "pattern": (
        "["
        "\u0610-\u061A"   # Quranic signs above
        "\u064B-\u065F"   # tashkeel (fatha, damma, kasra, etc.)
        "\u0670"          # superscript alef
        "\u06D6-\u06DC"   # small Quranic marks
        "\u06DF-\u06E4"   # more Quranic marks
        "\u06E7\u06E8"    # yeh barree / reversed damma
        "\u06EA-\u06ED"   # additional marks
        "]"
    ),
    "replacement": "",
}

CHAR_FILTER_NORMALIZE_ALEF = {
    "type": "pattern_replace",
    "pattern": "[\u0625\u0623\u0622\u0671]",  # إ أ آ ٱ
    "replacement": "\u0627",                    # → ا
}

CHAR_FILTER_NORMALIZE_TAA_MARBOUTA = {
    "type": "pattern_replace",
    "pattern": "\u0629",   # ة
    "replacement": "\u0647",  # → ه
}

CHAR_FILTER_NORMALIZE_ALEF_MAQSURA = {
    "type": "pattern_replace",
    "pattern": "\u0649",   # ى
    "replacement": "\u064A",  # → ي
}

CHAR_FILTER_STRIP_TATWEEL = {
    "type": "pattern_replace",
    "pattern": "\u0640",
    "replacement": "",
}

CHAR_FILTER_STRIP_DECORATIONS = {
    "type": "pattern_replace",
    "pattern": "[\uFD3F\uFD3E\u06DD\uFDFA\uFDFB\uFE70-\uFEFF﴿﴾۝۞]",
    "replacement": "",
}


# -- Assembled analysis settings for index creation ---------------------------

ANALYSIS_SETTINGS = {
    "analysis": {
        "char_filter": {
            "strip_diacritics": CHAR_FILTER_STRIP_DIACRITICS,
            "normalize_alef": CHAR_FILTER_NORMALIZE_ALEF,
            "normalize_taa_marbouta": CHAR_FILTER_NORMALIZE_TAA_MARBOUTA,
            "normalize_alef_maqsura": CHAR_FILTER_NORMALIZE_ALEF_MAQSURA,
            "strip_tatweel": CHAR_FILTER_STRIP_TATWEEL,
            "strip_decorations": CHAR_FILTER_STRIP_DECORATIONS,
        },
        "analyzer": {
            "arabic_furqan": {
                "type": "custom",
                "tokenizer": "standard",
                "char_filter": [
                    "strip_diacritics",
                    "normalize_alef",
                    "normalize_taa_marbouta",
                    "normalize_alef_maqsura",
                    "strip_tatweel",
                    "strip_decorations",
                ],
                "filter": ["lowercase"],
            },
        },
    },
}
