"""Analysis endpoint (stateless).

There is no server-side storage: the client sends the full parsed
resume inline with the job description, and the result is returned in
the response for the client to keep (browser localStorage). The
endpoint is a pure function of the request — safe on read-only,
ephemeral serverless filesystems (Vercel, Lambda, …).
"""
from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException, status

from app.schemas import (
    AnalyseRequest,
    AnalysisResult,
)
from app.services import analyser

log = structlog.get_logger()
router = APIRouter()


@router.post(
    "/",
    response_model=AnalysisResult,
    status_code=status.HTTP_200_OK,
    summary="Analyse a resume against a job description",
)
def run_analysis(req: AnalyseRequest):
    """
    NOTE: deliberately a sync `def` — FastAPI runs sync endpoints on its
    threadpool, keeping the CPU-heavy analyser OFF the event loop so
    concurrent requests keep being served.

    Stateless: `req.parsed` (the parsed resume from the upload
    response) must be supplied. Without it there is nothing to
    analyse — the backend holds no resumes to look up.
    """
    if req.parsed is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "No parsed resume supplied. Upload the resume first and send "
                "its parsed data alongside the job description."
            ),
        )

    try:
        result = analyser.analyse(req.parsed, req.job, req.resume_id)
    except Exception as exc:
        log.error("analysis_error", resume_id=req.resume_id, error=str(exc))
        raise HTTPException(status_code=500, detail="Analysis failed. Please try again.")

    log.info(
        "analysis_complete",
        analysis_id=result.analysis_id,
        score=result.overall_score,
    )
    return result
