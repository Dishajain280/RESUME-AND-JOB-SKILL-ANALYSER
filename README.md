# AI Resume & Job Skill Analyser 🧠

A production-quality full-stack application that uses AI/NLP to parse resumes and perform deep skill-gap analysis against job descriptions.

---

## 🏗️ Architecture

```
resume-analyser/
├── backend/                   # FastAPI + Python
│   ├── main.py                # App entry point (logging, metrics, middleware)
│   ├── .env.example           # Environment variable template
│   ├── Dockerfile             # Multi-stage image, non-root, healthcheck
│   ├── entrypoint.sh          # Migrations → gunicorn (uvicorn workers)
│   ├── pyproject.toml         # uv dependency management (source of truth)
│   ├── requirements.txt       # pip mirror of pyproject.toml (for local pip)
│   ├── uv.lock                # Locked dependency graph
│   ├── .env                   # Local dev environment (git-ignored)
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py      # Settings (pydantic-settings, fail-fast SECRET_KEY)
│   │   │   └── metrics.py     # Prometheus collectors
│   │   ├── api/v1/
│   │   │   ├── router.py
│   │   │   └── endpoints/
│   │   │       ├── resume.py  # Upload & parse (magic-byte validation)
│   │   │       ├── analysis.py# Run & retrieve analysis (paginated history)
│   │   │       └── jobs.py    # Job description parse
│   │   ├── middleware/
│   │   │   └── rate_limit.py  # Redis-backed, proxy-aware, fail-open
│   │   ├── schemas.py         # All Pydantic models
│   │   └── services/
│   │       ├── analyser.py    # Core AI scoring engine
│   │       ├── extractor.py   # PDF/DOCX/TXT extraction + content sniffing
│   │       ├── job_parser.py  # JD skill extraction
│   │       ├── job_templates.py# Pre-defined job role templates
│   │       ├── nlp_engine.py  # spaCy + sentence-transformers, LRU-capped
│   │       ├── parser.py      # NLP resume parser
│   │       └── skill_db.py    # 140+ skill knowledge base
│   └── tests/                 # 55 tests (pytest)
└── frontend/                  # React 18 + TypeScript + Vite
    ├── Dockerfile             # Vite build → nginx
    ├── nginx.conf             # SPA + API proxy + security headers
    ├── package.json
    ├── package-lock.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── index.html
    └── src/
        ├── App.tsx            # Route-level code splitting (React.lazy)
        ├── components/
        │   ├── ErrorBoundary.tsx
        │   ├── layout/        # Navbar, Footer, Layout
        │   ├── resume/        # ResumeUploader, ParsedResumeView
        │   └── analysis/      # ScoreGauge, SkillMatchGrid, charts, ...
        ├── pages/             # Home, Analyse, Results, History (paginated)
        ├── services/          # API service layer (stateless)
        ├── types/             # TypeScript API types
        └── lib/               # Utils, api client, persistence (localStorage)
```

---

## 🚀 Quick Start

### Option A — Docker Compose (recommended)

```bash
cd resume-analyser
docker compose up --build
```

- App: http://localhost (nginx → SPA + API proxy)
- API docs: http://localhost:8000/docs
- Metrics: http://localhost/metrics (internal networks only)

### Option B — Local development

**Backend**

```bash
cd resume-analyser/backend

# Install dependencies (uv, the Python package manager)
uv sync --frozen

# Copy the .env template (uses defaults for local dev)
cp .env.example .env

# Run the server
uv run uvicorn main:app --reload --port 8000
```

**Frontend**

```bash
cd resume-analyser/frontend
npm ci
npm run dev
```

App: http://localhost:5173 · API docs: http://localhost:8000/docs

> **Note:** The app is **stateless by design** — there is no database. All persistence is
> client-side (browser `localStorage`). Two deployment options are shipped:
>
> 1. **Local development (Compose)** — a Redis-backed, database-backed multiline is used for
>    rate-limit counters and history. Run `docker compose up` as above.
> 2. **Serverless / Vercel** — the backend runs as a Vercel Function with no persistent
>    storage. Uploads return the parsed resume inline; analysis results are kept in
>    `localStorage` so a page refresh does not lose your job.

---

## 🧪 Running Tests

### Backend (55 tests)

```bash
cd resume-analyser/backend
uv run python -m pytest tests/ -v
```

### Frontend (13 tests)

```bash
cd resume-analyser/frontend
npm test
```

### Full CI suite

```bash
# Backend (Py3.11 + Py3.12 matrix)
cd resume-analyser/backend
uv run python -m pytest tests/ -q

# Frontend
cd resume-analyser/frontend
npm run lint
npm test
npm run build
```

---

## 🔌 API Reference

| Method | Endpoint                  | Description                                   |
|--------|---------------------------|-----------------------------------------------|
| POST   | `/api/v1/resume/upload`   | Upload resume (PDF/DOCX/TXT)                  |
| GET    | `/api/v1/resume/{id}`     | Retrieve parsed resume *(removed in stateless)* |
| POST   | `/api/v1/analysis/`       | Run analysis against JD                       |
| GET    | `/api/v1/analysis/{id}`   | Get analysis result *(removed in stateless)*  |
| GET    | `/api/v1/analysis/`       | List analyses — `?limit=20&offset=0&resume_id=` *(removed in stateless)* |
| POST   | `/api/v1/jobs/parse`      | Parse a job description                       |
| GET    | `/api/v1/jobs/templates`  | List pre-defined, editable job role templates |
| GET    | `/health`                 | Health check (verifies config, no DB)         |
| GET    | `/metrics`                | Prometheus metrics                            |

### Stateless design

Upload and analysis are pure functions of the request. The parsed resume returned by
`POST /api/v1/resume/upload` is echoed back by the client, so the backend never persists
anything server-side.

---

## ✨ Features

- **Smart Resume Parsing** — PDF, DOCX, and TXT via PyMuPDF & python-docx (legacy `.doc` is
  rejected with a clear message — re-save as `.docx`)
- **Content-Sniffed Uploads** — magic-byte validation (renamed executables are rejected before
  parsing)
- **140+ Skill Knowledge Base** — categorised across 7 domains (Programming, Frameworks,
  Databases, Cloud, Tools, Soft, Domain)
- **Multi-Dimensional Scoring** — skill match, experience, education, keyword scores
- **Skill Gap Analysis** — visual breakdown by category (bar + radar charts)
- **Course Recommendations** — curated learning paths for missing skills
- **ATS Tips** — resume optimisation advice
- **Analysis History** — persisted, paginated (limit/offset), newest-first
- **Responsive UI** — lazy-loaded routes, error boundary, works on mobile and desktop
- **Async-safe request handling** — CPU-heavy parsing/analysis runs on the threadpool

---

## 🏭 Production Notes

### Vercel deployment (serverless, stateless)

This app is designed to run on Vercel's Functions (Flavours). Key points:

1. **No database** — there is no `DATABASE_URL`, no `SQLAlchemy`, and no `alembic`. The
   `app/db/` package was fully removed.
2. **Stateless REST** — `POST /api/v1/resume/upload` returns the parsed resume; the client
   sends it back on `POST /api/v1/analysis/`.
3. **Environment variables** — the app expects `DEBUG=false` (or `DEBUG=true`) plus a strong
   `SECRET_KEY` (32+ chars). `config.py` tolerates stale `DATABASE_URL` vars left in Vercel
   project settings via `extra="ignore"`.
4. **Model warm-up** — spaCy (`en_core_web_sm`) and sentence-transformers load at startup
   (disabled if `WARM_UP_MODELS_ON_STARTUP=false`).
5. **Rate limiting** — `RateLimitMiddleware` uses Redis when `REDIS_URL` is set, otherwise
   falls back to in-process counters.
6. **Observability** — structured JSON logs, Prometheus `/metrics`, optional Sentry
   (`SENTRY_DSN`).

### Local development (with compose)

`docker compose up --build` starts a Redis-backed multiline (for rate-limit counters and
analysis history), an `api` container running `gunicorn main:app -k uvicorn.workers.UvicornWorker`,
and an `nginx` SPA + API proxy. The `api` container runs `alembic upgrade head` before
accepting traffic.

---

## 🔒 Security

- `SECRET_KEY` must be set and at least 32 characters long. Whitelisted insecure keys are
  rejected at startup, and `DEBUG=false` with an insecure key will refuse to start.
- `MAX_UPLOAD_SIZE_MB` defaults to 10 MB (Vercel's function body limit is 4.5 MB, set it to 4).
- `TRUST_PROXY_HEADERS` should be enabled only when behind a trusted reverse proxy (nginx,
  Vercel), otherwise clients can spoof their IP and bypass rate limits.
- `ALLOWED_EXTENSIONS` restricts uploads; magic-byte checks add a second layer.

---

## 📖 Project Structure (backend)

- `main.py` — FastAPI app, lifespan, middleware, Prometheus, global error handler.
- `app/core/config.py` — Settings via `pydantic-settings`, dev-mode defaults, fail-fast SECRET_KEY.
- `app/api/v1/endpoints/resume.py` — Stateless upload endpoint with magic-byte validation.
- `app/api/v1/endpoints/analysis.py` — Stateless analysis endpoint (requires `parsed`).
- `app/api/v1/endpoints/jobs.py` — JD parse + job templates.
- `app/services/nlp_engine.py` — Lazy spaCy load with graceful fallback; LRU embedding cache.
- `app/services/extractor.py` — PDF/DOCX/TXT/HTML/RTF/ODT/Image extraction + content sniffing.
- `app/services/parser.py` — Regex resume parser (contact, skills, experience, education, certs).
- `app/services/analyser.py` — AI scoring engine (skill, experience, education, keyword).
- `app/services/skill_db.py` — 140+ skill knowledge base (confidence + category).
- `app/services/job_parser.py` — JD → structured skills (required/preferred, experience, education).
- `app/services/job_templates.py` — Pre-defined job role templates.
- `app/middleware/rate_limit.py` — Redis-backed sliding window, fail-open circuit breaker.
- `app/schemas.py` — Pydantic request/response models.
- `tests/test_analysis.py` — 55 tests (stateless; no DB).

---

## 🤝 Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feat/my-feature`.
3. Commit your changes: `git commit -am 'Add my feature'`.
4. Push to the branch: `git push origin feat/my-feature`.
5. Open a Pull Request.

---

## 📄 License

MIT © 2026 Dishajain280.
