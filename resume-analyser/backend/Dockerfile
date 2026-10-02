# ── Stage 1: builder ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Build deps for native wheels (numpy, spacy, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Compile wheels into a prefix we can copy into the slim runtime
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Runtime packages only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy pre-built site-packages
COPY --from=builder /install /usr/local

# Copy application code
COPY --chown=appuser:appuser . /app

# chmod in-image so the exec bit survives Windows checkouts (git may drop it)
RUN chmod +x /app/entrypoint.sh

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Start via gunicorn-managed uvicorn workers; migrations run in the
# entrypoint BEFORE workers accept traffic.
CMD ["./entrypoint.sh"]
