"""
Parse a raw job description text / structured request into a ParsedJobDescription.
Uses the skill database for skill extraction.
"""
from __future__ import annotations

import re
from typing import List

from app.schemas import (
    JobDescriptionRequest,
    ParsedJobDescription,
    RequiredSkillItem,
    SkillCategory,
    ExperienceLevel,
)
from app.services.skill_db import SKILL_DB, normalise_skill

_EXP_YEARS_RE = re.compile(r"(\d+)\+?\s*(?:to\s*\d+\s*)?years?", re.I)
_EDU_LEVEL_RE = re.compile(
    r"(bachelor'?s?|master'?s?|phd|doctorate|associate'?s?|b\.?s\.?|m\.?s\.?|m\.?b\.?a\.?)",
    re.I,
)

# Section markers: everything AFTER a required-marker belongs to the required
# section, everything after a preferred-marker to the preferred section, until
# the next marker. Classifying by last-marker-before-match beats proximity
# windows (±N chars), which mis-classify skills in dense lists that happen to
# sit near a "Preferred:" heading.
_SECTION_MARKER_RE = re.compile(
    r"\b(?:(?P<req>required|must\s+have|mandatory|essential)"
    r"|(?P<pref>preferred|nice\s+to\s+have|bonus|plus|desired|advantage))\b",
    re.I,
)

_INDUSTRY_HINTS = {
    "fintech": ["finance", "banking", "payments", "fintech", "trading", "crypto"],
    "healthcare": ["health", "medical", "clinical", "hospital", "pharma"],
    "e-commerce": ["ecommerce", "retail", "marketplace", "shopify"],
    "saas": ["saas", "software as a service", "platform"],
    "gaming": ["game", "gaming", "unity", "unreal"],
    "ai/ml": ["machine learning", "artificial intelligence", "deep learning", "data science"],
}


def parse_job_description(req: JobDescriptionRequest) -> ParsedJobDescription:
    text = req.description
    text_lower = text.lower()

    required_skills, preferred_skills = _extract_job_skills(text_lower)

    # Years experience
    exp_match = _EXP_YEARS_RE.search(text)
    experience_years = float(exp_match.group(1)) if exp_match else _level_to_years(req.experience_level)

    # Education level
    edu_match = _EDU_LEVEL_RE.search(text)
    education_level = edu_match.group(1).lower() if edu_match else None

    # Key responsibilities
    responsibilities = _extract_responsibilities(text)

    # Industry
    industry = _detect_industry(text_lower)

    return ParsedJobDescription(
        title=req.title,
        company=req.company,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        experience_years=experience_years,
        education_level=education_level,
        key_responsibilities=responsibilities,
        industry=industry,
    )


def _extract_job_skills(text_lower: str) -> tuple[list, list]:
    """
    Split job skills into required vs preferred based on the section each
    match falls in. A skill's section is determined by the last section
    marker appearing before its first occurrence; text before any marker is
    treated as required (intro mentions are must-haves in practice).
    """
    required: List[RequiredSkillItem] = []
    preferred: List[RequiredSkillItem] = []
    seen = set()

    # Positions of section markers, in document order
    markers: list[tuple[int, str]] = [
        (m.start(), "preferred" if m.group("pref") else "required")
        for m in _SECTION_MARKER_RE.finditer(text_lower)
    ]

    def section_of(pos: int) -> str:
        kind = "required"
        for marker_pos, marker_kind in markers:
            if marker_pos < pos:
                kind = marker_kind
            else:
                break
        return kind

    for skill_alias, meta in SKILL_DB.items():
        pattern = re.compile(
            r"(?<![a-zA-Z0-9])" + re.escape(skill_alias.lower()) + r"(?![a-zA-Z0-9])"
        )
        match = pattern.search(text_lower)
        if not match:
            continue

        canonical = normalise_skill(skill_alias)
        if canonical.lower() in seen:
            continue
        seen.add(canonical.lower())

        item = RequiredSkillItem(
            name=canonical,
            category=SkillCategory(meta["category"]),
            importance=section_of(match.start()),
        )
        if item.importance == "preferred":
            preferred.append(item)
        else:
            required.append(item)

    return required, preferred


def _extract_responsibilities(text: str) -> List[str]:
    bullets = []
    for line in text.splitlines():
        stripped = line.strip()
        if (stripped.startswith(("•", "-", "*", "–", "·")) or
                (stripped and stripped[0].isupper() and len(stripped) > 20)):
            clean = stripped.lstrip("•-*–· ").strip()
            if 20 < len(clean) < 200:
                bullets.append(clean)
    return bullets[:10] or [text[:200]]


def _level_to_years(level: ExperienceLevel) -> float:
    mapping = {
        ExperienceLevel.INTERN: 0,
        ExperienceLevel.JUNIOR: 1,
        ExperienceLevel.MID: 3,
        ExperienceLevel.SENIOR: 5,
        ExperienceLevel.LEAD: 7,
        ExperienceLevel.PRINCIPAL: 10,
    }
    return float(mapping.get(level, 3))


def _detect_industry(text_lower: str) -> str | None:
    for industry, hints in _INDUSTRY_HINTS.items():
        if any(h in text_lower for h in hints):
            return industry
    return None
