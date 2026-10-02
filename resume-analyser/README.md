# AI Resume & Job Skill Analyser 🧠

A production-quality full-stack application that uses AI/NLP to parse resumes and perform deep skill-gap analysis against job descriptions.

---

## 🏗️ Architecture

```
resume-analyser/
├── backend/                   # FastAPI + Python
│   ├── main.py                # App entry point (logging, metrics, middleware)
│   ├── alembic.ini            # DB migration config
│   ├── alembic/               # Alembic migrations
│   ├── Dockerfile             # Multi-stage image, non-root, healthcheck
│   ├── entrypoint.sh          # Migrations → gunicorn (uvicorn workers)
│   ├── requirements.txt
│   ├── .env.example
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py      # Settings (pydantic-settings, fail-fast SECRET_KEY)
│   │   │   └── metrics.py     # Prometheus collectors
│   │   ├── schemas.py         # All Pydantic models
│   │   ├── api/v1/
│   │   │   ├── router.py
│   │   │   └── endpoints/
│   │   │       ├── resume.py  # Upload & parse (magic-byte validation)
│   │   │       ├── analysis.py# Run & retrieve analysis (paginated history)
│   │   │       └── jobs.py    # Job description parse
│   │   ├── db/
│   │   │   ├── database.py    # Engine, sessions, init/check helpers
│   │   │   ├── models.py      # SQLAlchemy ORM models
│   │   │   └── crud.py        # Persistence layer
│   │   ├── middleware/
│   │   │   └── rate_limit.py  # Redis-backed, proxy-aware, fail-open
│   │   └── services/
│   │       ├── extractor.py   # PDF/DOCX/TXT extraction + content sniffing
│   │       ├── parser.py      # NLP resume parser
│   │       ├── skill_db.py    # 140+ skill knowledge base
│   │       ├── job_parser.py  # JD skill extraction
│   │       ├── analyser.py    # Core AI scoring engine
│   │       └── nlp_engine.py  # spaCy + sentence-transformers, LRU-capped
│   └── tests/                 # 58 tests (pytest)
└── frontend/                  # React 18 + TypeScript + Vite
    ├── Dockerfile             # Vite build → nginx
    ├── nginx.conf             # SPA + API proxy + security headers
    ├── src/
    │   ├── App.tsx            # Route-level code splitting (React.lazy)
    │   ├── components/
    │   │   ├── ErrorBoundary.tsx
    │   │   ├── layout/        # Navbar, Footer, Layout
    │   │   ├── resume/        # Uploader, ParsedResumeView
    │   │   └── analysis/      # ScoreGauge, SkillMatchGrid, charts, ...
    │   ├── pages/             # Home, Analyse, Results, History (paginated)
    │   ├── services/          # API service layer
    │   ├── types/             # TypeScript API types
    │   └── lib/               # Utils, api client
    └── vitest tests           # ErrorBoundary, RouteFallback, HistoryPage
```

---

## 🚀 Quick Start

### Option A — Docker Compose (recommended)

```bash
cd resume-analyser/backend
cp .env.example .env
# REQUIRED: set SECRET_KEY before starting
#   python -c "import secrets; print(secrets.token_hex(32))"

cd ..
docker compose up --build
```

- App: http://localhost (nginx → SPA + API proxy)
- API docs: http://localhost:8000/docs (via `docker compose exec` or expose the port)
- Metrics: http://localhost/metrics (internal networks only)

The `api` container runs `alembic upgrade head` before accepting traffic; Redis backs the shared rate-limit counters.

### Option B — Local development

**Backend**

```bash
cd resume-analyser/backend

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # DEBUG=true works without SECRET_KEY
uvicorn main:app --reload --port 8000
```

**Frontend**

```bash
cd resume-analyser/frontend
npm install
cp .env.example .env
npm run dev
```

App: http://localhost:5173 · API docs: http://localhost:8000/docs

---

## 🧪 Running Tests

```bash
# Backend (62 tests)
cd resume-analyser/backend
pytest tests/ -v

# Frontend (13 tests)
cd resume-analyser/frontend
npm test
```

CI (GitHub Actions) runs the backend matrix on Python 3.11/3.12, frontend lint + tests + build, verifies migrations upgrade/downgrade cleanly, and builds both Docker images.

---

## 🔌 API Reference

| Method | Endpoint                  | Description                                   |
|--------|---------------------------|-----------------------------------------------|
| POST   | `/api/v1/resume/upload`   | Upload resume (PDF/DOCX/TXT)                  |
| GET    | `/api/v1/resume/{id}`     | Retrieve parsed resume                        |
| POST   | `/api/v1/analysis/`       | Run analysis against JD                       |
| GET    | `/api/v1/analysis/{id}`   | Get analysis result                           |
| GET    | `/api/v1/analysis/`       | List analyses — `?limit=20&offset=0&resume_id=` |
| POST   | `/api/v1/jobs/parse`      | Parse a job description                       |
| GET    | `/api/v1/jobs/templates`  | List pre-defined, editable job role templates |
| GET    | `/health`                 | Health check (verifies DB, 503 when down)     |
| GET    | `/metrics`                 | Prometheus metrics                            |

---

## ✨ Features

- **Smart Resume Parsing** — PDF, DOCX, and TXT via PyMuPDF & python-docx (legacy `.doc` is rejected with a clear message — re-save as `.docx`)
- **Content-Sniffed Uploads** — magic-byte validation (renamed executables are rejected before parsing)
- **140+ Skill Knowledge Base** — categorised across 7 domains
- **Multi-Dimensional Scoring** — skill match, experience, education, keyword scores
- **Skill Gap Analysis** — visual breakdown by category (bar + radar charts)
- **Course Recommendations** — curated learning paths for missing skills
- **ATS Tips** — resume optimisation advice
- **Analysis History** — persisted, paginated (limit/offset)
- **Responsive UI** — lazy-loaded routes, error boundary, works on mobile and desktop

---

## 🏭 Production Notes

Already built in:

- **Fail-fast configuration** — the app refuses to start with `DEBUG=false` unless a strong `SECRET_KEY` is set (no silent per-worker random keys)
- **Async-safe request handling** — CPU-heavy parsing/analysis runs on the threadpool; the event loop never blocks
- **Docker & Compose** — multi-stage images, non-root user, healthchecks, gunicorn-managed uvicorn workers, nginx SPA+proxy tier with security headers
- **Alembic migrations** — versioned schema; `create_all` is dev/test only (`AUTO_CREATE_TABLES=false` in prod)
- **Redis rate limiting** — shared counters across workers/replicas, proxy-aware client IPs (`TRUST_PROXY_HEADERS`), fail-open on Redis outage
- **Observability** — structured JSON logs with request-ID correlation, Prometheus `/metrics`, DB-aware `/health`, optional Sentry (`SENTRY_DSN`)
- **Model warm-up** — spaCy + sentence-transformers load at startup, not on first request
- **Bounded memory** — LRU-capped embedding cache

For further scale, plan to swap:

- **SQLite → PostgreSQL** (set `DATABASE_URL`; migrations already work unchanged)
- **nginx container → managed LB/CDN** for TLS termination
- **Next: JWT authentication** — `python-jose`/`passlib` are already in requirements; resumes contain PII, so multi-user deployments should add auth before going public
