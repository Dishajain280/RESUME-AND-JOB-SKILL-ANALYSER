"""
AI Resume & Job Skill Analyser — FastAPI Backend
Main application entry point
"""
from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager

import structlog
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1.router import api_router
from app.middleware.rate_limit import RateLimitMiddleware

# ── Structured logging ────────────────────────────────────────────────────────
# JSON logs in production, pretty console in development. merge_contextvars
# enables per-request fields (e.g. request_id) set via structlog.contextvars.
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.EventRenamer("message"),
        (
            structlog.dev.ConsoleRenderer(colors=True)
            if settings.DEBUG
            else structlog.processors.JSONRenderer()
        ),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO and above
    cache_logger_on_first_use=True,
)

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-load NLP models so the first request doesn't pay a multi-second
    # (or model-download) penalty. No-op when disabled in tests.
    if settings.WARM_UP_MODELS_ON_STARTUP:
        from app.services.nlp_engine import warm_up

        warm_up()

    log.info(
        "startup",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        docs_enabled=settings.ENABLE_DOCS,
        metrics_enabled=settings.ENABLE_METRICS,
        redis_configured=bool(settings.REDIS_URL),
    )
    yield
    log.info("shutdown")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered resume parser and job skill gap analyser",
    docs_url="/docs" if settings.ENABLE_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_DOCS else None,
    openapi_url="/openapi.json" if settings.ENABLE_DOCS else None,
    lifespan=lifespan,
)

# ── Sentry (optional — no-op unless SENTRY_DSN is set) ───────────────────────
if settings.SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            send_default_pii=False,
            environment="production" if not settings.DEBUG else "development",
            integrations=[FastApiIntegration(), StarletteIntegration()],
        )
        log.info("sentry_initialised")
    except Exception as exc:  # pragma: no cover - defensive
        log.warning("sentry_init_failed", error=str(exc))

# ── Middleware ────────────────────────────────────────────────────────────────
# add_middleware prepends, so the LAST call is the OUTERMOST layer. Desired
# execution order (outermost → innermost): timing → CORS → gzip → rate limit.
app.add_middleware(RateLimitMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    """Request-ID correlation, Prometheus metrics, and process-time header."""
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    structlog.contextvars.bind_contextvars(request_id=request_id)

    start = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.4f}s"
        return response
    finally:
        duration = time.perf_counter() - start
        # Use the matched route path as the metric label to avoid unbounded
        # cardinality from raw URLs (IDs in paths). Unmatched → "unmatched".
        route = request.scope.get("route")
        path_label = getattr(route, "path", "unmatched")
        record_metrics(request.method, path_label, status_code, duration)
        structlog.contextvars.unbind_contextvars("request_id")


# ── Prometheus metrics ────────────────────────────────────────────────────────
if settings.ENABLE_METRICS:
    from app.core.metrics import make_metrics_app, record_metrics

    app.mount("/metrics", make_metrics_app())
else:  # metrics helper is a no-op when disabled
    from app.core.metrics import record_metrics  # noqa: F401


# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["health"], summary="Health check")
async def health_check():
    """Liveness probe. The app is stateless (no database), so healthy
    means the process is up and serving."""
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("unhandled_exception", path=request.url.path, error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        # reload=True is for development only — use `uvicorn main:app --reload` in dev
        reload=settings.DEBUG,
        log_level="info",
    )
