# Sprint 2: Authentication, Security & Testing
## Al-Furqan — The Criterion
### Detailed Implementation Plan

---

## 🎯 Sprint Goal
Secure the API, add authentication, implement rate limiting, and achieve meaningful test coverage before adding new features.

## ⏱️ Estimated Duration: 3-4 sessions

---

## Phase 2A: API Key Authentication (Session 1)

### 2A.1: API Key Model & Storage
```python
# New file: src/al_furqan/auth/models.py

@dataclass
class APIKey:
    key_id: str           # Public identifier (e.g., "afk_live_abc123")
    key_hash: str         # bcrypt hash of the actual key
    name: str             # Human-readable name ("Muhammad's key")
    role: str             # "reader" | "evaluator" | "admin"
    created_at: float
    last_used: float
    is_active: bool
    rate_limit: int       # Requests per minute (0 = unlimited)
    allowed_models: list  # Which LLM providers this key can use
```

**Storage:** JSON file at `~/.al-furqan/api_keys.json` (encrypted at rest)
**Key format:** `afk_live_{32_char_random}` (prefixed for easy identification)

### 2A.2: Auth Middleware
```python
# New file: src/al_furqan/auth/middleware.py

class APIKeyMiddleware:
    """FastAPI middleware that validates API keys."""
    
    # Header: X-API-Key: afk_live_xxx
    # Or: Authorization: Bearer afk_live_xxx
    
    # Endpoints that DON'T need auth:
    EXEMPT = ["/", "/docs", "/openapi.json", "/api/v1/health"]
    
    # Role-based access:
    # reader   → GET endpoints only
    # evaluator → GET + POST /evaluate
    # admin    → Everything
```

### 2A.3: CLI Key Management
```bash
# Add to main.py or separate CLI
python -m al_furqan.auth.cli create-key --name "Muhammad" --role evaluator
python -m al_furqan.auth.cli list-keys
python -m al_furqan.auth.cli revoke-key afk_live_xxx
python -m al_furqan.auth.cli rotate-key afk_live_xxx
```

### 2A.4: Config Changes
```yaml
# config.yaml additions
auth:
  enabled: true
  require_api_key: true
  allow_anonymous_health: true
  key_storage: "~/.al-furqan/api_keys.json"
```

**Files to create:**
- `src/al_furqan/auth/__init__.py`
- `src/al_furqan/auth/models.py`
- `src/al_furqan/auth/middleware.py`
- `src/al_furqan/auth/key_manager.py`
- `src/al_furqan/auth/cli.py`

**Files to modify:**
- `src/al_furqan/api/app.py` (add middleware)
- `src/al_furqan/config.py` (add AuthConfig)
- `config.yaml` (add auth section)

**Tests:**
- `tests/test_auth.py`
  - test_valid_key_accepted
  - test_invalid_key_rejected
  - test_missing_key_rejected
  - test_exempt_endpoints_no_auth
  - test_role_reader_cannot_post
  - test_role_evaluator_can_evaluate
  - test_role_admin_full_access
  - test_revoked_key_rejected
  - test_key_creation_and_hashing

---

## Phase 2B: Rate Limiting (Session 1-2)

### 2B.1: Rate Limiter Implementation
```python
# New file: src/al_furqan/auth/rate_limiter.py

class RateLimiter:
    """Token bucket rate limiter with per-key tracking."""
    
    def __init__(self, default_rpm: int = 30):
        self.buckets: dict[str, TokenBucket] = {}
    
    def check(self, key_id: str, limit: int) -> tuple[bool, dict]:
        """Returns (allowed, headers_dict)."""
        # Headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
    
    def cleanup_expired(self):
        """Remove stale buckets periodically."""
```

### 2B.2: Rate Limit Headers
```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 28
X-RateLimit-Reset: 1773944000
Retry-After: 30  (only when limited)
```

### 2B.3: Rate Limit by Endpoint Type
| Endpoint | Default Limit | Notes |
|----------|--------------|-------|
| GET /health | Unlimited | Health checks |
| GET /verdicts | 60/min | Read operations |
| POST /evaluate | 10/min | Expensive (LLM calls) |
| POST /evaluate (dual) | 5/min | Very expensive (2x LLM calls) |

**Files to create:**
- `src/al_furqan/auth/rate_limiter.py`

**Files to modify:**
- `src/al_furqan/auth/middleware.py` (integrate rate limiting)

**Tests:**
- `tests/test_rate_limiter.py`
  - test_under_limit_allowed
  - test_over_limit_rejected_429
  - test_rate_limit_headers_present
  - test_per_key_isolation
  - test_limit_resets_after_window
  - test_evaluate_has_lower_limit

---

## Phase 2C: Request Validation & Security (Session 2)

### 2C.1: Request Body Size Limits
```python
# In middleware or app.py
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure per deployment
)

# Custom middleware for body size
MAX_BODY_SIZE = 64 * 1024  # 64KB
```

### 2C.2: Input Validation Hardening
- Maximum question length enforcement in API layer (not just engine)
- Content-Type validation (reject non-JSON)
- UTF-8 validation for all string inputs
- Prevent excessively nested JSON

### 2C.3: Security Headers
```python
# Response headers
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'none'
Strict-Transport-Security: max-age=31536000  # When TLS enabled
```

### 2C.4: CORS Tightening
```yaml
api:
  cors_origins: ["http://localhost:3000"]  # Default restrictive
  # NOT ["*"] in production
```

**Files to modify:**
- `src/al_furqan/api/app.py` (security headers, body limits)
- `src/al_furqan/api/routers/evaluate.py` (input validation)

**Tests:**
- `tests/test_security.py`
  - test_oversized_body_rejected
  - test_non_json_rejected
  - test_security_headers_present
  - test_cors_restrictive
  - test_long_question_truncated

---

## Phase 2D: API Endpoint Tests (Session 2-3)

### 2D.1: Test Infrastructure
```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    """FastAPI test client with auth disabled for unit tests."""
    ...

@pytest.fixture
def auth_client():
    """FastAPI test client with test API key."""
    ...
```

### 2D.2: Endpoint Tests
```
tests/
├── test_api_health.py        # Health endpoint
├── test_api_evaluate.py       # Evaluate endpoints (mock LLM)
├── test_api_verdicts.py       # Verdict CRUD
├── test_api_stats.py          # Stats endpoint
├── test_api_criterion.py      # Criterion test endpoint
├── test_auth.py               # Authentication
├── test_rate_limiter.py       # Rate limiting
├── test_security.py           # Security headers & validation
└── conftest.py                # Shared fixtures
```

### 2D.3: Coverage Target
- Current: 0% API coverage
- Target: ≥80% API endpoint coverage
- All error paths tested (400, 401, 403, 404, 429, 500)

**Tests to write (minimum):**
- test_health_returns_200
- test_evaluate_valid_question
- test_evaluate_empty_question_400
- test_evaluate_too_long_question
- test_get_verdict_by_id
- test_get_verdict_not_found_404
- test_list_verdicts
- test_stats_returns_counts
- test_criterion_test_endpoint

---

## Phase 2E: Error Handling & Logging (Session 3)

### 2E.1: Structured Error Responses
```json
{
    "error": {
        "code": "RATE_LIMIT_EXCEEDED",
        "message": "Rate limit exceeded. Try again in 30 seconds.",
        "details": {
            "limit": 10,
            "reset_at": "2026-03-20T10:00:00Z"
        }
    }
}
```

### 2E.2: Error Codes
| Code | HTTP | Description |
|------|------|-------------|
| INVALID_API_KEY | 401 | API key missing or invalid |
| INSUFFICIENT_ROLE | 403 | Key doesn't have required role |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |
| INVALID_REQUEST | 400 | Malformed request body |
| QUESTION_TOO_LONG | 400 | Question exceeds max length |
| EVALUATION_FAILED | 500 | LLM or engine error |
| INTERNAL_ERROR | 500 | Unexpected server error |

### 2E.3: Audit Logging
```python
# Log all auth events
logger.info("API_KEY_AUTH", extra={
    "key_id": "afk_live_abc",
    "endpoint": "/api/v1/evaluate",
    "method": "POST",
    "ip": "1.2.3.4",
    "status": "accepted"
})
```

---

## 📋 Definition of Done (Sprint 2)

- [ ] All API endpoints require API key (except health/docs)
- [ ] Role-based access control working (reader/evaluator/admin)
- [ ] Rate limiting active with proper headers
- [ ] Request body size limits enforced
- [ ] Security headers on all responses
- [ ] ≥80% API test coverage
- [ ] Structured error responses with codes
- [ ] Audit logging for auth events
- [ ] CLI tool for key management
- [ ] Documentation updated
- [ ] All existing tests still passing
- [ ] No regressions in evaluation pipeline

---

## 🚫 NOT in Sprint 2 (Deferred)

- JWT tokens (Sprint 4 — when we need user sessions)
- OAuth2 integration (Sprint 4)
- Database migration to PostgreSQL (Sprint 4)
- TLS/HTTPS setup (DevOps task, not app code)
- Knowledge Base integration (Sprint 3)
- New evaluation features (Sprint 3)

---

## 📊 Estimated Effort

| Phase | Effort | Session |
|-------|--------|---------|
| 2A: API Key Auth | ~2 hours | Session 1 |
| 2B: Rate Limiting | ~1 hour | Session 1-2 |
| 2C: Security | ~1 hour | Session 2 |
| 2D: Tests | ~2 hours | Session 2-3 |
| 2E: Error Handling | ~1 hour | Session 3 |
| **Total** | **~7 hours** | **3 sessions** |

---

_Plan created: March 19, 2026_
_Sprint starts: March 20, 2026_
