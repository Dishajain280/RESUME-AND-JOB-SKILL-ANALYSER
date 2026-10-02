"""
Rate-limiting middleware with two backends:

- **Redis** (production, multi-worker/multi-replica safe) when REDIS_URL is set.
- **In-process sliding window** (dev / single worker fallback) otherwise.

Both paths are proxy-aware: the client key honours X-Forwarded-For /
X-Real-IP when TRUST_PROXY_HEADERS=true, and falls back to the socket peer
otherwise (headers are ignored so clients can't spoof their IP and bypass
limits when not behind a trusted reverse proxy).

Design notes:
- Redis failures **fail open** (requests pass) — availability beats strict
  limiting; a short circuit-breaker window prevents hammering a down Redis.
- Limits: /api/v1/resume/upload → 5/min, /api/v1/analysis/ → 10/min,
  everything else → 60/min per client+path.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional

import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

log = structlog.get_logger()

# Route-specific limits: (max_requests, window_seconds)
_ROUTE_LIMITS: list[tuple[str, int, int]] = [
    ("/api/v1/resume/upload", 5, 60),
    ("/api/v1/analysis/", 10, 60),
]
_DEFAULT_LIMIT = (60, 60)

# ── Redis backend state ───────────────────────────────────────────────────────
_redis_client = None
_redis_broken_until: float = 0.0  # circuit breaker: skip Redis before this ts
_REDIS_RETRY_SECONDS = 30.0


def _get_redis():
    """Lazily create the shared Redis client. Returns None when unavailable."""
    global _redis_client
    from app.core.config import settings

    if not settings.REDIS_URL:
        return None
    if _redis_client is not None:
        return _redis_client
    try:
        import redis

        _redis_client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=0.5,
            socket_timeout=0.5,
        )
        _redis_client.ping()
        log.info("rate_limit_redis_connected")
    except Exception as exc:
        log.warning("rate_limit_redis_unavailable", error=str(exc))
        _redis_client = None
    return _redis_client


def _get_limit(path: str) -> tuple[int, int]:
    for prefix, max_req, window in _ROUTE_LIMITS:
        if path.startswith(prefix):
            return max_req, window
    return _DEFAULT_LIMIT


def _client_ip(request: Request) -> str:
    """
    Resolve the client IP, honouring proxy headers only when explicitly
    trusted. X-Forwarded-For is "client, proxy1, proxy2" — the first entry
    is the original client.
    """
    from app.core.config import settings

    if settings.TRUST_PROXY_HEADERS:
        xff = request.headers.get("X-Forwarded-For")
        if xff:
            first = xff.split(",")[0].strip()
            if first:
                return first
        real_ip = request.headers.get("X-Real-IP")
        if real_ip and real_ip.strip():
            return real_ip.strip()
    return request.client.host if request.client else "unknown"


# ── In-memory fallback counters ───────────────────────────────────────────────
# { "ip:path": deque of timestamps }
_counters: Dict[str, Deque[float]] = defaultdict(deque)


def _check_memory(key: str, max_req: int, window: int) -> Optional[int]:
    """Sliding-window check. Returns retry_after seconds when limited, else None."""
    now = time.monotonic()
    dq = _counters[key]
    while dq and dq[0] < now - window:
        dq.popleft()
    if len(dq) >= max_req:
        return int(window - (now - dq[0])) + 1
    dq.append(now)
    return None


def _check_redis(client, key: str, max_req: int, window: int) -> Optional[int]:
    """
    Atomic sliding-window counter in Redis (a Lua-scripted sliding window is
    overkill here: INCR + EXPIRE gives fixed windows with at most one boundary
    burst of 2x — acceptable for coarse per-IP limits).
    Returns retry_after seconds when limited, else None.
    """
    import redis.exceptions

    bucket = int(time.time()) // window
    redis_key = f"ratelimit:{key}:{bucket}"
    ttl = window * 2  # keep the bucket briefly past the window edge

    count = client.incr(redis_key)
    if count == 1:
        client.expire(redis_key, ttl)
    if count > max_req:
        # Seconds remaining in the current fixed window
        return (bucket + 1) * window - int(time.time()) + 1
    return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        from app.core.config import settings

        # Skip rate limiting entirely in DEBUG/test mode
        if settings.DEBUG or not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        path = request.url.path
        max_req, window = _get_limit(path)
        client_ip = _client_ip(request)
        key = f"{client_ip}:{path}"

        retry_after: Optional[int] = None
        backend = "memory"

        global _redis_broken_until
        client = _get_redis()
        if client is not None and time.monotonic() >= _redis_broken_until:
            try:
                retry_after = _check_redis(client, key, max_req, window)
                backend = "redis"
            except Exception as exc:
                # Fail open + circuit breaker: stop calling Redis for a while.
                _redis_broken_until = time.monotonic() + _REDIS_RETRY_SECONDS
                log.warning(
                    "rate_limit_redis_error_fail_open", error=str(exc), path=path
                )
                retry_after = None
        elif not client:
            retry_after = _check_memory(key, max_req, window)

        if retry_after is not None:
            log.info("rate_limited", path=path, client=client_ip, backend=backend)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit exceeded. Max {max_req} requests per {window}s. "
                    f"Retry after {retry_after}s."
                },
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
