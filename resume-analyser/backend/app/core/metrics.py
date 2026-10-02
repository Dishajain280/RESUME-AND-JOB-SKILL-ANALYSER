"""
Prometheus metrics — HTTP request counters/histograms and process stats.

Rendered with prometheus_client's WSGI app mounted at /metrics by main.py
(only when settings.ENABLE_METRICS is true). record_metrics() is safe to call
unconditionally: it no-ops when metrics are disabled.

Collectors live on the library's default registry, which also carries the
automatic python GC / process / platform collectors.
"""
from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, make_wsgi_app

from app.core.config import settings

# ── Collectors ────────────────────────────────────────────────────────────────
# Buckets tuned for this service (analysis takes ~0.1–2s CPU; p95 should sit
# inside the 2.5s bucket).
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
DOCS_ACCESS_TOTAL = Counter(
    "docs_access_total",
    "Attempts to access disabled API documentation endpoints",
)
DB_HEALTH_STATUS = Gauge(
    "db_health_status",
    "Database reachability (1 = reachable, 0 = unreachable)",
)
IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Requests currently being served",
    ["method", "endpoint"],
)

_metrics_app = None


def make_metrics_app():
    """Return a WSGI app exposing /metrics (mounted by main.py)."""
    global _metrics_app
    if _metrics_app is None:
        _metrics_app = make_wsgi_app()  # default registry incl. process stats
    return _metrics_app


def record_metrics(method: str, endpoint: str, status: int, duration: float) -> None:
    """Record one HTTP request. Cheap no-op when metrics are disabled."""
    if not settings.ENABLE_METRICS:
        return
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=str(status)).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)


def record_docs_blocked() -> None:
    DOCS_ACCESS_TOTAL.inc()


def set_db_health(reachable: bool) -> None:
    DB_HEALTH_STATUS.set(1 if reachable else 0)
