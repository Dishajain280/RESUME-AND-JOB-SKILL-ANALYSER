"""Database CRUD operations — drop-in replacement for the old in-memory store."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import ResumeRecord, AnalysisRecord
from app.schemas import ResumeSection, AnalysisResult, AnalysisListItem


# ── Resume ────────────────────────────────────────────────────────────────────

def save_resume(
    db: Session,
    resume_id: str,
    filename: str,
    page_count: int,
    word_count: int,
    parsed: ResumeSection,
) -> None:
    record = ResumeRecord.from_parsed(
        resume_id=resume_id,
        filename=filename,
        page_count=page_count,
        word_count=word_count,
        parsed_dict=parsed.model_dump(),
    )
    db.merge(record)   # upsert
    db.commit()


def get_resume(db: Session, resume_id: str) -> Optional[tuple]:
    """Returns (filename, page_count, word_count, ResumeSection) or None."""
    record = db.query(ResumeRecord).filter(ResumeRecord.id == resume_id).first()
    if not record:
        return None
    parsed = ResumeSection.model_validate(record.get_parsed_dict())
    return record.filename, record.page_count, record.word_count, parsed


# ── Analysis ──────────────────────────────────────────────────────────────────

def save_analysis(db: Session, result: AnalysisResult) -> None:
    record = AnalysisRecord.from_result(result.model_dump())
    db.merge(record)
    db.commit()


def get_analysis(db: Session, analysis_id: str) -> Optional[AnalysisResult]:
    record = db.query(AnalysisRecord).filter(AnalysisRecord.id == analysis_id).first()
    if not record:
        return None
    return AnalysisResult.model_validate(record.get_result_dict())


def count_analyses(db: Session, resume_id: Optional[str] = None) -> int:
    """Total number of analyses (optionally scoped to one resume)."""
    query = db.query(AnalysisRecord)
    if resume_id:
        query = query.filter(AnalysisRecord.resume_id == resume_id)
    return query.count()


def list_analyses(
    db: Session,
    resume_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> list[AnalysisListItem]:
    """Paginated, newest-first analysis list."""
    query = db.query(AnalysisRecord)
    if resume_id:
        query = query.filter(AnalysisRecord.resume_id == resume_id)
    records = (
        query.order_by(AnalysisRecord.created_at.desc())
        .offset(max(0, offset))
        .limit(max(1, limit))
        .all()
    )
    return [
        AnalysisListItem(
            analysis_id=r.id,
            resume_id=r.resume_id,
            job_title=r.job_title,
            company=r.company,
            overall_score=r.overall_score,
            created_at=r.created_at.isoformat() if r.created_at else "",
        )
        for r in records
    ]
