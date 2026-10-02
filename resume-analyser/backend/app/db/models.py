"""
SQLAlchemy ORM models — persists resumes and analysis results to SQLite/PostgreSQL.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ResumeRecord(Base):
    __tablename__ = "resumes"

    id = Column(String, primary_key=True, index=True)          # UUID string
    filename = Column(String, nullable=False)
    page_count = Column(Integer, default=1)
    word_count = Column(Integer, default=0)
    # Store the full parsed ResumeSection as JSON
    parsed_json = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    analyses = relationship("AnalysisRecord", back_populates="resume", cascade="all, delete-orphan")

    # ── Helpers ──────────────────────────────────────────────────────────────
    def get_parsed_dict(self) -> dict:
        return json.loads(self.parsed_json)

    @classmethod
    def from_parsed(cls, resume_id: str, filename: str, page_count: int,
                    word_count: int, parsed_dict: dict) -> "ResumeRecord":
        return cls(
            id=resume_id,
            filename=filename,
            page_count=page_count,
            word_count=word_count,
            parsed_json=json.dumps(parsed_dict),
        )


class AnalysisRecord(Base):
    __tablename__ = "analyses"

    id = Column(String, primary_key=True, index=True)          # UUID string (analysis_id)
    resume_id = Column(String, ForeignKey("resumes.id"), nullable=False, index=True)
    job_title = Column(String, nullable=False)
    company = Column(String, nullable=True)
    overall_score = Column(Float, nullable=False)
    # Store the full AnalysisResult as JSON
    result_json = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    resume = relationship("ResumeRecord", back_populates="analyses")

    # ── Helpers ──────────────────────────────────────────────────────────────
    def get_result_dict(self) -> dict:
        return json.loads(self.result_json)

    @classmethod
    def from_result(cls, result_dict: dict) -> "AnalysisRecord":
        return cls(
            id=result_dict["analysis_id"],
            resume_id=result_dict["resume_id"],
            job_title=result_dict["job_title"],
            company=result_dict.get("company"),
            overall_score=result_dict["overall_score"],
            result_json=json.dumps(result_dict),
        )
