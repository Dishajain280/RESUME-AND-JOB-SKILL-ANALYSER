"""Resume upload endpoint (stateless).

There is no server-side storage: the parsed resume is returned in the
upload response and the client keeps it (browser localStorage). The
analysis endpoint accepts the parsed resume inline, so the backend is
a pure function of each request — safe on read-only, ephemeral
serverless filesystems (Vercel, Lambda, …).
"""
from __future__ import annotations

import uuid
from pathlib import Path

import structlog
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from app.core.config import settings
from app.schemas import ResumeUploadResponse
from app.services.extractor import extract_text, validate_magic_bytes
from app.services.parser import parse_resume

log = structlog.get_logger()
router = APIRouter()

MAX_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED = set(settings.ALLOWED_EXTENSIONS)


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a resume (PDF / DOCX / TXT / RTF / ODT / HTML / images)",
)
async def upload_resume(
    file: UploadFile | None = File(default=None),
    files: list[UploadFile] = File(default_factory=list),
):
    """
    Supports both `file` and `files` form keys for compatibility with browsers,
    older clients, and any proxy/SDK that sends a pluralized field name.
    """
    chosen_file = file or (files[0] if files else None)
    if chosen_file is None:
        raise HTTPException(
            status_code=422,
            detail="No resume file was uploaded. Please choose a document or image file.",
        )

    # ── Validate file type ─────────────────────────────────────────────────
    ext = Path(chosen_file.filename or "").suffix.lower()
    if ext not in ALLOWED:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED)}",
        )

    # ── Stream + enforce size limit without buffering full file first ──────
    # UploadFile exposes read(size) — we read in 64 KB chunks to avoid
    # loading a huge file into memory before the size check fires.
    CHUNK_SIZE = 64 * 1024  # 64 KB
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await chosen_file.read(CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit.",
            )
        chunks.append(chunk)
    file_bytes = b"".join(chunks)

    # ── Validate magic bytes (content sniffing) ───────────────────────────
    # The extension check alone is spoofable (virus.exe → virus.pdf).
    # Verify the actual file signature before spending CPU on parsing.
    sniff_error = validate_magic_bytes(file_bytes, ext)
    if sniff_error:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=sniff_error)

    # ── Extract text ───────────────────────────────────────────────────────
    # CPU-heavy (PyMuPDF/docx parsing) → threadpool, not the event loop.
    try:
        raw_text, page_count = await run_in_threadpool(
            extract_text, file_bytes, chosen_file.filename
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        log.error("extraction_failed", filename=chosen_file.filename, error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to extract text from file.")

    # ── Parse ──────────────────────────────────────────────────────────────
    parsed = await run_in_threadpool(parse_resume, raw_text)
    word_count = len(raw_text.split())
    resume_id = str(uuid.uuid4())

    log.info(
        "resume_uploaded",
        resume_id=resume_id,
        filename=chosen_file.filename,
        skills=len(parsed.skills),
    )

    # The full parsed resume is returned to the client — nothing is
    # stored server-side.
    return ResumeUploadResponse(
        resume_id=resume_id,
        filename=chosen_file.filename,
        parsed=parsed,
        word_count=word_count,
        page_count=page_count,
    )
