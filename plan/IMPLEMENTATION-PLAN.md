# 🗺️ Al-Furqan (The Criterion) — Implementation Plan

> **Version:** 1.0  
> **Date:** 2026-03-19  
> **Author:** عارف (Arif AI) — بتوجيه من محمد الأشماوي ومحمود السمان  
> **Status:** Draft  
> **Related:** [PRD v1.0](./PRD-v1.0.pdf) | [Architecture v1.0](./Architecture-v1.0.pdf)

---

## 📍 نقطة البداية (Phase 0 — ✅ Done)

الموجود دلوقتي:
- CLI tool شغال (argparse)
- Reasoning Engine: Scan → Mirror → Verdict → Self-Correct (≤5 passes)
- LLM Layer: Ollama + Transformers (Strategy Pattern)
- Verdict Store: ChromaDB (vectors) + JSON files
- Human Review: approve/correct/reject via CLI
- Repo: `github.com/Ashmaawyy/The-Code-Of-The-Criterion`

---

## 🔵 Phase 1: Foundation (6 أسابيع)

### Sprint 1 (Week 1-2): API Layer + Auth

| Task | Owner | Days | Priority |
|------|-------|------|----------|
| Setup FastAPI project structure + routers | Dev | 2 | Must |
| `POST /api/v1/evaluate` — async evaluation | Dev | 3 | Must |
| `GET /api/v1/evaluate/{id}` — status/result | Dev | 1 | Must |
| `GET /api/v1/verdicts` — list + filters | Dev | 2 | Must |
| `GET /api/v1/verdicts/{id}` — single verdict | Dev | 1 | Must |
| `POST /api/v1/verdicts/{id}/review` — review action | Dev | 2 | Must |
| `GET /api/v1/verdicts/search` — semantic search | Dev | 1 | Must |
| `DELETE /api/v1/verdicts/{id}` — cascade invalidation | Dev | 2 | Must |
| `POST /api/v1/criterion-test` — full test | Dev | 2 | Must |
| `GET /api/v1/stats` + `GET /api/v1/health` | Dev | 1 | Must |
| OpenAPI/Swagger auto-docs | Dev | 0.5 | Must |

**Deliverable:** REST API كامل شغال locally

### Sprint 2 (Week 3-4): Auth + Cloud LLMs + Docker

| Task | Owner | Days | Priority |
|------|-------|------|----------|
| API key authentication middleware | Dev | 2 | Must |
| JWT token generation + validation | Dev | 2 | Must |
| RBAC: reader / reviewer / admin roles | Dev | 2 | Must |
| Rate limiting middleware | Dev | 1 | Must |
| Tenant isolation (API key → separate store) | Dev | 3 | Must |
| OpenAI provider implementation | Dev | 1 | Must |
| Anthropic provider implementation | Dev | 1 | Must |
| Google Gemini provider implementation | Dev | 1 | Should |
| LLM call statistics tracking (US-008) | Dev | 1 | Should |
| `config.yaml` — LLM params + `--init` flag | Dev | 1 | Must |

**Deliverable:** Multi-tenant API with cloud LLM support

### Sprint 3 (Week 5-6): Docker + Benchmarks + CI

| Task | Owner | Days | Priority |
|------|-------|------|----------|
| Dockerfile (API + Worker) | DevOps | 2 | Must |
| `docker-compose.yml` (API + Ollama + ChromaDB + Redis) | DevOps | 2 | Must |
| Celery/background worker for async evaluations | Dev | 3 | Must |
| Benchmark suite: 20+ philosophical frameworks | Dev | 4 | Must |
| Expected results documentation per framework | Dev | 2 | Must |
| Automated regression testing (pytest) | Dev | 2 | Must |
| GitHub Actions CI pipeline | DevOps | 1 | Must |
| CORS middleware configuration | Dev | 0.5 | Must |

**Deliverable:** Docker-ready app + benchmark suite ✅

---

## 🟡 Phase 2: Research Paper (8 أسابيع)

### Sprint 4 (Week 7-9): Paper Foundation

| Task | Owner | Days | Priority |
|------|-------|------|----------|
| Run benchmarks on all 20+ frameworks → collect data | Dev | 5 | Must |
| Consistency tests: same question × 50 runs | Dev | 3 | Must |
| Multi-model comparison (GPT-4, Claude, Gemini, Mistral) | Dev | 3 | Must |
| Draft: Abstract + Introduction + Related Work | محمد | 5 | Must |
| Draft: The Criterion Framework (formal definitions) | محمد | 5 | Must |
| Philosophical citations compilation (Leibniz, Hume, Ibn Sina, etc.) | محمد | 3 | Must |

### Sprint 5 (Week 10-12): Paper Completion

| Task | Owner | Days | Priority |
|------|-------|------|----------|
| Draft: Architecture section | Dev + محمد | 3 | Must |
| Draft: Evaluation + Results (tables, charts) | Dev + محمد | 5 | Must |
| Draft: Case Studies (3-5 ethical dilemmas) | محمد | 4 | Must |
| Draft: Discussion + Limitations | محمد | 3 | Must |
| Inter-annotator agreement study (2+ reviewers) | Team | 5 | Should |
| Internal peer review cycle | Team | 5 | Must |
| Submit to NeurIPS AI Safety Workshop | محمد | 1 | Must |

**Deliverable:** Paper draft submitted + benchmark data published 📄

---

## 🟢 Phase 3: Web Dashboard (8 أسابيع)

### Sprint 6 (Week 13-15): Dashboard Core

| Task | Owner | Days | Priority |
|------|-------|------|----------|
| Next.js project setup + design system | Frontend | 3 | Should |
| Auth pages: login, API key management | Frontend | 3 | Should |
| Verdict list page + filters (status, system, score) | Frontend | 4 | Should |
| Verdict detail page (full reasoning + gate scores) | Frontend | 3 | Should |
| Gate score visualization (radar chart / bar chart) | Frontend | 2 | Should |
| Review actions: Approve ✅ / Correct ✏️ / Reject ❌ | Frontend | 4 | Should |

### Sprint 7 (Week 16-18): Dashboard Advanced

| Task | Owner | Days | Priority |
|------|-------|------|----------|
| Multi-framework comparison view (side-by-side) | Frontend | 4 | Could |
| Analytics dashboard (verdict volume, accuracy trends) | Frontend | 4 | Should |
| Gate-level failure analysis charts | Frontend | 2 | Should |
| Real-time evaluation status (WebSocket/polling) | Dev + FE | 3 | Should |
| Multi-user review support | Dev + FE | 3 | Should |
| Arabic RTL support + Arabic verdict templates | Frontend | 3 | Should |
| Responsive design (mobile-friendly) | Frontend | 2 | Should |

**Deliverable:** Full web dashboard for review + analytics 🖥️

---

## 🟣 Phase 4: Cloud & Scale (6 أسابيع)

### Sprint 8 (Week 19-21): Production Infrastructure

| Task | Owner | Days | Priority |
|------|-------|------|----------|
| Kubernetes manifests (API, Worker, DB, Vector DB) | DevOps | 4 | Must |
| ChromaDB → Qdrant migration | Dev | 3 | Must |
| PostgreSQL setup (metadata, auth, analytics) | Dev | 3 | Must |
| TLS configuration (in-transit encryption) | DevOps | 1 | Must |
| AES-256 at-rest encryption | DevOps | 2 | Must |
| HPA (auto-scaling: CPU > 70%) | DevOps | 1 | Must |
| Prometheus + Grafana monitoring | DevOps | 2 | Must |
| Loki logging integration | DevOps | 1 | Must |

### Sprint 9 (Week 22-24): Enterprise Features

| Task | Owner | Days | Priority |
|------|-------|------|----------|
| LLM Gateway (load balancing, fallback, cost tracking) | Dev | 5 | Must |
| Redis caching (recent verdicts, sessions) | Dev | 2 | Must |
| Webhook notifications on evaluation completion | Dev | 2 | Should |
| Daily automated backups | DevOps | 1 | Must |
| GDPR-compliant cascade deletion | Dev | 2 | Must |
| Audit trail (all actions logged) | Dev | 2 | Must |
| Performance testing: 10+ concurrent evals | QA | 3 | Must |

**Deliverable:** Production-ready cloud deployment ☁️

---

## 🔴 Phase 5: Ecosystem (4 أسابيع)

### Sprint 10 (Week 25-28)

| Task | Owner | Days | Priority |
|------|-------|------|----------|
| Python SDK (`pip install al-furqan`) | Dev | 5 | Should |
| SDK: async support + Pythonic interface | Dev | 3 | Should |
| API documentation site (Docusaurus/MkDocs) | Dev | 3 | Should |
| i18n: Turkish, Urdu, Bahasa, French prompts | Dev | 4 | Could |
| Developer onboarding guide | Dev | 2 | Should |
| Open source: README, CONTRIBUTING.md, LICENSE | Dev | 1 | Must |
| Community setup (Discord/GitHub Discussions) | Team | 1 | Should |

**Deliverable:** SDK + docs + community ready 🌍

---

## ⚖️ Phase 6: Patent Filing (4 أسابيع — parallel مع Phase 5)

| Task | Owner | Days | Priority |
|------|-------|------|----------|
| Prior art comprehensive search | محمد + Legal | 5 | Must |
| Patent draft: Criterion Test methodology | Legal + محمد | 10 | Must |
| Patent draft: Axiom-anchored reasoning pipeline | Legal | 5 | Must |
| Patent draft: Precedent-based AI calibration | Legal | 3 | Must |
| Jurisdiction decision (Egypt / US / both) — Q4 | محمد + Legal | 2 | Must |
| Filing | Legal | 3 | Must |

---

## 📊 Resource Requirements

| Role | Phase 1-2 | Phase 3-4 | Phase 5-6 |
|------|-----------|-----------|-----------|
| **Backend Dev (Python/FastAPI)** | 1 FT | 1 FT | 0.5 FT |
| **Frontend Dev (React/Next.js)** | — | 1 FT | 0.5 FT |
| **DevOps** | 0.5 FT | 1 FT | 0.25 FT |
| **محمد (Research + Domain)** | 0.5 FT | 0.25 FT | 0.25 FT |
| **محمود (Architecture + Review)** | 0.25 FT | 0.25 FT | 0.25 FT |
| **Legal (Patent)** | — | — | 1 FT (Phase 6) |

---

## 🎯 Key Milestones

| When | Milestone | Success Metric |
|------|-----------|---------------|
| **Week 6** | API v1 + Docker + Benchmarks | All 10 endpoints passing, 20+ frameworks benchmarked |
| **Week 14** | Paper submitted | NeurIPS AI Safety Workshop submission |
| **Week 20** | Dashboard live | Reviewers using web UI instead of CLI |
| **Week 24** | Production cloud | 99.5% uptime, <60s evaluation, 10+ concurrent |
| **Week 28** | SDK + Ecosystem | `pip install al-furqan` working, docs site live |
| **Week 32** | Patent filed | Application submitted |
| **Month 12** | 1,000+ approved verdicts | Precedent store growing organically |
| **Month 18** | 10+ paying customers | Professional tier revenue |

---

## ⚠️ Critical Dependencies & Risks

1. **LLM Quality Gate** — لازم نعمل benchmark على models مختلفة بدري (Week 5-6) عشان نعرف minimum viable model
2. **Reviewer Availability** — Phase 1-3 محتاجين reviewers بشكل مستمر عشان الـ verdict store يكبر
3. **Paper Timeline** — NeurIPS deadline لازم يتأكد — لو فاتنا ممكن نستهدف AAAI أو FAccT
4. **Patent vs Open Source Balance** — لازم الـ legal team يحدد إيه open وإيه proprietary قبل ما ننشر

---

## 📐 Tech Stack Summary

| Component | Current (v0) | Target (v1) | Target (v2) |
|-----------|-------------|-------------|-------------|
| Language | Python 3.10+ | Python 3.10+ | Python 3.10+ |
| Framework | CLI (argparse) | FastAPI + CLI | FastAPI + CLI |
| Vector DB | ChromaDB (local) | ChromaDB / Qdrant | Qdrant (cloud) |
| Storage | JSON files | JSON + PostgreSQL | PostgreSQL + JSON backup |
| LLM | Ollama/Transformers | + OpenAI, Anthropic, Google | + LLM Gateway |
| Auth | None | API keys + JWT | + RBAC + tenant isolation |
| Frontend | None | React/Next.js | + Mobile responsive |
| Deployment | Local | Docker + Compose | Kubernetes |
| CI/CD | None | GitHub Actions | GitHub Actions |
| Monitoring | Basic logging | Prometheus + Grafana | + Alertmanager + Loki |
| Verification | None | None | Z3 Theorem Prover |

---

_This is a living document. Last updated: 2026-03-19_
