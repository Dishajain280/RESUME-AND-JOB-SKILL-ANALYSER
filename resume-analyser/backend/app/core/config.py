"""Application configuration via environment variables / .env file."""
from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Values that must never be accepted as a real SECRET_KEY in production.
_INSECURE_KEYS = frozenset({
    "",
    "dev-insecure-secret-key-change-me",
    "replace-with-a-64-char-random-hex-string",  # the .env.example placeholder
})


def _explicitly_configured() -> bool:
    """
    True when the operator has shown *explicit* production intent, i.e. set
    DEBUG or SECRET_KEY in the process env or in the backend .env file.

    A bare `uvicorn main:app` on a laptop with no configuration is treated as
    local development (auto DEBUG=true, dev key, loud warning) so the app
    just works out of the box. Docker/compose and CI always set these vars
    explicitly, so production deployments keep the strict fail-fast.
    """
    if "DEBUG" in os.environ or "SECRET_KEY" in os.environ:
        return True
    env_file = Path(".env")
    if env_file.exists():
        try:
            text = env_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return False
        return bool(re.search(r"(?im)^\s*(DEBUG|SECRET_KEY)\s*=", text))
    return False


# Apply dev defaults BEFORE Settings() parses, so both the validator and the
# field values agree on the effective mode.
if not _explicitly_configured():
    os.environ["DEBUG"] = "true"
    os.environ.setdefault("SECRET_KEY", "dev-insecure-secret-key-change-me")
    print(
        "\n[WARNING] No explicit configuration found (no DEBUG/SECRET_KEY in env or .env). "
        "Running in LOCAL DEVELOPMENT mode with an insecure dev key.\n"
        "   For production: set DEBUG=false and SECRET_KEY="
        "(python -c \"import secrets; print(secrets.token_hex(32))\").\n",
        flush=True,
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    APP_NAME: str = "AI Resume & Job Skill Analyser"
    APP_VERSION: str = "1.1.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # ── Security ─────────────────────────────────────────────────────────────
    # SECRET_KEY must be provided explicitly when DEBUG=false. In production a
    # missing key is a hard startup error (fail fast) — never a random per-worker
    # value, which would break token verification across uvicorn/gunicorn workers.
    SECRET_KEY: str = Field(default="dev-insecure-secret-key-change-me")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    @model_validator(mode="after")
    def _validate_secret_key(self) -> "Settings":
        """Fail fast on startup when running with DEBUG=false."""
        if not self.DEBUG:
            if self.SECRET_KEY in _INSECURE_KEYS:
                raise ValueError(
                    "SECRET_KEY must be set in the environment or .env when DEBUG=false. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
                )
            if len(self.SECRET_KEY) < 32:
                raise ValueError(
                    f"SECRET_KEY is too short ({len(self.SECRET_KEY)} chars); "
                    "use at least 32 chars of entropy."
                )
        return self

    # ── Database ─────────────────────────────────────────────────────────────
    # SQLite by default; swap to PostgreSQL URL for production.
    DATABASE_URL: str = "sqlite:///./resume_analyser.db"
    # In DEBUG (dev/tests) create_all is convenient; production must use Alembic.
    AUTO_CREATE_TABLES: bool = True

    # ── CORS / proxy ─────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]
    # Trust X-Forwarded-For / X-Real-IP headers set by the reverse proxy.
    # Only enable when the app is actually behind a trusted proxy (nginx etc.);
    # otherwise clients could spoof their IP and bypass rate limits.
    TRUST_PROXY_HEADERS: bool = False

    # ── File upload ──────────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 10
    # NOTE: legacy .doc (OLE2) is intentionally NOT supported — python-docx
    # cannot read it. Ask users to re-save as .docx or PDF.
    # Image formats are OCR'd with Tesseract (scanned/screenshot resumes).
    ALLOWED_EXTENSIONS: list[str] = [
        ".pdf", ".docx", ".txt", ".rtf", ".odt",
        ".md", ".markdown", ".html", ".htm", ".csv",
        ".jpg", ".jpeg", ".png", ".gif", ".bmp",
        ".tiff", ".tif", ".webp",
    ]
    # Path to the Tesseract binary for OCR (scanned/image-only PDFs).
    # Empty = rely on PATH lookup.
    TESSERACT_CMD: str = ""

    # ── AI / NLP ─────────────────────────────────────────────────────────────
    NLP_MODEL: str = "en_core_web_sm"
    SIMILARITY_THRESHOLD: float = 0.55
    # Load spaCy + sentence-transformers once at startup instead of lazily on
    # the first request (first-request latency spike / model download).
    WARM_UP_MODELS_ON_STARTUP: bool = True

    # ── Rate limiting ────────────────────────────────────────────────────────
    # Redis URL for shared rate-limit counters across workers/replicas.
    # Empty → in-process fallback (single worker only).
    REDIS_URL: str = ""
    RATE_LIMIT_ENABLED: bool = True

    # ── API docs ─────────────────────────────────────────────────────────────
    # Keep interactive docs for developers; disable on public production hosts.
    ENABLE_DOCS: bool = True

    # ── Observability ────────────────────────────────────────────────────────
    # Expose Prometheus metrics at /metrics (prometheus_client installed).
    ENABLE_METRICS: bool = True
    METRICS_EXCLUDE_PATHS: list[str] = ["/metrics", "/health"]
    # Optional Sentry DSN — empty disables Sentry entirely.
    SENTRY_DSN: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
