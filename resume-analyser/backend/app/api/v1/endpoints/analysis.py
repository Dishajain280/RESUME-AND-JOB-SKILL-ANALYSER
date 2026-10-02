"""Analysis endpoints: run analysis, get results, list history."""
from __future__ import annotations

from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.schemas import (
    AnalyseRequest,
    AnalysisResult,
    AnalysisHistoryResponse,
)
from app.db.database import get_db
from app.db import crud
from app.services import analyser

log = structlog.get_logger()
router = APIRouter()


@router.post(
    "/",
    response_model=AnalysisResult,
    status_code=status.HTTP_200_OK,
    summary="Analyse a resume against a job description",
)
def run_analysis(req: AnalyseRequest, db: Session = Depends(get_db)):
    """
    NOTE: deliberately a sync `def` — FastAPI runs sync endpoints on its
    threadpool, keeping the CPU-heavy analyser (and the sync DB session)
    OFF the event loop so concurrent requests keep being served.
    """
    record = crud.get_resume(db, req.resume_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Resume with id '{req.resume_id}' not found. Upload it first.",
        )
    _filename, _pages, _words, parsed_resume = record

    try:
        result = analyser.analyse(parsed_resume, req.job, req.resume_id)
    except Exception as exc:
        log.error("analysis_error", resume_id=req.resume_id, error=str(exc))
        raise HTTPException(status_code=500, detail="Analysis failed. Please try again.")

    crud.save_analysis(db, result)
    log.info(
        "analysis_complete",
        analysis_id=result.analysis_id,
        score=result.overall_score,
    )
    return result


@router.get(
    "/{analysis_id}",
    response_model=AnalysisResult,
    summary="Retrieve a past analysis by ID",
)
async def get_analysis(analysis_id: str, db: Session = Depends(get_db)):
    result = crud.get_analysis(db, analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return result


@router.get(
    "/",
    response_model=AnalysisHistoryResponse,
    summary="List analyses (paginated, optionally filtered by resume_id)",
)
def list_analyses(
    resume_id: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100, description="Page size (1-100)"),
    offset: int = Query(default=0, ge=0, description="Row offset for pagination"),
    db: Session = Depends(get_db),
):
    """Newest-first. `total` counts ALL matching rows for pagination controls."""
    items = crud.list_analyses(db, resume_id, limit=limit, offset=offset)
    total = crud.count_analyses(db, resume_id)
    return AnalysisHistoryResponse(items=items, total=total, limit=limit, offset=offset)
