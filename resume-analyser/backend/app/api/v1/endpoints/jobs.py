"""Job-related helper endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from app.schemas import JobDescriptionRequest, JobRoleTemplate, ParsedJobDescription
from app.services.job_parser import parse_job_description
from app.services.job_templates import TEMPLATES

router = APIRouter()


@router.post(
    "/parse",
    response_model=ParsedJobDescription,
    summary="Parse a raw job description to extract structured skills & info",
)
async def parse_job(req: JobDescriptionRequest):
    return parse_job_description(req)


@router.get(
    "/templates",
    response_model=list[JobRoleTemplate],
    summary="List pre-defined job role templates for quick JD pre-filling",
)
async def list_job_templates():
    """Curated, editable starting points for common roles (grouped by category client-side)."""
    return TEMPLATES
