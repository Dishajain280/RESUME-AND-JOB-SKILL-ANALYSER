"""
Core AI analyser: compares a parsed resume against a job description.
Returns a rich AnalysisResult with scores, gaps, and recommendations.
"""
from __future__ import annotations

import math
import re
from datetime import datetime
from typing import Dict, List, Tuple

import structlog

from app.schemas import (
    AnalysisResult,
    ParsedJobDescription,
    ResumeSection,
    RequiredSkillItem,
    SkillCategory,
    SkillGapCategory,
    SkillItem,
    SkillMatch,
    RecommendedCourse,
)
from app.services.job_parser import parse_job_description
from app.services.nlp_engine import semantic_skill_match
from app.schemas import JobDescriptionRequest

log = structlog.get_logger()


# ── Course recommendation database ───────────────────────────────────────────
COURSE_DB: List[Dict] = [
    {"skill": "Python", "title": "Python for Everybody", "provider": "Coursera", "url": "https://coursera.org/specializations/python", "difficulty": "Beginner", "hours": 40},
    {"skill": "Machine Learning", "title": "Machine Learning Specialization", "provider": "Coursera", "url": "https://coursera.org/specializations/machine-learning-introduction", "difficulty": "Intermediate", "hours": 90},
    {"skill": "React", "title": "React - The Complete Guide", "provider": "Udemy", "url": "https://udemy.com/course/react-the-complete-guide", "difficulty": "Intermediate", "hours": 48},
    {"skill": "AWS", "title": "AWS Certified Solutions Architect", "provider": "AWS Training", "url": "https://aws.amazon.com/training", "difficulty": "Intermediate", "hours": 60},
    {"skill": "Docker", "title": "Docker & Kubernetes: The Practical Guide", "provider": "Udemy", "url": "https://udemy.com/course/docker-kubernetes", "difficulty": "Intermediate", "hours": 24},
    {"skill": "Kubernetes", "title": "Kubernetes for the Absolute Beginners", "provider": "KodeKloud", "url": "https://kodekloud.com/courses/kubernetes-for-the-absolute-beginners", "difficulty": "Beginner", "hours": 15},
    {"skill": "TypeScript", "title": "Understanding TypeScript", "provider": "Udemy", "url": "https://udemy.com/course/understanding-typescript", "difficulty": "Intermediate", "hours": 22},
    {"skill": "System Design", "title": "Grokking System Design Interview", "provider": "Educative", "url": "https://educative.io/courses/grokking-modern-system-design", "difficulty": "Advanced", "hours": 30},
    {"skill": "Deep Learning", "title": "Deep Learning Specialization", "provider": "Coursera", "url": "https://coursera.org/specializations/deep-learning", "difficulty": "Advanced", "hours": 120},
    {"skill": "Terraform", "title": "HashiCorp Terraform Associate", "provider": "HashiCorp", "url": "https://developer.hashicorp.com/terraform/tutorials", "difficulty": "Intermediate", "hours": 20},
    {"skill": "NLP", "title": "Natural Language Processing Specialization", "provider": "Coursera", "url": "https://coursera.org/specializations/natural-language-processing", "difficulty": "Advanced", "hours": 100},
    {"skill": "GraphQL", "title": "GraphQL with React", "provider": "Udemy", "url": "https://udemy.com/course/graphql-with-react-course", "difficulty": "Intermediate", "hours": 14},
    {"skill": "PostgreSQL", "title": "The Complete SQL Bootcamp", "provider": "Udemy", "url": "https://udemy.com/course/the-complete-sql-bootcamp", "difficulty": "Beginner", "hours": 18},
    {"skill": "Microservices", "title": "Microservices with Node JS and React", "provider": "Udemy", "url": "https://udemy.com/course/microservices-with-node-js-and-react", "difficulty": "Advanced", "hours": 55},
    {"skill": "DevOps", "title": "DevOps Bootcamp: Terraform, Docker, CI/CD", "provider": "Udemy", "url": "https://udemy.com/course/devops-bootcamp", "difficulty": "Intermediate", "hours": 40},
]

# ── ATS tips ───────────────────────────────────────────────────────────────────
_ATS_TIPS = [
    "Use a clean, single-column layout for better ATS parsing.",
    "Include exact keywords from the job description in your resume.",
    "Avoid tables, headers/footers, and text in images — ATS cannot read them.",
    "Use standard section headings: Experience, Education, Skills, Certifications.",
    "Quantify achievements with numbers: 'Increased performance by 30%', 'managed 5-person team'.",
    "Spell out acronyms at least once (e.g., 'Natural Language Processing (NLP)').",
    "Save your resume as a PDF (unless the job explicitly requests .docx).",
    "Put your most relevant skills near the top of the Skills section.",
    "Mirror the exact job title from the posting in your headline if accurate.",
    "Keep the resume to 1–2 pages; remove outdated or irrelevant roles.",
]


def analyse(resume: ResumeSection, job_req: JobDescriptionRequest, resume_id: str) -> AnalysisResult:
    """Run the full analysis pipeline and return an AnalysisResult."""
    parsed_job = parse_job_description(job_req)

    # Build lookup sets
    resume_skill_names = {s.name.lower() for s in resume.skills}
    resume_raw = resume.raw_text.lower()

    # ── Skill matching ─────────────────────────────────────────────────────
    skill_matches, matched, missing, bonus = _match_skills(
        resume_skill_names, resume_raw, parsed_job
    )

    # ── Sub-scores ─────────────────────────────────────────────────────────
    skill_match_score = _compute_skill_score(skill_matches, parsed_job)
    experience_score = _compute_experience_score(resume, parsed_job)
    education_score = _compute_education_score(resume, parsed_job)
    keyword_score = _compute_keyword_score(resume_raw, parsed_job)

    # ── Overall weighted score ─────────────────────────────────────────────
    overall = (
        skill_match_score * 0.45
        + experience_score * 0.25
        + education_score * 0.15
        + keyword_score * 0.15
    )

    # ── Gap breakdown by category ──────────────────────────────────────────
    gap_by_category = _compute_gap_by_category(skill_matches)

    # ── Recommendations ────────────────────────────────────────────────────
    recommendations = _build_recommendations(
        overall, skill_match_score, missing, bonus, resume, parsed_job
    )

    # ── Course recommendations ─────────────────────────────────────────────
    courses = _recommend_courses(missing[:8])

    # ── ATS tips (top 5 most relevant) ────────────────────────────────────
    ats_tips = _ats_tips_for_resume(resume_raw, _ATS_TIPS)

    # ── Strengths & weaknesses ─────────────────────────────────────────────
    strengths = _compute_strengths(overall, skill_match_score, experience_score, bonus, resume)
    weaknesses = _compute_weaknesses(overall, skill_match_score, missing, resume)

    return AnalysisResult(
        resume_id=resume_id,
        job_title=parsed_job.title,
        company=parsed_job.company,
        overall_score=round(overall, 1),
        skill_match_score=round(skill_match_score, 1),
        experience_score=round(experience_score, 1),
        education_score=round(education_score, 1),
        keyword_score=round(keyword_score, 1),
        skill_matches=skill_matches,
        gap_by_category=gap_by_category,
        matched_skills=matched,
        missing_skills=missing,
        bonus_skills=bonus,
        recommendations=recommendations,
        recommended_courses=courses,
        ats_tips=ats_tips,
        strengths=strengths,
        weaknesses=weaknesses,
    )


# ── Skill matching logic ──────────────────────────────────────────────────────

def _match_skills(
    resume_skills: set,
    resume_raw: str,
    parsed_job: ParsedJobDescription,
) -> Tuple[List[SkillMatch], List[str], List[str], List[str]]:
    """
    Match required/preferred skills against the resume using semantic NLP.
    Falls back to keyword matching transparently if models aren't loaded.
    """
    matches: List[SkillMatch] = []
    matched_names: List[str] = []
    missing_names: List[str] = []

    # Pass resume skills as a list for semantic comparison
    resume_skill_list = list(resume_skills)
    all_required = parsed_job.required_skills + parsed_job.preferred_skills

    for req in all_required:
        status, conf = semantic_skill_match(
            required_skill=req.name,
            resume_skills=resume_skill_list,
            resume_text=resume_raw,
        )

        if status in ("matched", "partial"):
            matched_names.append(req.name)
        else:
            missing_names.append(req.name)

        matches.append(
            SkillMatch(
                skill=req.name,
                category=req.category,
                status=status,
                confidence=conf,
                importance=req.importance,
            )
        )

    # Bonus skills: resume skills NOT in the job description
    job_skill_lower = {r.name.lower() for r in all_required}
    bonus = [
        s.title() for s in resume_skills
        if s not in job_skill_lower and len(s) > 2
    ][:10]

    return matches, matched_names, missing_names, bonus


def _compute_skill_score(matches: List[SkillMatch], parsed_job: ParsedJobDescription) -> float:
    if not matches:
        return 0.0
    required_count = len(parsed_job.required_skills)
    preferred_count = len(parsed_job.preferred_skills)

    req_matched = sum(
        1 for m in matches
        if m.importance == "required" and m.status in ("matched", "partial")
    )
    pref_matched = sum(
        1 for m in matches
        if m.importance == "preferred" and m.status in ("matched", "partial")
    )

    req_score = (req_matched / required_count * 100) if required_count else 100.0
    pref_score = (pref_matched / preferred_count * 100) if preferred_count else 100.0

    return req_score * 0.7 + pref_score * 0.3


def _compute_experience_score(resume: ResumeSection, parsed_job: ParsedJobDescription) -> float:
    required_years = parsed_job.experience_years or 0
    candidate_years = _estimate_years_experience(resume)

    if required_years == 0:
        # No explicit requirement — score on raw experience (max 100 at 10+ years)
        return min(100.0, 50.0 + candidate_years * 5)

    ratio = candidate_years / required_years
    if ratio >= 1.5:
        return 100.0   # clearly overqualified — full marks
    elif ratio >= 1.0:
        return 90.0 + (ratio - 1.0) * 20   # 90–100 band for meeting requirement
    else:
        return max(10.0, ratio * 90.0)     # scales 0→90 as years approach requirement


def _estimate_years_experience(resume: ResumeSection) -> float:
    """Rough estimate from number of job entries × assumed tenure."""
    entries = resume.experience
    if not entries:
        return 0.0
    # Count date ranges
    total_years = 0.0
    for entry in entries:
        dr = entry.get("date_range", "")
        years = re.findall(r"\d{4}", dr)
        if len(years) >= 2:
            y1, y2 = int(years[0]), int(years[-1])
            if y2 == datetime.now().year or "present" in dr.lower() or "current" in dr.lower():
                y2 = datetime.now().year
            total_years += max(0, y2 - y1)
        elif years:
            total_years += 1.0
    return total_years or len(entries) * 1.5


def _compute_education_score(resume: ResumeSection, parsed_job: ParsedJobDescription) -> float:
    req_level = (parsed_job.education_level or "").lower()
    edu_text = " ".join(
        e.get("degree", "") + " " + e.get("field", "") for e in resume.education
    ).lower()

    degree_hierarchy = ["phd", "doctor", "master", "bachelor", "associate", "diploma", "high school"]
    req_idx = next((i for i, d in enumerate(degree_hierarchy) if d in req_level), 3)
    cand_idx = next((i for i, d in enumerate(degree_hierarchy) if d in edu_text), 9)

    if cand_idx <= req_idx:
        return 100.0
    elif cand_idx <= req_idx + 1:
        return 75.0
    elif resume.education:
        return 60.0
    else:
        return 40.0


def _compute_keyword_score(resume_raw: str, parsed_job: ParsedJobDescription) -> float:
    responsibilities = " ".join(parsed_job.key_responsibilities).lower()
    keywords = set(re.findall(r"\b[a-z][a-z\+\#\.]{2,}\b", responsibilities))
    stopwords = {"the", "and", "for", "with", "that", "this", "have", "from",
                 "will", "are", "you", "able", "work", "team", "our", "their"}
    keywords -= stopwords

    if not keywords:
        return 75.0

    hits = sum(1 for kw in keywords if kw in resume_raw)
    return min(100.0, hits / len(keywords) * 100)


def _compute_gap_by_category(matches: List[SkillMatch]) -> List[SkillGapCategory]:
    cats: Dict[str, Dict] = {}
    for m in matches:
        cat = m.category.value if hasattr(m.category, "value") else str(m.category)
        if cat not in cats:
            cats[cat] = {"matched": 0, "missing": 0}
        if m.status in ("matched", "partial"):
            cats[cat]["matched"] += 1
        else:
            cats[cat]["missing"] += 1

    result = []
    for cat, counts in cats.items():
        total = counts["matched"] + counts["missing"]
        score = counts["matched"] / total * 100 if total else 0
        result.append(
            SkillGapCategory(
                category=cat,
                matched=counts["matched"],
                missing=counts["missing"],
                score=round(score, 1),
            )
        )
    return sorted(result, key=lambda x: x.score, reverse=True)


def _build_recommendations(
    overall: float,
    skill_score: float,
    missing: List[str],
    bonus: List[str],
    resume: ResumeSection,
    parsed_job: ParsedJobDescription,
) -> List[str]:
    recs = []
    if missing:
        top_missing = ", ".join(missing[:4])
        recs.append(f"Acquire or highlight these missing skills: {top_missing}.")
    if skill_score < 60:
        recs.append("Your skill match is below 60%. Focus on the top required skills before applying.")
    if not resume.experience:
        recs.append("Add work experience entries with dates, titles, and impact-driven bullet points.")
    if not resume.certifications:
        recs.append("Add relevant certifications to strengthen your credibility.")
    if not resume.contact_info.get("linkedin"):
        recs.append("Include your LinkedIn profile URL to increase visibility.")
    if overall >= 80:
        recs.append("Strong match! Customise your cover letter to highlight your key achievements.")
    elif overall >= 60:
        recs.append("Good foundation. Address 2-3 skill gaps before submitting your application.")
    else:
        recs.append("Consider upskilling for 2–4 weeks before applying. Use the course recommendations below.")
    if bonus:
        recs.append(f"Highlight your extra skills ({', '.join(bonus[:3])}) — they differentiate you.")
    if parsed_job.experience_years and _estimate_years_experience(resume) < parsed_job.experience_years:
        recs.append(
            f"The role requires ~{parsed_job.experience_years} years experience. "
            "Emphasise quality over quantity of your projects."
        )
    return recs[:8]


def _recommend_courses(missing_skills: List[str]) -> List[RecommendedCourse]:
    courses = []
    missing_lower = [s.lower() for s in missing_skills]
    for entry in COURSE_DB:
        if any(entry["skill"].lower() in ml or ml in entry["skill"].lower() for ml in missing_lower):
            courses.append(
                RecommendedCourse(
                    title=entry["title"],
                    provider=entry["provider"],
                    url=entry["url"],
                    skill_covered=entry["skill"],
                    difficulty=entry["difficulty"],
                    duration_hours=entry.get("hours"),
                )
            )
        if len(courses) >= 5:
            break
    return courses


def _ats_tips_for_resume(resume_raw: str, tips: List[str]) -> List[str]:
    """
    Select the most relevant ATS tips based on actual resume content.
    Each tip is added only when the resume shows a signal that it applies.
    """
    selected: List[str] = []

    # Tip: use clean layout — always relevant, always first
    selected.append("Use a clean, single-column layout for better ATS parsing.")

    # Tip: avoid tables/images — only if resume looks like it uses them
    if any(marker in resume_raw for marker in ["<table", "|---", "┌", "│"]):
        selected.append("Avoid tables, headers/footers, and text in images — ATS cannot read them.")
    else:
        selected.append("Use standard section headings: Experience, Education, Skills, Certifications.")

    # Tip: quantify achievements — if no numbers found in experience bullets
    number_pattern = re.compile(r"\d+[\%x]|\d+\s*(years?|months?|team|engineers?|users?|ms|k\b|\$)", re.I)
    if not number_pattern.search(resume_raw):
        selected.append("Quantify achievements with numbers: 'Increased performance by 30%', 'managed 5-person team'.")

    # Tip: spell out acronyms — if resume uses common acronyms without definitions
    acronyms = re.findall(r"\b[A-Z]{2,5}\b", resume_raw)
    if len(set(acronyms)) > 3:
        selected.append("Spell out acronyms at least once (e.g., 'Natural Language Processing (NLP)').")

    # Tip: LinkedIn — if LinkedIn URL not found
    if "linkedin" not in resume_raw.lower():
        selected.append("Include your LinkedIn profile URL to increase visibility.")

    # Tip: PDF format reminder
    selected.append("Save your resume as a PDF (unless the job explicitly requests .docx).")

    # Tip: keywords — always relevant
    selected.append("Include exact keywords from the job description in your resume.")

    # Tip: mirror job title — always useful
    selected.append("Mirror the exact job title from the posting in your headline if accurate.")

    # Tip: resume length — insert early so it isn't squeezed out by the cap
    word_count = len(resume_raw.split())
    if word_count > 1200:
        selected.insert(1, "Keep the resume to 1-2 pages; remove outdated or irrelevant roles.")

    # Deduplicate and cap at 5 most relevant
    seen: set = set()
    unique: List[str] = []
    for tip in selected:
        if tip not in seen:
            seen.add(tip)
            unique.append(tip)
        if len(unique) == 5:
            break
    return unique


def _compute_strengths(
    overall: float,
    skill_score: float,
    exp_score: float,
    bonus: List[str],
    resume: ResumeSection,
) -> List[str]:
    s = []
    if skill_score >= 75:
        s.append("Strong technical skill alignment with the job requirements.")
    if exp_score >= 75:
        s.append("Relevant work experience level matches or exceeds expectations.")
    if resume.certifications:
        s.append(f"Holds {len(resume.certifications)} professional certification(s).")
    if bonus:
        s.append(f"Brings additional value with {len(bonus)} bonus skills beyond job requirements.")
    if resume.education:
        s.append("Has formal educational qualifications.")
    if not s:
        s.append("Resume is parseable and structured — a solid starting point.")
    return s[:5]


def _compute_weaknesses(
    overall: float,
    skill_score: float,
    missing: List[str],
    resume: ResumeSection,
) -> List[str]:
    w = []
    if missing:
        w.append(f"Missing {len(missing)} required/preferred skill(s): {', '.join(missing[:3])}.")
    if skill_score < 60:
        w.append("Skill match score is below 60% — significant gap with job requirements.")
    if not resume.experience:
        w.append("No work experience section detected.")
    if not resume.summary:
        w.append("No professional summary — add one to pass ATS keyword filters.")
    if overall < 50:
        w.append("Overall fit is low. Substantial upskilling recommended before applying.")
    return w[:5]
