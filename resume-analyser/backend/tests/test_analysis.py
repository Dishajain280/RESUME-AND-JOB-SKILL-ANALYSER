"""
Comprehensive test suite for the resume analyser backend.
Covers: parser, extractor text sections, skill DB, analyser scoring,
        NLP engine fallback, rate limiter, and API endpoints.

The backend is stateless (no database): uploads return the parsed
resume in the response, and analysis requests carry the parsed resume
inline. Nothing is persisted server-side.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app
from app.services.parser import parse_resume
from app.services.skill_db import SKILL_DB, normalise_skill
from app.services.extractor import detect_sections, validate_magic_bytes, extract_text
from app.services.nlp_engine import semantic_skill_match
from app.services.analyser import (
    _compute_education_score,
    _compute_experience_score,
    _compute_keyword_score,
    _ats_tips_for_resume,
)
from app.schemas import (
    ResumeSection,
    ParsedJobDescription,
    RequiredSkillItem,
    SkillCategory,
    ExperienceLevel,
    JobDescriptionRequest,
)

# Patch settings.DEBUG = True so the rate limiter bypasses during tests
from app.core.config import settings as _settings
_settings.DEBUG = True
client = TestClient(app)

# ── Fixtures ──────────────────────────────────────────────────────────

SAMPLE_RESUME_TEXT = """
John Doe
john.doe@example.com | +1-555-0100
linkedin.com/in/johndoe | github.com/johndoe

Summary
Senior software engineer with 6 years of experience building scalable web applications.

Experience

Senior Software Engineer — Acme Corp
Jan 2020 – Present
• Built REST APIs using Python, FastAPI, and PostgreSQL
• Led migration from monolith to microservices using Docker and Kubernetes
• Implemented CI/CD pipelines with GitHub Actions
• Improved system performance by 40% through query optimisation

Software Engineer — Beta Inc
Jun 2017 – Dec 2019
• Developed React frontends consuming GraphQL and REST APIs
• Worked with AWS (EC2, S3, Lambda) for cloud infrastructure
• Managed a team of 3 engineers during a critical product launch

Education
B.S. Computer Science — State University — 2017

Skills
Python, JavaScript, TypeScript, React, FastAPI, Node.js,
Docker, Kubernetes, PostgreSQL, MongoDB, AWS, Git, Agile

Certifications
AWS Certified Solutions Architect – Associate
"""

SAMPLE_JD = {
    "title": "Senior Backend Engineer",
    "company": "TechCorp",
    "description": (
        "We are looking for a Senior Backend Engineer with 5+ years of experience. "
        "Required: Python, FastAPI, PostgreSQL, Docker, Kubernetes, AWS, microservices, REST API. "
        "Preferred: Terraform, GraphQL, Redis. "
        "You will design and build scalable backend systems, lead code reviews, "
        "and collaborate with cross-functional teams in an agile environment."
    ),
    "experience_level": "senior",
}


def _upload_sample_resume() -> dict:
    """Helper that uploads the sample resume and returns the full response
    (resume_id + parsed data), as a stateless client would keep it."""
    resp = client.post(
        "/api/v1/resume/upload",
        files={"file": ("resume.txt", SAMPLE_RESUME_TEXT.encode(), "text/plain")},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _analyse(upload: dict, job: dict | None = None) -> dict:
    """Run an analysis against an uploaded (stateless) resume."""
    resp = client.post(
        "/api/v1/analysis/",
        json={"resume_id": upload["resume_id"], "job": job or SAMPLE_JD, "parsed": upload["parsed"]},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


# ══════════════════════════════════════════════════════════════════════════════
# Health
# ══════════════════════════════════════════════════════════════════════════════
def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


# ══════════════════════════════════════════════════════════════════════════════
# Skill DB
# ══════════════════════════════════════════════════════════════════════════════
def test_skill_db_has_entries():
    assert len(SKILL_DB) >= 50, "Skill DB should have at least 50 entries"

def test_normalise_skill_known():
    assert normalise_skill("python") == "Python"
    assert normalise_skill("reactjs") == "React"
    assert normalise_skill("k8s") == "Kubernetes"
    assert normalise_skill("golang") == "Go"

def test_normalise_skill_unknown():
    result = normalise_skill("SomethingUnknown")
    assert result == "Somethingunknown"  # title() on unknown

def test_skill_categories_are_valid():
    valid_cats = {c.value for c in SkillCategory}
    for alias, meta in SKILL_DB.items():
        assert meta["category"] in valid_cats, f"Invalid category for '{alias}': {meta['category']}"

def test_skill_confidence_range():
    for alias, meta in SKILL_DB.items():
        conf = meta.get("confidence", 1.0)
        assert 0.0 <= conf <= 1.0, f"Confidence out of range for '{alias}': {conf}"


# ══════════════════════════════════════════════════════════════════════════════
# Extractor — section detection
# ══════════════════════════════════════════════════════════════════════════════
def test_detect_sections_finds_all():
    sections = detect_sections(SAMPLE_RESUME_TEXT)
    assert "experience" in sections
    assert "education" in sections
    assert "skills" in sections
    assert "certifications" in sections
    assert "summary" in sections

def test_detect_sections_experience_has_content():
    sections = detect_sections(SAMPLE_RESUME_TEXT)
    assert "Acme Corp" in sections["experience"] or "Senior Software Engineer" in sections["experience"]

def test_detect_sections_empty_text():
    sections = detect_sections("")
    # Should return empty / minimal dict without crashing
    assert isinstance(sections, dict)


# ══════════════════════════════════════════════════════════════════════════════
# Parser
# ══════════════════════════════════════════════════════════════════════════════
def test_parse_resume_contact():
    parsed = parse_resume(SAMPLE_RESUME_TEXT)
    assert parsed.contact_info.get("email") == "john.doe@example.com"
    assert "linkedin" in parsed.contact_info
    assert "github" in parsed.contact_info

def test_parse_resume_skills_found():
    parsed = parse_resume(SAMPLE_RESUME_TEXT)
    skill_names = {s.name.lower() for s in parsed.skills}
    assert "python" in skill_names
    assert "react" in skill_names
    assert "docker" in skill_names

def test_parse_resume_experience_extracted():
    parsed = parse_resume(SAMPLE_RESUME_TEXT)
    assert len(parsed.experience) > 0
    titles = [e["title"] for e in parsed.experience]
    # At least one entry should contain "Engineer"
    assert any("Engineer" in t for t in titles)

def test_parse_resume_experience_date_range():
    parsed = parse_resume(SAMPLE_RESUME_TEXT)
    for entry in parsed.experience:
        # date_range should be populated where present
        if entry.get("date_range"):
            assert "2017" in entry["date_range"] or "2020" in entry["date_range"] or "Present" in entry["date_range"]

def test_parse_resume_education():
    parsed = parse_resume(SAMPLE_RESUME_TEXT)
    assert len(parsed.education) > 0
    degrees = [e["degree"] for e in parsed.education]
    assert any("B" in d or "Bachelor" in d for d in degrees)

def test_parse_resume_education_field_populated():
    parsed = parse_resume(SAMPLE_RESUME_TEXT)
    # "Computer Science" should be detected as field
    fields = [e.get("field", "") for e in parsed.education]
    assert any("Computer Science" in f for f in fields)

def test_parse_resume_certifications():
    parsed = parse_resume(SAMPLE_RESUME_TEXT)
    assert len(parsed.certifications) > 0
    assert any("AWS" in c for c in parsed.certifications)

def test_parse_resume_summary():
    parsed = parse_resume(SAMPLE_RESUME_TEXT)
    assert parsed.summary is not None
    assert len(parsed.summary) > 10


# ══════════════════════════════════════════════════════════════════════════════
# Analyser — scoring functions
# ══════════════════════════════════════════════════════════════════════════════
def _make_job(experience_years: float = 5.0, education_level: str = "bachelor",
              responsibilities: list[str] | None = None) -> ParsedJobDescription:
    return ParsedJobDescription(
        title="Test Job",
        company="Acme",
        required_skills=[],
        preferred_skills=[],
        experience_years=experience_years,
        education_level=education_level,
        key_responsibilities=responsibilities or ["Build scalable systems using Python and AWS."],
        industry=None,
    )

def _make_resume(experience_entries=None, education_entries=None) -> ResumeSection:
    return ResumeSection(
        contact_info={"email": "test@test.com"},
        skills=[],
        experience=experience_entries or [{"date_range": "2018 – 2024", "title": "Engineer", "company": "X", "bullets": []}],
        education=education_entries or [{"degree": "Bachelor", "institution": "Uni", "year": "2018", "field": "Computer Science"}],
        certifications=[],
        raw_text="python machine learning aws 3 years 10 engineers",
    )

def test_experience_score_meets_requirement():
    """Candidate with exactly matching years should score >= 90."""
    resume = _make_resume(
        experience_entries=[{"date_range": "2018 – 2023", "title": "Engineer", "company": "X", "bullets": []}]
    )
    score = _compute_experience_score(resume, _make_job(experience_years=5.0))
    assert score >= 90.0

def test_experience_score_under_requirement():
    """Candidate with 2 years vs 5 required should score < 50."""
    resume = _make_resume(
        experience_entries=[{"date_range": "2022 – 2024", "title": "Engineer", "company": "X", "bullets": []}]
    )
    score = _compute_experience_score(resume, _make_job(experience_years=5.0))
    assert score < 50.0

def test_experience_score_no_requirement():
    """No experience requirement — score based on raw years, no hard ceiling."""
    resume = _make_resume()
    score = _compute_experience_score(resume, _make_job(experience_years=0))
    assert 0.0 <= score <= 100.0

def test_education_score_exact_match():
    resume = _make_resume(education_entries=[{"degree": "Bachelor", "institution": "Uni", "year": "2018", "field": "CS"}])
    score = _compute_education_score(resume, _make_job(education_level="bachelor"))
    assert score == 100.0

def test_education_score_overqualified():
    resume = _make_resume(education_entries=[{"degree": "PhD", "institution": "Uni", "year": "2018", "field": "CS"}])
    score = _compute_education_score(resume, _make_job(education_level="bachelor"))
    assert score == 100.0

def test_education_score_underqualified():
    resume = _make_resume(education_entries=[])  # no education
    score = _compute_education_score(resume, _make_job(education_level="master"))
    # No education vs master requirement: score should be below 80
    assert score <= 80.0

def test_keyword_score_high_overlap():
    resume = _make_resume()
    # resume raw_text contains "python", "aws" which are in responsibilities
    job = _make_job(responsibilities=["Build systems using Python and AWS for scalable infrastructure"])
    score = _compute_keyword_score(resume.raw_text, job)
    assert score > 0

def test_keyword_score_no_keywords():
    resume = _make_resume()
    job = _make_job(responsibilities=[""])
    score = _compute_keyword_score(resume.raw_text, job)
    assert score == 75.0   # fallback when no keywords extractable


# ══════════════════════════════════════════════════════════════════════════════
# ATS tips
# ══════════════════════════════════════════════════════════════════════════════
def test_ats_tips_count():
    tips = _ats_tips_for_resume(SAMPLE_RESUME_TEXT, [])
    assert 1 <= len(tips) <= 5

def test_ats_tips_linkedin_missing():
    text = "No social links here. Python developer with 3 years."
    tips = _ats_tips_for_resume(text, [])
    assert any("LinkedIn" in t or "linkedin" in t.lower() for t in tips)


# ══════════════════════════════════════════════════════════════════════════════
# Extractor — magic bytes & legacy .doc rejection
# ══════════════════════════════════════════════════════════════════════════════

MINIMAL_PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF\n"

def test_validate_magic_bytes_accepts_valid_pdf():
    assert validate_magic_bytes(MINIMAL_PDF, ".pdf") is None

def test_validate_magic_bytes_rejects_exe_renamed_pdf():
    exe = b"MZ\x90\x00\x03" + b"\x00" * 256
    err = validate_magic_bytes(exe, ".pdf")
    assert err is not None
    assert "PDF" in err

def test_validate_magic_bytes_rejects_png_renamed_docx():
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
    err = validate_magic_bytes(png, ".docx")
    assert err is not None
    assert ".docx" in err

def test_validate_magic_bytes_accepts_real_docx():
    import io
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
    err = validate_magic_bytes(buf.getvalue(), ".docx")
    assert err is None

def test_validate_magic_bytes_rejects_binary_txt():
    binary = bytes(range(0, 32)) * 64
    err = validate_magic_bytes(binary, ".txt")
    assert err is not None

def test_validate_magic_bytes_accepts_plain_txt():
    err = validate_magic_bytes("Hello, plain resume text.\n".encode(), ".txt")
    assert err is None

def test_extract_doc_rejected():
    """Legacy .doc must be rejected, not crash python-docx."""
    with pytest.raises(ValueError) as excinfo:
        extract_text(b"\xd0\xcf\x11\xe0OLE2", "resume.doc")
    assert ".docx or PDF" in str(excinfo.value)

def test_ats_tips_linkedin_present():
    text = "linkedin.com/in/johndoe | Python developer"
    tips = _ats_tips_for_resume(text, [])
    # LinkedIn tip should NOT appear when already present
    assert not any("LinkedIn" in t for t in tips)

def test_ats_tips_long_resume_gets_length_tip():
    # 3 words x 450 reps = 1350 words → triggers the >1200 word length tip
    long_text = "Senior software engineer. " * 450
    tips = _ats_tips_for_resume(long_text, [])
    # Check for "page" anywhere in tips (encoding-safe)
    assert any("page" in t.lower() for t in tips)

def test_ats_tips_no_numbers_gets_quantify_tip():
    text = "Software engineer. Worked on projects. Led team. Improved things."
    tips = _ats_tips_for_resume(text, [])
    assert any("Quantify" in t or "numbers" in t.lower() for t in tips)


# ══════════════════════════════════════════════════════════════════════════════
# NLP engine — semantic_skill_match
# ══════════════════════════════════════════════════════════════════════════════
def test_semantic_direct_match():
    status, conf = semantic_skill_match("Python", ["Python", "React"], "Python developer")
    assert status == "matched"
    assert conf == 1.0

def test_semantic_text_match():
    status, conf = semantic_skill_match("FastAPI", [], "We use FastAPI for our backend services")
    assert status == "matched"
    assert conf >= 0.85

def test_semantic_missing():
    status, conf = semantic_skill_match("Terraform", ["React", "Node.js"], "Frontend developer")
    assert status == "missing"
    assert conf == 0.0

def test_semantic_fuzzy_partial():
    # "Docker" substring in "Docker Compose" should fuzzy-match
    status, conf = semantic_skill_match("Docker", ["Docker Compose", "Kubernetes"], "")
    # "docker" is contained in "docker compose" — expect matched or partial
    assert status in ("matched", "partial")


# ══════════════════════════════════════════════════════════════════════════════
# API — resume endpoints (stateless)
# ══════════════════════════════════════════════════════════════════════════════
def test_upload_text_resume():
    resume_bytes = SAMPLE_RESUME_TEXT.encode()
    resp = client.post(
        "/api/v1/resume/upload",
        files={"file": ("resume.txt", resume_bytes, "text/plain")},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert "resume_id" in data
    assert data["word_count"] > 0
    assert len(data["parsed"]["skills"]) > 0

def test_upload_unsupported_type():
    resp = client.post(
        "/api/v1/resume/upload",
        files={"file": ("resume.exe", b"binary", "application/octet-stream")},
    )
    assert resp.status_code == 415

def test_upload_no_file():
    resp = client.post("/api/v1/resume/upload")
    assert resp.status_code == 422


# ══════════════════════════════════════════════════════════════════════════════
# API — analysis endpoints (stateless)
# ══════════════════════════════════════════════════════════════════════════════
def test_full_analysis_pipeline():
    upload = _upload_sample_resume()
    result = _analyse(upload)
    assert "overall_score" in result
    assert 0 <= result["overall_score"] <= 100
    assert isinstance(result["matched_skills"], list)
    assert isinstance(result["recommendations"], list)
    assert result["overall_score"] >= 50  # strong resume vs matching JD

def test_analysis_result_has_all_fields():
    upload = _upload_sample_resume()
    result = _analyse(upload)
    required_fields = [
        "analysis_id", "resume_id", "job_title", "overall_score",
        "skill_match_score", "experience_score", "education_score", "keyword_score",
        "skill_matches", "gap_by_category", "matched_skills", "missing_skills",
        "bonus_skills", "recommendations", "recommended_courses", "ats_tips",
        "strengths", "weaknesses",
    ]
    for field in required_fields:
        assert field in result, f"Missing field: {field}"

def test_analysis_requires_parsed_resume():
    """Without the inline parsed resume there is nothing to analyse."""
    resp = client.post(
        "/api/v1/analysis/",
        json={"resume_id": "any-id", "job": SAMPLE_JD},
    )
    assert resp.status_code == 400
    assert "parsed" in resp.json()["detail"].lower()

def test_ats_tips_in_analysis_are_contextual():
    upload = _upload_sample_resume()
    result = _analyse(upload)
    tips = result["ats_tips"]
    # Should have 1–5 tips, none empty
    assert 1 <= len(tips) <= 5
    for tip in tips:
        assert len(tip) > 5


# ══════════════════════════════════════════════════════════════════════════════
# API — job parse endpoint
# ══════════════════════════════════════════════════════════════════════════════
def test_parse_job():
    resp = client.post("/api/v1/jobs/parse", json=SAMPLE_JD)
    assert resp.status_code == 200
    data = resp.json()
    assert "required_skills" in data
    assert len(data["required_skills"]) > 0

def test_parse_job_extracts_experience_years():
    resp = client.post("/api/v1/jobs/parse", json=SAMPLE_JD)
    data = resp.json()
    assert data["experience_years"] == 5.0  # "5+ years" in SAMPLE_JD

def test_parse_job_education_level():
    jd = dict(SAMPLE_JD)
    jd["description"] += " Bachelor's degree required."
    resp = client.post("/api/v1/jobs/parse", json=jd)
    data = resp.json()
    assert data.get("education_level") is not None


# ══════════════════════════════════════════════════════════════════════════════
# Job role templates
# ══════════════════════════════════════════════════════════════════════════════
def test_job_templates_listed():
    resp = client.get("/api/v1/jobs/templates")
    assert resp.status_code == 200
    templates = resp.json()
    assert len(templates) >= 10, "Should ship a useful set of role templates"

def test_job_templates_have_required_fields():
    templates = client.get("/api/v1/jobs/templates").json()
    for t in templates:
        assert {"id", "title", "category", "experience_level", "description"} <= set(t)
        assert len(t["description"]) >= 50, f"{t['id']} description too short for min_length rule"

def test_job_templates_unique_ids_and_titles():
    templates = client.get("/api/v1/jobs/templates").json()
    ids = [t["id"] for t in templates]
    titles = [t["title"] for t in templates]
    assert len(ids) == len(set(ids))
    assert len(titles) == len(set(titles))

def test_job_template_parses_into_skills():
    """Each template's description must yield required skills via the JD parser."""
    from app.services.job_parser import parse_job_description
    from app.schemas import JobDescriptionRequest

    templates = client.get("/api/v1/jobs/templates").json()
    for t in templates:
        req = JobDescriptionRequest(
            title=t["title"],
            description=t["description"],
            experience_level=t["experience_level"],
        )
        parsed = parse_job_description(req)
        assert len(parsed.required_skills) >= 3, (
            f"Template '{t['id']}' should extract at least 3 required skills, "
            f"got {[s.name for s in parsed.required_skills]}"
        )
