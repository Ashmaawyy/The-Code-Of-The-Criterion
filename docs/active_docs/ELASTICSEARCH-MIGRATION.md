# Elasticsearch Migration Plan

**Status:** Completed
**Date:** 2026-03-30
**Replaces:** JSON file-based storage + ChromaDB + Python regex matching
**Result:** All legacy modules deleted, ChromaDB dependency removed, all runtime I/O through ES

---

## Table of Contents

1. [Motivation](#motivation)
2. [Architecture Overview](#architecture-overview)
3. [Index Schema Design](#index-schema-design)
4. [Arabic Text Analysis Pipeline](#arabic-text-analysis-pipeline)
5. [Migration Steps](#migration-steps)
6. [Query Migration Guide](#query-migration-guide)
7. [Infrastructure Requirements](#infrastructure-requirements)
8. [Rollback Plan](#rollback-plan)

---

## Motivation

### Current State

| Component | Technology | Problem |
|-----------|-----------|---------|
| Verse/hadith matching | Python sliding-window regex | O(n*m) per query, ~6236 verses scanned every time |
| Arabic normalization | `normalize_arabic()` at query time | Re-normalizes the entire corpus on every search |
| Knowledge graph | JSON file (`sample_graph.json`) | No query language, loaded entirely into memory |
| Vector embeddings | ChromaDB | Separate service, no graph awareness |
| Verdict storage | JSON files on disk | No indexing, linear scan for retrieval |
| Feedback storage | JSON files on disk | Same limitations |

### Target State

One Elasticsearch cluster replacing all of the above:
- Arabic text analysis at **index time** (normalize once, query fast)
- `match_phrase` for consecutive-word matching (replaces sliding window)
- Nested documents for graph edges (replaces JSON adjacency lists)
- `dense_vector` fields for embeddings (replaces ChromaDB)
- Full-text + keyword + date indexing on verdicts/feedback

---

## Architecture Overview

```
Before:                              After:

  quran_complete.json ──┐            ┌──────────────────────────┐
  hadith_sample.json ───┤            │     Elasticsearch 8.x    │
  sample_graph.json ────┤            │                          │
  lessons_enriched/ ────┤  migrate   │  idx: furqan_quran       │
  verdicts/*.json ──────┤ ────────→  │  idx: furqan_hadith      │
  feedback/*.json ──────┤            │  idx: furqan_graph       │
  ChromaDB ─────────────┘            │  idx: furqan_lessons     │
                                     │  idx: furqan_verdicts    │
  Python sliding-window              │  idx: furqan_feedback    │
  normalize_arabic()     replaced    │                          │
  _has_consecutive_match  ────────→  │  analyzer: arabic_furqan │
                                     │  query: match_phrase     │
                                     └──────────────────────────┘
```

---

## Index Schema Design

### 1. `furqan_quran` — Quranic Verses

**Source:** `data/quran/quran_complete.json` (6,236 documents)

```json
{
  "mappings": {
    "properties": {
      "surah":           { "type": "integer" },
      "ayah":            { "type": "integer" },
      "verse_key":       { "type": "keyword" },
      "surah_name_ar":   { "type": "keyword" },
      "surah_name_en":   { "type": "keyword" },
      "text_ar": {
        "type": "text",
        "analyzer": "arabic_furqan",
        "fields": {
          "raw": { "type": "keyword", "ignore_above": 2000 }
        }
      },
      "text_en": {
        "type": "text",
        "analyzer": "english"
      },
      "juz":             { "type": "integer" },
      "page":            { "type": "integer" },
      "revelation_type": { "type": "keyword" },
      "topics":          { "type": "keyword" },
      "embedding": {
        "type": "dense_vector",
        "dims": 384,
        "index": true,
        "similarity": "cosine"
      }
    }
  }
}
```

**Document ID pattern:** `{surah}:{ayah}` (e.g., `2:255`)

---

### 2. `furqan_hadith` — Hadith Collection

**Source:** `data/hadith/hadith_sample.json` (55 documents, will grow)

```json
{
  "mappings": {
    "properties": {
      "collection_name": { "type": "keyword" },
      "number":          { "type": "integer" },
      "hadith_key":      { "type": "keyword" },
      "text_ar": {
        "type": "text",
        "analyzer": "arabic_furqan",
        "fields": {
          "raw": { "type": "keyword", "ignore_above": 5000 }
        }
      },
      "text_en": {
        "type": "text",
        "analyzer": "english"
      },
      "narrator":        { "type": "keyword" },
      "grading":         { "type": "keyword" },
      "topics":          { "type": "keyword" },
      "embedding": {
        "type": "dense_vector",
        "dims": 384,
        "index": true,
        "similarity": "cosine"
      }
    }
  }
}
```

**Document ID pattern:** `{collection_name}:{number}` (e.g., `bukhari:1`)

---

### 3. `furqan_graph` — Knowledge Graph Edges

**Source:** `data/graph/sample_graph.json` (73 nodes, 95 edges)

Graph nodes are stored as documents in their respective indices (`furqan_quran`,
`furqan_hadith`, etc.). This index stores **edges only** — relationships between
entities.

```json
{
  "mappings": {
    "properties": {
      "source":          { "type": "keyword" },
      "target":          { "type": "keyword" },
      "edge_type":       { "type": "keyword" },
      "weight":          { "type": "float" },
      "provenance":      { "type": "keyword" },
      "provenance_type": { "type": "keyword" },
      "reference":       { "type": "text", "analyzer": "arabic_furqan" },
      "verified_by":     { "type": "keyword" },
      "confidence":      { "type": "float" },
      "metadata":        { "type": "object", "enabled": false }
    }
  }
}
```

**Document ID pattern:** `{source}--{edge_type}--{target}` (e.g., `ayah:2:275--BELONGS_TO--topic:riba`)

**Graph traversal** is done via two queries:
```
# Forward edges from a node
GET furqan_graph/_search
{ "query": { "term": { "source": "ayah:6:80" } } }

# Reverse edges to a node
GET furqan_graph/_search
{ "query": { "term": { "target": "ayah:6:80" } } }
```

For multi-hop traversal (depth > 1), the application collects first-hop results
then issues a second query — acceptable at this scale (< 1000 edges).

---

### 4. `furqan_lessons` — Enriched Lesson Data

**Source:** `data/lessons/lessons_enriched_json/` (~24 documents)

```json
{
  "mappings": {
    "properties": {
      "lesson_number":  { "type": "integer" },
      "surah":          { "type": "integer" },
      "title":          { "type": "keyword" },
      "total_chapters": { "type": "integer" },
      "chapters": {
        "type": "nested",
        "properties": {
          "chapter_number": { "type": "integer" },
          "title":          { "type": "text", "analyzer": "arabic_furqan" },
          "content": {
            "type": "text",
            "analyzer": "arabic_furqan",
            "fields": {
              "english": { "type": "text", "analyzer": "english" }
            }
          },
          "taught_verses": {
            "type": "nested",
            "properties": {
              "verse_key": { "type": "keyword" },
              "surah":     { "type": "integer" },
              "ayah":      { "type": "integer" },
              "text_ar":   { "type": "text", "analyzer": "arabic_furqan" }
            }
          },
          "linked_verses": {
            "type": "nested",
            "properties": {
              "verse_key": { "type": "keyword" },
              "surah":     { "type": "integer" },
              "ayah":      { "type": "integer" },
              "text_ar":   { "type": "text", "analyzer": "arabic_furqan" }
            }
          },
          "mentioned_ahadeeth": {
            "type": "nested",
            "properties": {
              "collection": { "type": "keyword" },
              "number":     { "type": "integer" },
              "text_ar":    { "type": "text", "analyzer": "arabic_furqan" }
            }
          }
        }
      }
    }
  }
}
```

**Document ID pattern:** `lesson_{number:02d}` (e.g., `lesson_01`)

---

### 5. `furqan_verdicts` — Evaluation Verdicts

**Source:** `verdicts/*.json` (runtime-generated)

```json
{
  "mappings": {
    "properties": {
      "verdict_id":       { "type": "keyword" },
      "question":         { "type": "text", "analyzer": "arabic_furqan" },
      "primary_system":   { "type": "keyword" },
      "origin_gate":      { "type": "keyword" },
      "friction_points":  { "type": "text", "analyzer": "arabic_furqan" },
      "revised_reasoning": { "type": "text", "analyzer": "arabic_furqan" },
      "final_judgment":   { "type": "text", "analyzer": "arabic_furqan" },
      "total_score":      { "type": "float" },
      "passes":           { "type": "boolean" },
      "status":           { "type": "keyword" },
      "timestamp":        { "type": "date" },
      "gate_scores": {
        "type": "nested",
        "properties": {
          "gate_id":   { "type": "keyword" },
          "score":     { "type": "float" },
          "reasoning": { "type": "text" }
        }
      },
      "embedding": {
        "type": "dense_vector",
        "dims": 384,
        "index": true,
        "similarity": "cosine"
      }
    }
  }
}
```

**Document ID pattern:** `{verdict_id}`

---

### 6. `furqan_feedback` — Human Review Feedback

**Source:** `feedback_store` (runtime-generated)

```json
{
  "mappings": {
    "properties": {
      "feedback_id":     { "type": "keyword" },
      "verdict_id":      { "type": "keyword" },
      "reviewer":        { "type": "keyword" },
      "rating":          { "type": "keyword" },
      "gate_corrections": { "type": "object", "enabled": false },
      "notes":           { "type": "text" },
      "timestamp":       { "type": "date" }
    }
  }
}
```

**Document ID pattern:** `{feedback_id}`

---

## Arabic Text Analysis Pipeline

The core of the migration — replaces `normalize_arabic()` + `_has_consecutive_match()`.

### Custom Analyzer: `arabic_furqan`

```json
{
  "settings": {
    "analysis": {
      "char_filter": {
        "strip_diacritics": {
          "type": "pattern_replace",
          "pattern": "[\\u0610-\\u061A\\u064B-\\u065F\\u0670\\u06D6-\\u06DC\\u06DF-\\u06E4\\u06E7\\u06E8\\u06EA-\\u06ED]",
          "replacement": ""
        },
        "normalize_alef": {
          "type": "pattern_replace",
          "pattern": "[\\u0625\\u0623\\u0622\\u0671]",
          "replacement": "\\u0627"
        },
        "normalize_taa_marbouta": {
          "type": "pattern_replace",
          "pattern": "\\u0629",
          "replacement": "\\u0647"
        },
        "normalize_alef_maqsura": {
          "type": "pattern_replace",
          "pattern": "\\u0649",
          "replacement": "\\u064A"
        },
        "strip_tatweel": {
          "type": "pattern_replace",
          "pattern": "\\u0640",
          "replacement": ""
        },
        "strip_decorations": {
          "type": "pattern_replace",
          "pattern": "[\\uFD3F\\uFD3E\\u06DD\\uFDFA\\uFDFB﴿﴾۝۞]",
          "replacement": ""
        }
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
            "strip_decorations"
          ],
          "filter": ["lowercase"]
        }
      }
    }
  }
}
```

This analyzer replicates the exact behavior of the Python `normalize_arabic()`
function but runs **at index time**, once per document. Queries against these
fields are automatically analyzed with the same pipeline.

### Why no Arabic stemmer?

We intentionally omit stemming. The Quranic text is sacred and precise — stems
would conflate words that are theologically distinct. The char_filter approach
preserves exact word forms after normalization, which is what the current Python
pipeline does.

---

## Migration Steps

### Phase 0: Infrastructure Setup

```bash
# Option A: Docker (recommended for development)
docker run -d --name furqan-es \
  -p 9200:9200 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
  elasticsearch:8.13.0

# Option B: Add to docker-compose.yml (see below)
```

Add to `docker-compose.yml`:
```yaml
  elasticsearch:
    image: elasticsearch:8.13.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - ES_JAVA_OPTS=-Xms1g -Xmx1g
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data

volumes:
  es_data:
```

Add to `pyproject.toml`:
```toml
dependencies = [
    ...,
    "elasticsearch[async]>=8.0.0",
]
```

### Phase 1: Create Indices with Analyzers

```bash
# Run the index creation script (to be implemented)
python -m al_furqan.kb.es.setup_indices
```

This script will:
1. Create the `arabic_furqan` analyzer (settings above)
2. Create all 6 indices with their mappings
3. Verify the analyzer works with a test document

### Phase 2: Migrate Static Data

```bash
# Bulk-load Quran, Hadith, Graph, Lessons
python -m al_furqan.kb.es.migrate_data
```

Migration order (respects dependencies):
1. `furqan_quran` — load `quran_complete.json` (6,236 docs)
2. `furqan_hadith` — load `hadith_sample.json` (55 docs)
3. `furqan_graph` — load `sample_graph.json` edges (95 docs)
4. `furqan_lessons` — load `lessons_enriched_json/*.json` (~24 docs)

Uses ES `_bulk` API for batch ingestion. Expected time: < 30 seconds.

### Phase 3: Migrate Runtime Data

```bash
# Migrate existing verdicts and feedback
python -m al_furqan.kb.es.migrate_verdicts
```

1. Scan `verdicts/*.json` files → bulk index to `furqan_verdicts`
2. Scan feedback store → bulk index to `furqan_feedback`

### Phase 4: Migrate Vector Embeddings

```bash
# Export from ChromaDB, re-index with dense_vector fields
python -m al_furqan.kb.es.migrate_embeddings
```

1. Export all embeddings from ChromaDB collections
2. Update `furqan_quran` and `furqan_hadith` docs with `embedding` field
3. Update `furqan_verdicts` (approved/corrected only) with `embedding` field

### Phase 5: Update Application Code

Replace the following modules:

| Current module | Replacement | What changes |
|---|---|---|
| `kb/retriever.py` | `kb/es/retriever.py` | JSON scan → ES `match_phrase` |
| `kb/collections/quran.py` | `kb/es/quran.py` | In-memory list → ES index |
| `kb/collections/hadith.py` | `kb/es/hadith.py` | In-memory list → ES index |
| `kb/graph/store.py` | `kb/es/graph.py` | JSON dict → ES term queries |
| `store/verdict_store.py` | `store/es_verdict_store.py` | File I/O → ES index/search |
| `store/feedback_store.py` | `store/es_feedback_store.py` | File I/O → ES index/search |

### Phase 6: Validation

```bash
# Run comparison tests
python -m al_furqan.kb.es.validate_migration
```

For each enriched lesson, run verse matching via both old (Python regex) and
new (ES `match_phrase`) paths. Verify:
- Same verses matched (no false negatives)
- No new false positives
- Response time < 50ms per query (vs. ~500ms+ current)

---

## Query Migration Guide

### Verse Matching (the core replacement)

**Before (Python):**
```python
content_norm = normalize_arabic(content)
content_word_set = set(content_norm.split())
for verse in all_6236_verses:
    verse_norm = normalize_arabic(verse["text_ar"])
    # ... sliding window check ...
```

**After (Elasticsearch):**
```python
# Find all verses whose text appears as a phrase in the lesson content
results = es.search(index="furqan_quran", body={
    "query": {
        "match_phrase": {
            "text_ar": {
                "query": lesson_content,  # raw Arabic, analyzer handles normalization
                "slop": 0                 # exact consecutive match
            }
        }
    },
    "size": 100
})
```

The `arabic_furqan` analyzer normalizes both the indexed text and the query
identically — no Python normalization needed.

### Verse Lookup by Reference

**Before:** `verse_index["by_ref"][(6, 80)]`

**After:**
```python
es.get(index="furqan_quran", id="6:80")
```

### Graph Traversal

**Before:**
```python
edges = [e for e in graph["edges"] if e["source"] == node_id]
```

**After:**
```python
es.search(index="furqan_graph", body={
    "query": {
        "bool": {
            "must": [
                {"term": {"source": node_id}},
                {"term": {"edge_type": "EXPLAINS"}}  # optional filter
            ]
        }
    }
})
```

### Verdict Similarity Search (replaces ChromaDB)

**Before:**
```python
results = chroma_collection.query(
    query_embeddings=[embedding], n_results=5
)
```

**After:**
```python
es.search(index="furqan_verdicts", body={
    "knn": {
        "field": "embedding",
        "query_vector": embedding,
        "k": 5,
        "num_candidates": 50,
        "filter": {"term": {"status": "approved"}}
    }
})
```

### Full-Text Search Across All Indices

**New capability** not possible with the current architecture:

```python
# Search across all Arabic text in the system
es.search(index="furqan_quran,furqan_hadith,furqan_lessons", body={
    "query": {
        "multi_match": {
            "query": "التوحيد والشرك",
            "fields": ["text_ar", "chapters.content"],
            "type": "phrase"
        }
    }
})
```

---

## Infrastructure Requirements

### Development

| Resource | Spec |
|----------|------|
| Elasticsearch | 8.13+ (single node) |
| RAM | 1 GB heap for ES |
| Disk | ~500 MB for indices |
| Docker | Recommended |

### Production

| Resource | Spec |
|----------|------|
| Elasticsearch | 8.13+ (3-node cluster recommended) |
| RAM | 2 GB heap per node |
| Disk | 2 GB SSD |
| Network | Low-latency to API servers |

### Data Volume

#### RAG indices

| Index | Documents | Size |
|-------|-----------|------|
| `furqan_quran` | 6,236 | ~4 MB |
| `furqan_quran_tokens` | 418,516 | ~29 MB |
| `furqan_tafsir` | 165,369 | ~794 MB |
| `furqan_tafsir_structural` | 39,802 | ~218 MB |
| `furqan_hadith` | 55 | <1 MB |
| `furqan_graph` | 95 | <1 MB |
| `furqan_lessons` | 2,434 | ~4 MB |
| `furqan_verdicts` | variable | runtime |
| `furqan_feedback` | variable | runtime |

#### Training index

| Index | Documents | Size |
|-------|-----------|------|
| `furqan_train_tafsir_pairs` | ~188,000 | ~750 MB |
| **Total** | **~820K** | **~1.8 GB** |

---

## Rollback Plan

The migration is non-destructive:

1. **JSON files are not deleted** — they remain on disk as the source of truth
2. **ChromaDB data persists** in `.chroma_db/` directory
3. **Application code** can be switched back by reverting the import paths
4. **Feature flag** approach: `config.yaml` gets a `store.backend: "elasticsearch"` option;
   set to `"file"` to revert to the current JSON-based storage

```yaml
# config.yaml
store:
  backend: "elasticsearch"       # or "file" to use JSON files
  elasticsearch:
    hosts: ["http://localhost:9200"]
    index_prefix: "furqan"
  # File-based (legacy) settings still available
  verdicts_dir: "/tmp/al-furqan/verdicts"
  chroma_dir: "/tmp/al-furqan/.chroma_db"
```

---

## Implementation Timeline

| Phase | Description | Depends on |
|-------|-------------|------------|
| 0 | Infrastructure + ES in docker-compose | — |
| 1 | Create indices + analyzer | Phase 0 |
| 2 | Migrate static data (Quran, Hadith, Graph, Lessons) | Phase 1 |
| 3 | Migrate verdicts + feedback | Phase 1 |
| 4 | Migrate embeddings from ChromaDB | Phase 2, 3 |
| 5 | Update application code (new retriever, stores) | Phase 2 |
| 6 | Validation + comparison tests | Phase 5 |
| 7 | Remove ChromaDB dependency | Phase 6 (after validation) |
