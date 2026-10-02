"""
NLP-based resume parser.
Extracts: contact info, skills, experience, education, certifications.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

import structlog

from app.services.extractor import detect_sections
from app.services.skill_db import SKILL_DB, normalise_skill
from app.schemas import ResumeSection, SkillItem, SkillCategory

log = structlog.get_logger()

# ── Contact info patterns ─────────────────────────────────────────────────────
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(
    r"(\+?\d[\d\s\-().]{7,}\d)"
)
_LINKEDIN_RE = re.compile(r"linkedin\.com/in/[\w\-]+", re.I)
_GITHUB_RE = re.compile(r"github\.com/[\w\-]+", re.I)
_URL_RE = re.compile(r"https?://[^\s]+")

# ── Date patterns ─────────────────────────────────────────────────────────────
_DATE_RE = re.compile(
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}"
    r"|\d{1,2}/\d{4}"
    r"|\d{4}",
    re.I,
)
_YEAR_RANGE_RE = re.compile(
    # Bug #7 fix: explicitly include hyphen-minus (-) alongside en/em-dash
    r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*)?"
    r"(\d{4})\s*[-\u2013\u2014]\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*)?(\d{4}|[Pp]resent|[Cc]urrent)",
    re.I,
)

# ── Education keywords ────────────────────────────────────────────────────────
_DEGREE_PATTERNS = re.compile(
    r"(Ph\.?D|Doctor|M\.?S\.?|M\.?Sc|M\.?Eng|M\.?B\.?A|B\.?S\.?|B\.?Sc|B\.?E|B\.?Tech|"
    r"Bachelor|Master|Associate|Diploma|High\s+School|GED)",
    re.I,
)

# ── Certification keywords ────────────────────────────────────────────────────
_CERT_LINES_RE = re.compile(
    r"(AWS|Azure|GCP|Google|Cisco|CompTIA|Oracle|PMI|PMP|Scrum|CKA|CKAD|"
    r"Certified|Certificate|Certification|ISTQB|TOGAF|ITIL|Six\s+Sigma|"
    r"Professional|Associate|Expert)",
    re.I,
)


def parse_resume(raw_text: str) -> ResumeSection:
    """Parse raw resume text into structured ResumeSection."""
    sections = detect_sections(raw_text)

    contact = _extract_contact(raw_text)
    skills = _extract_skills(sections.get("skills", "") + "\n" + raw_text)
    experience = _extract_experience(sections.get("experience", ""))
    education = _extract_education(sections.get("education", ""))
    certs = _extract_certifications(sections.get("certifications", "") + "\n" + raw_text)
    summary = sections.get("summary", "")

    return ResumeSection(
        contact_info=contact,
        summary=summary[:800] if summary else None,
        skills=skills,
        experience=experience,
        education=education,
        certifications=certs,
        raw_text=raw_text,
    )


# ── Contact extraction ────────────────────────────────────────────────────────

_SECTION_HEADING_RE = re.compile(
    r"\b(profile|summary|objective|experience|education|skills|"
    r"certifications|work|hobbies|strengths|references|about|contact)\b",
    re.I,
)

# A name: 2–4 consecutive Capitalized words, e.g. "Disha Pirodiya".
_NAME_RE = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b")


def _extract_contact(text: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    email = _EMAIL_RE.search(text)
    if email:
        result["email"] = email.group()
    phone = _PHONE_RE.search(text)
    if phone:
        result["phone"] = phone.group().strip()
    linkedin = _LINKEDIN_RE.search(text)
    if linkedin:
        result["linkedin"] = "https://" + linkedin.group()
    github = _GITHUB_RE.search(text)
    if github:
        result["github"] = "https://" + github.group()
    # Guess name: scan the document header (above the first section
    # heading) for a line that looks like a name. Searching *within*
    # the line tolerates OCR noise like "J, Disha Pirodiya", and the
    # header-only scope keeps skills-list lines such as
    # "Web Application" from being mistaken for the candidate's name.
    for line in text.splitlines():
        stripped = line.strip()
        # Stop at the first section heading — below it is body content.
        if len(stripped) < 60 and _SECTION_HEADING_RE.search(stripped):
            break
        # Skip contact-info lines (email, phone, urls)
        if _EMAIL_RE.search(stripped) or _URL_RE.search(stripped) or _PHONE_RE.search(stripped):
            continue
        m = _NAME_RE.search(stripped)
        if m and 2 < len(m.group(1)) < 50:
            result["name"] = m.group(1)
            break
    return result


# ── Skills extraction ─────────────────────────────────────────────────────────

def _extract_skills(text: str) -> List[SkillItem]:
    found: Dict[str, SkillItem] = {}
    text_lower = text.lower()

    for skill_name, meta in SKILL_DB.items():
        # Match whole word / phrase
        pattern = re.compile(
            r"(?<![a-zA-Z0-9])" + re.escape(skill_name.lower()) + r"(?![a-zA-Z0-9])"
        )
        if pattern.search(text_lower):
            canonical = normalise_skill(skill_name)
            if canonical not in found:
                found[canonical] = SkillItem(
                    name=canonical,
                    category=SkillCategory(meta["category"]),
                    confidence=meta.get("confidence", 1.0),
                )

    return list(found.values())


# ── Experience extraction ─────────────────────────────────────────────────────

# Separators between job title and company on the SAME line:  "Title - Company" or "Title | Company" or "Title @ Company"
_TITLE_COMPANY_SEP = re.compile(r"\s+[-|@]\s+|\s+at\s+", re.I)


def _extract_experience(text: str) -> List[Dict[str, Any]]:
    if not text.strip():
        return []

    entries = []
    blocks = re.split(r"\n{2,}", text.strip())

    for block in blocks[:10]:
        if len(block.strip()) < 20:
            continue
        lines = [l.strip() for l in block.splitlines() if l.strip()]

        # ── Step 1: find date range (scan all lines) ──────────────────────────
        date_range = None
        date_line_idx = -1
        for idx, line in enumerate(lines):
            m = _YEAR_RANGE_RE.search(line)
            if m:
                date_range = m.group()
                date_line_idx = idx
                break

        # ── Step 2: strip the date portion from the line it was found on ─────
        # so "Senior Engineer - Acme Corp   Jan 2020 - Present" → "Senior Engineer - Acme Corp"
        clean_lines: List[str] = []
        for idx, line in enumerate(lines):
            if idx == date_line_idx:
                cleaned = _YEAR_RANGE_RE.sub("", line).strip().rstrip(",-|").strip()
                if cleaned:
                    clean_lines.append(cleaned)
            else:
                clean_lines.append(line)

        # ── Step 3: skip lines that are purely a date (nothing else) ─────────
        non_date_lines = [l for l in clean_lines if l and not _YEAR_RANGE_RE.fullmatch(l)]

        # ── Step 4: title / company resolution ────────────────────────────────
        title_guess = ""
        company_guess = ""
        if non_date_lines:
            first = non_date_lines[0]
            # Check if title and company are on the same line separated by - | @ at
            sep_match = _TITLE_COMPANY_SEP.search(first)
            if sep_match:
                title_guess   = first[:sep_match.start()].strip()
                company_guess = first[sep_match.end():].strip()
            else:
                title_guess = first
                # Company is the next non-bullet, non-date line
                for l in non_date_lines[1:]:
                    if not l.startswith(("•", "-", "*", "\u2013", "·")) and not l[0].islower():
                        company_guess = l
                        break

        # ── Step 5: collect bullet points ─────────────────────────────────────
        bullets = [
            l for l in lines
            if l.startswith(("•", "-", "*", "\u2013", "·"))
            or (len(l) > 10 and l[0].islower())
        ]

        entries.append(
            {
                "title": title_guess[:120],
                "company": company_guess[:120],
                "date_range": date_range or "",
                "bullets": bullets[:10],
            }
        )
    return entries


# ── Education extraction ──────────────────────────────────────────────────────

# Field of study patterns (e.g. "Computer Science", "Electrical Engineering")
_FIELD_PATTERNS = re.compile(
    r"(Computer\s+Science|Software\s+Engineering|Electrical\s+Engineering|"
    r"Mechanical\s+Engineering|Civil\s+Engineering|Information\s+Technology|"
    r"Data\s+Science|Artificial\s+Intelligence|Mathematics|Physics|"
    r"Business\s+Administration|Economics|Finance|Accounting|"
    r"Information\s+Systems|Cybersecurity|Networking|Biotechnology|"
    r"Chemistry|Statistics|Psychology|Communications|Marketing)",
    re.I,
)


# Institution name separators: "B.S. CS - State University - 2017" or "Degree | University"
_EDU_SEP = re.compile(r"\s*[-|,]\s*")

def _extract_education(text: str) -> List[Dict[str, Any]]:
    if not text.strip():
        return []

    entries = []
    # Education sections often have single-line entries: try splitting on newlines too
    blocks = re.split(r"\n{2,}", text.strip())
    # If no blank-line blocks, treat each line as its own block
    if len(blocks) == 1:
        blocks = [b for b in text.strip().splitlines() if b.strip()]

    for block in blocks[:5]:
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if not lines:
            continue
        first_line = lines[0]

        degree_match = _DEGREE_PATTERNS.search(block)
        year_match   = _DATE_RE.search(block)
        field_match  = _FIELD_PATTERNS.search(block)

        # Bug #5 fix: when degree + institution are on ONE line (most common case),
        # split that line on separators and extract institution from the parts.
        institution = ""
        if degree_match:
            # Remove degree token and year token from first_line; what remains is institution
            stripped = first_line
            stripped = re.sub(_DEGREE_PATTERNS.pattern, "", stripped, flags=re.I)
            stripped = re.sub(_FIELD_PATTERNS.pattern,  "", stripped, flags=re.I)
            stripped = re.sub(r"\d{4}", "", stripped)
            parts = [p.strip().strip("-|,") for p in _EDU_SEP.split(stripped) if p.strip().strip("-|,")]
            # Take the longest remaining part as institution name
            parts = [p for p in parts if len(p) > 2]
            if parts:
                institution = max(parts, key=len)[:120]

        # Fall back to second line if inline extraction yielded nothing
        if not institution:
            for line in lines[1:]:
                if not _DEGREE_PATTERNS.search(line) and not _DATE_RE.search(line):
                    institution = line[:120]
                    break

        entries.append(
            {
                "degree": degree_match.group() if degree_match else first_line[:80],
                "institution": institution,
                "year": year_match.group() if year_match else "",
                "field": field_match.group().title() if field_match else "",
            }
        )
    return entries


# ── Certifications extraction ─────────────────────────────────────────────────

def _extract_certifications(text: str) -> List[str]:
    """
    Bug #2 fix: only accept lines that look like actual certification names.
    A real certification line:
      - contains a cert keyword (AWS, Certified, etc.)
      - is NOT a section heading by itself (e.g. the word "Certifications" alone)
      - is NOT a skills list (more than 3 comma/space separated tokens → likely a skills line)
      - is NOT a bullet from experience (starts lowercase or is a short phrase)
    """
    certs: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not _CERT_LINES_RE.search(stripped):
            continue
        if not (10 < len(stripped) < 150):
            continue
        # Skip bare section headings (single word or very short)
        if len(stripped.split()) <= 1:
            continue
        # Skip lines that look like skills lists (many comma-separated items)
        tokens = [t.strip() for t in re.split(r"[,\s]+", stripped) if t.strip()]
        if len(tokens) > 6:
            continue
        # Skip OCR artifacts: a line of one repeated word
        # (e.g. "Professional Professional Professional Professional")
        if len(tokens) > 1 and len({t.lower() for t in tokens}) == 1:
            continue
        # Skip lines that are clearly bullets from experience (start lowercase)
        if stripped[0].islower():
            continue
        certs.append(stripped)

    # Deduplicate preserving order
    seen: set = set()
    unique: List[str] = []
    for c in certs:
        key = c.lower()
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique[:15]
