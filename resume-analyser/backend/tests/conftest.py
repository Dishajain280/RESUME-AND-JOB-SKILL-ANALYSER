"""
Pytest bootstrap — runs BEFORE test modules are collected.

Critical ordering guarantee: env vars that Settings() reads at import time
must be set before any `app.*` import. test_analysis.py imports main.app at
module level, so these fixture-less env assignments live here, in conftest.
"""
from __future__ import annotations

import os

# Force DEBUG=true so config validation accepts the placeholder SECRET_KEY
# and the rate limiter / model warm-up skip during tests.
os.environ["DEBUG"] = "true"
os.environ.setdefault("SECRET_KEY", "dev-insecure-secret-key-change-me")
os.environ.setdefault("WARM_UP_MODELS_ON_STARTUP", "false")
os.environ.setdefault("AUTO_CREATE_TABLES", "true")
os.environ.setdefault("ENABLE_METRICS", "true")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("SENTRY_DSN", "")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_resume_analyser.db")
