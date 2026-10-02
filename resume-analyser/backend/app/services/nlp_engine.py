"""
NLP engine — wraps spaCy and sentence-transformers for semantic skill matching.
Falls back gracefully to keyword matching if models are unavailable.

All heavy work is synchronous by design: callers run it on a worker thread
(see endpoints using `run_in_threadpool`), never on the event loop.
"""
from __future__ import annotations

import re
import threading
from typing import List, Optional

import structlog

log = structlog.get_logger()

# ── spaCy ─────────────────────────────────────────────────────────────────────
_nlp = None
_nlp_lock = threading.Lock()


def _get_nlp():
    global _nlp
    if _nlp is not None:
        return _nlp
    with _nlp_lock:
        if _nlp is not None:  # double-checked locking
            return _nlp
        try:
            import spacy

            from app.core.config import settings

            _nlp = spacy.load(settings.NLP_MODEL)
            log.info("spacy_loaded", model=settings.NLP_MODEL)
        except Exception as exc:
            log.warning("spacy_unavailable", error=str(exc))
            _nlp = False  # sentinel: do not retry
        return _nlp


# ── sentence-transformers ─────────────────────────────────────────────────────
_EMBED_CACHE_MAX = 10_000  # cap memory: ~10k skill strings is plenty
_embedder = None
_embedder_lock = threading.Lock()
_embed_cache: dict[str, list | None] = {}
_embed_lock = threading.Lock()


def _get_embedder():
    global _embedder
    if _embedder is not None:
        return _embedder
    with _embedder_lock:
        if _embedder is not None:
            return _embedder
        try:
            from sentence_transformers import SentenceTransformer

            _embedder = SentenceTransformer("all-MiniLM-L6-v2")
            log.info("sentence_transformer_loaded", model="all-MiniLM-L6-v2")
        except Exception as exc:
            log.warning("sentence_transformer_unavailable", error=str(exc))
            _embedder = False
        return _embedder


def _embed(text: str) -> Optional[list]:
    """
    Return a cached embedding vector, or None if embedder is unavailable.
    The cache is LRU-capped so long-running processes don't grow unbounded.
    Thread-safe: two threads embedding the same new string compute it once.
    """
    with _embed_lock:
        if text in _embed_cache:
            return _embed_cache[text]
    embedder = _get_embedder()
    if not embedder:
        return None
    try:
        import numpy as np

        vec = embedder.encode(text, normalize_embeddings=True).tolist()
    except Exception as exc:
        log.warning("embed_error", error=str(exc))
        return None

    with _embed_lock:
        if len(_embed_cache) >= _EMBED_CACHE_MAX:
            # Simple FIFO eviction is fine: skill strings are tiny and the
            # working set (skill DB + common JD phrases) is well under the cap.
            for old_key in list(_embed_cache)[: len(_embed_cache) - _EMBED_CACHE_MAX + 1]:
                _embed_cache.pop(old_key, None)
        _embed_cache[text] = vec
    return vec


def warm_up() -> None:
    """
    Pre-load spaCy + sentence-transformers at startup.

    Called from the app lifespan so the first request doesn't pay a
    multi-second model-load (or runtime model-download) penalty. Exceptions
    are swallowed — the engine degrades to keyword matching.
    """
    log.info("nlp_warmup_started")
    _get_nlp()
    if _get_embedder():
        _embed("warmup probe")  # force one encode pass through the full stack
    log.info("nlp_warmup_finished")


def _cosine(a: list, b: list) -> float:
    import numpy as np

    a_arr, b_arr = np.array(a), np.array(b)
    denom = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    return float(np.dot(a_arr, b_arr) / denom) if denom > 0 else 0.0


# ── Public API ────────────────────────────────────────────────────────────────

def semantic_skill_match(
    required_skill: str,
    resume_skills: list[str],
    resume_text: str,
    threshold: float = 0.60,
) -> tuple[str, float]:
    """
    Return (status, confidence) for a required skill against the resume.

    Status values:
      "matched"  — direct keyword hit or semantic similarity ≥ threshold
      "partial"  — semantic similarity in [threshold*0.7, threshold)
      "missing"  — no match found

    Falls back to substring matching if sentence-transformers is unavailable.
    """
    req_lower = required_skill.lower()
    resume_lower_set = {s.lower() for s in resume_skills}
    resume_text_lower = resume_text.lower()

    # ── 1. Direct keyword match ───────────────────────────────────────────
    if req_lower in resume_lower_set:
        return "matched", 1.0

    # ── 2. Substring match in raw text ───────────────────────────────────
    pattern = re.compile(
        r"(?<![a-zA-Z0-9])" + re.escape(req_lower) + r"(?![a-zA-Z0-9])"
    )
    if pattern.search(resume_text_lower):
        return "matched", 0.90

    # ── 3. Fuzzy substring (skill contains / is contained in required) ───
    for rs in resume_lower_set:
        if len(rs) > 2 and (req_lower in rs or rs in req_lower):
            return "partial", 0.70

    # ── 4. Semantic similarity via sentence-transformers ─────────────────
    req_vec = _embed(required_skill)
    if req_vec is not None:
        best_sim = 0.0
        for rs in resume_skills:
            rs_vec = _embed(rs)
            if rs_vec is None:
                continue
            sim = _cosine(req_vec, rs_vec)
            if sim > best_sim:
                best_sim = sim

        if best_sim >= threshold:
            return "matched", round(best_sim, 3)
        elif best_sim >= threshold * 0.7:
            return "partial", round(best_sim, 3)

    # ── 5. spaCy token similarity (fallback) ────────────────────────────
    nlp = _get_nlp()
    if nlp:
        try:
            req_doc = nlp(required_skill)
            for rs in resume_skills:
                rs_doc = nlp(rs)
                if req_doc.has_vector and rs_doc.has_vector:
                    sim = req_doc.similarity(rs_doc)
                    if sim >= threshold:
                        return "matched", round(sim, 3)
                    elif sim >= threshold * 0.7:
                        return "partial", round(sim, 3)
        except Exception as exc:
            log.warning("spacy_similarity_error", error=str(exc))

    return "missing", 0.0


def extract_entities_from_text(text: str) -> List[str]:
    """
    Use spaCy NER to extract organisation names, products, and proper-noun
    tokens that may be skill references not in SKILL_DB.
    Returns a list of lowercase candidate skill strings.
    """
    nlp = _get_nlp()
    if not nlp:
        return []
    try:
        doc = nlp(text[:50_000])  # cap to avoid OOM on huge inputs
        entities = [
            ent.text.lower()
            for ent in doc.ents
            if ent.label_ in ("ORG", "PRODUCT", "GPE", "WORK_OF_ART")
        ]
        # Also grab noun chunks that look like technology names
        noun_chunks = [
            chunk.text.lower()
            for chunk in doc.noun_chunks
            if 2 < len(chunk.text) < 30
        ]
        return list(set(entities + noun_chunks))
    except Exception as exc:
        log.warning("ner_extraction_error", error=str(exc))
        return []
