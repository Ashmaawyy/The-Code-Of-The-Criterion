# Islamic Sharia Knowledge Base — Digital Sources Catalog

## Status: Research Phase (Sprint 3 Planning)
## Author: Al-Furqan R&D Team
## Date: 2026-03-19

---

## 📖 1. QURAN SOURCES

### Datasets (HuggingFace)
| Source | URL | Size | Notes |
|--------|-----|------|-------|
| tarteel-ai/quran-tafsir | https://huggingface.co/datasets/tarteel-ai/quran-tafsir | 6.24k rows | ⭐ Multiple tafsir (Ibn Kathir, etc.) — **TOP PICK** |
| siddiqiya/ar-quran-hadith14books-MSA | https://huggingface.co/datasets/siddiqiya/ar-quran-hadith14books-MSA | 34.6k rows | Quran + 14 Hadith books in MSA |
| Nasaq-GP/Quran_tafsir | https://huggingface.co/datasets/Nasaq-GP/Quran_tafsir | 6.24k rows | Quran with tafsir |
| raiyanruhan/Quran-With-Tafsir | https://huggingface.co/datasets/raiyanruhan/Quran-With-Tafsir | 6.24k rows | Full Quran + Tafsir |

### APIs (GitHub)
| Source | URL | Stars | Notes |
|--------|-----|-------|-------|
| gadingnst/quran-api | https://github.com/gadingnst/quran-api | 811⭐ | Full Quran JSON + Tafsir + Audio |
| spa5k/tafsir_api | https://github.com/spa5k/tafsir_api | 147⭐ | ⭐ Multi-language Tafsir API (Go) — **TOP PICK** |
| penggguna/QuranJSON | https://github.com/penggguna/QuranJSON | 180⭐ | Complete Quran JSON |
| misraj-ai/quranhub | https://github.com/misraj-ai/quranhub | 56⭐ | REST API with multiple editions |
| djalal/quran-mcp-server | https://github.com/djalal/quran-mcp-server | 62⭐ | Quran.com API MCP integration |

### Raw Data (GitHub)
| Source | URL | Notes |
|--------|-----|-------|
| zonetecde/mushaf-layout | https://github.com/zonetecde/mushaf-layout | 604-page Madani Mushaf dataset — JSON |
| mostafaahmed97/asbab-al-nuzul-dataset | https://github.com/mostafaahmed97/asbab-al-nuzul-dataset | Asbab al-Nuzul (reasons of revelation) — JSON/CSV |
| nafiskabbo/quran-dataset | https://github.com/nafiskabbo/quran-dataset | Configurable Quran export (JSON/CSV) |
| CheeseWithSauce/TheHolyQuranJSONFormat | https://github.com/CheeseWithSauce/TheHolyQuranJSONFormat | Complete Quran — 114 per-surah JSON files |

---

## 📚 2. HADITH SOURCES

### Datasets (HuggingFace)
| Source | URL | Size | Notes |
|--------|-----|------|-------|
| meeAtif/hadith_datasets | https://huggingface.co/datasets/meeAtif/hadith_datasets | 33.7k rows | ⭐ Large hadith collection — 497 downloads — **TOP PICK** |
| arbml/Hadith | https://huggingface.co/datasets/arbml/Hadith | 124k rows | ⭐ Largest Arabic hadith dataset |
| M-AI-C/all_hadith | https://huggingface.co/datasets/M-AI-C/all_hadith | 34.4k rows | All major hadith books |
| fawazahmed0/hadith-data | https://huggingface.co/datasets/fawazahmed0/hadith-data | 300k rows | ⭐ Massive multi-source hadith — **TOP PICK** |
| arbml/LK_Hadith | https://huggingface.co/datasets/arbml/LK_Hadith | 34.1k rows | Leeds University Hadith Corpus |
| rwmasood/hadith-qa-pair | https://huggingface.co/datasets/rwmasood/hadith-qa-pair | 68.9k rows | ⭐ QA pairs from hadith — ready for RAG |
| Siyam/bukhari-hadith-alpaca | https://huggingface.co/datasets/Siyam/bukhari-hadith-alpaca | 842 rows | Alpaca-format for fine-tuning |
| arbml/Quran_Hadith | https://huggingface.co/datasets/arbml/Quran_Hadith | 8.14k rows | Combined Quran + Hadith |
| MohamedAmineC/hadith-vector-db | https://huggingface.co/datasets/MohamedAmineC/hadith-vector-db | — | ⭐⭐ Pre-built Vector DB! |
| ReligiousLLMs/Quran_Hadith_explain_verse_8K | https://huggingface.co/datasets/ReligiousLLMs/Quran_Hadith_explain_verse_8K | 7.95k rows | Verse explanations |

### GitHub Repositories
| Source | URL | Stars | Notes |
|--------|-----|-------|-------|
| ShathaTm/LK-Hadith-Corpus | https://github.com/ShathaTm/LK-Hadith-Corpus | 91⭐ | ⭐ Leeds + King Saud University corpus — **ACADEMIC QUALITY** |
| ShathaTm/Quran_Hadith_Datasets | https://github.com/ShathaTm/Quran_Hadith_Datasets | 11⭐ | QQ and QH datasets (research paper) |
| alfa155518/Islamic-API-S | https://github.com/alfa155518/Islamic-API-S | 8⭐ | Quran + Hadith + Azkar + Prayer Times APIs |
| hadith-plugin/hadith-dataset | https://github.com/hadith-plugin/hadith-dataset | 3⭐ | Structured hadith data |
| mlotfic/al-hadith-dataset | https://github.com/mlotfic/al-hadith-dataset | 1⭐ | Structured al-hadith |
| nafiskabbo/hadith-dataset | https://github.com/nafiskabbo/hadith-dataset | 1⭐ | Configurable hadith export pipeline |
| Jaguar16/open-hadith-data | https://github.com/Jaguar16/open-hadith-data | 1⭐ | Open-source hadith data |

---

## ⚖️ 3. FIQH & USUL AL-FIQH SOURCES

### Digital Sources
| Source | URL | Notes |
|--------|-----|-------|
| zakisheriff/Akhi-AI | https://github.com/zakisheriff/Akhi-AI | Quran, Hadith & Fiqh-based answers with citations |

### Gap: Fiqh Datasets
**⚠️ CRITICAL GAP: No comprehensive fiqh/usul al-fiqh dataset exists on GitHub or HuggingFace.**

Recommended approach:
1. **Manually curate** 50-100 core fiqh rules (القواعد الفقهية الخمس الكبرى + فروعها)
2. **Scrape/digitize** from trusted sources:
   - IslamQA.info (فتاوى)
   - الموسوعة الفقهية الكويتية (encyclopedia)
   - مجمع الفقه الإسلامي decisions
3. **Partner with Islamic universities** for annotated datasets

---

## 🧠 4. ARABIC NLP & EMBEDDING MODELS

### Models (HuggingFace)
| Model | URL | Notes |
|-------|-----|-------|
| CAMeL-Lab/bert-base-arabic-camelbert-ca | https://huggingface.co/CAMeL-Lab/bert-base-arabic-camelbert-ca | ⭐ Classical Arabic BERT — **BEST for Quran/Hadith** |
| aubmindlab/bert-base-arabertv02 | https://huggingface.co/aubmindlab/bert-base-arabertv02 | Arabic BERT v2 — general purpose |
| sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 | HF | Multilingual sentence embeddings (includes Arabic) |

---

## 📋 5. RECOMMENDED MVP STACK (Sprint 3)

### Phase A: Core Knowledge Base
1. **Quran**: `tarteel-ai/quran-tafsir` + `spa5k/tafsir_api` (Ibn Kathir + Al-Jalalain)
2. **Hadith**: `fawazahmed0/hadith-data` (300k) + `MohamedAmineC/hadith-vector-db` (pre-vectorized!)
3. **Combined**: `siddiqiya/ar-quran-hadith14books-MSA` (14 books standardized)
4. **QA Pairs**: `rwmasood/hadith-qa-pair` (68.9k ready-to-use QA)

### Phase B: Embedding
1. **Primary**: `CAMeL-Lab/bert-base-arabic-camelbert-ca` (Classical Arabic)
2. **Fallback**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

### Phase C: Manual Curation
1. **50 Core Fiqh Rules** (القواعد الفقهية)
2. **Usul al-Fiqh methodology** (أصول الفقه — rules of derivation)
3. **Asbab al-Nuzul**: `mostafaahmed97/asbab-al-nuzul-dataset`

### Estimated Sizes
| Source | Records | Vector DB Size (est.) |
|--------|---------|----------------------|
| Quran + Tafsir | ~6,236 verses × multiple tafsir | ~50MB |
| Hadith (14 books) | ~34,000 | ~200MB |
| Hadith (extended) | ~300,000 | ~1.5GB |
| QA Pairs | ~68,900 | ~400MB |
| Fiqh Rules | ~100 | ~5MB |
| **Total MVP** | **~110,000** | **~650MB** |
| **Total Extended** | **~410,000** | **~2.2GB** |

---

## 🔍 6. QUALITY CRITERIA FOR SOURCE SELECTION

All sources must meet:
1. **Authenticity**: Verified chain of transmission (isnad) for hadith
2. **Grading**: Sahih/Hasan/Daif classification preserved
3. **Arabic Original**: Must include original Arabic text (not translation-only)
4. **Citation**: Each entry must be traceable to original source (book, chapter, number)
5. **License**: Open-source or permissive license for use in research

---

## 🚧 7. GAPS TO FILL

| Gap | Priority | Approach |
|-----|----------|----------|
| Usul al-Fiqh rules DB | 🔴 Critical | Manual curation by scholars |
| Scholarly annotations | 🔴 Critical | Partner with Islamic universities |
| Fatwa database | 🟡 High | IslamQA.info scraping + curation |
| Maqasid al-Shariah mapping | 🟡 High | Manual mapping to gates |
| Cross-reference (Quran ↔ Hadith) | 🟢 Medium | Use existing tafsir references |
| Audio lectures (annotated) | 🟢 Medium | YouTube + manual annotation |

---

_This document will be updated as more sources are discovered and evaluated._
