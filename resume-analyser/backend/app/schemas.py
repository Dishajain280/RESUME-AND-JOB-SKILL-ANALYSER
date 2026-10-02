"""Pydantic schemas (request / response models)."""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────────────────────

class ExperienceLevel(str, Enum):
    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    PRINCIPAL = "principal"


class SkillCategory(str, Enum):
    PROGRAMMING = "Programming Languages"
    FRAMEWORKS = "Frameworks & Libraries"
    DATABASES = "Databases"
    CLOUD = "Cloud & DevOps"
    TOOLS = "Tools & Platforms"
    SOFT = "Soft Skills"
    DOMAIN = "Domain Knowledge"
    OTHER = "Other"


# ── Skill ─────────────────────────────────────────────────────────────────────

class SkillItem(BaseModel):
    name: str
    category: SkillCategory = SkillCategory.OTHER
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    years_experience: Optional[float] = None


# ── Resume ────────────────────────────────────────────────────────────────────

class ResumeSection(BaseModel):
    contact_info: Dict[str, str] = Field(default_factory=dict)
    summary: Optional[str] = None
    skills: List[SkillItem] = Field(default_factory=list)
    experience: List[Dict] = Field(default_factory=list)
    education: List[Dict] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    raw_text: str = ""


class ResumeUploadResponse(BaseModel):
    resume_id: str = Field(default_factory=lambda: str(uuid4()))
    filename: str
    parsed: ResumeSection
    word_count: int
    page_count: int


# ── Job Description ───────────────────────────────────────────────────────────

class JobDescriptionRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    company: Optional[str] = None
    description: str = Field(..., min_length=50, max_length=10000)
    experience_level: ExperienceLevel = ExperienceLevel.MID
    location: Optional[str] = None


class RequiredSkillItem(BaseModel):
    name: str
    category: SkillCategory = SkillCategory.OTHER
    importance: str = "required"   # required | preferred | bonus


class ParsedJobDescription(BaseModel):
    title: str
    company: Optional[str]
    required_skills: List[RequiredSkillItem]
    preferred_skills: List[RequiredSkillItem]
    experience_years: Optional[float]
    education_level: Optional[str]
    key_responsibilities: List[str]
    industry: Optional[str]


class JobRoleTemplate(BaseModel):
    """A pre-defined job role the UI can use to pre-fill the JD form."""
    id: str
    title: str
    category: str
    experience_level: ExperienceLevel
    description: str = Field(..., min_length=50, max_length=10000)


# ── Analysis ──────────────────────────────────────────────────────────────────

class SkillMatch(BaseModel):
    skill: str
    category: SkillCategory
    status: str          # matched | missing | partial
    confidence: float = 1.0
    candidate_proficiency: Optional[float] = None
    importance: str = "required"


class SkillGapCategory(BaseModel):
    category: str
    matched: int
    missing: int
    score: float


class RecommendedCourse(BaseModel):
    title: str
    provider: str
    url: str
    skill_covered: str
    difficulty: str
    duration_hours: Optional[int] = None


class AnalysisResult(BaseModel):
    analysis_id: str = Field(default_factory=lambda: str(uuid4()))
    resume_id: str
    job_title: str
    company: Optional[str]
    overall_score: float = Field(ge=0.0, le=100.0)
    skill_match_score: float = Field(ge=0.0, le=100.0)
    experience_score: float = Field(ge=0.0, le=100.0)
    education_score: float = Field(ge=0.0, le=100.0)
    keyword_score: float = Field(ge=0.0, le=100.0)
    skill_matches: List[SkillMatch]
    gap_by_category: List[SkillGapCategory]
    matched_skills: List[str]
    missing_skills: List[str]
    bonus_skills: List[str]
    recommendations: List[str]
    recommended_courses: List[RecommendedCourse]
    ats_tips: List[str]
    strengths: List[str]
    weaknesses: List[str]


# ── Batch & History ───────────────────────────────────────────────────────────

class AnalyseRequest(BaseModel):
    resume_id: str
    job: JobDescriptionRequest


class AnalysisListItem(BaseModel):
    analysis_id: str
    resume_id: str
    job_title: str
    company: Optional[str]
    overall_score: float
    created_at: str


class AnalysisHistoryResponse(BaseModel):
    """Paginated analysis history.

    total    — count of ALL matching rows (for UI pagination controls)
    limit    — page size actually applied (echoed back)
    offset   — row offset actually applied (echoed back)
    """
    items: List[AnalysisListItem]
    total: int
    limit: int = 20
    offset: int = 0
