"""API v1 main router."""
from fastapi import APIRouter

from app.api.v1.endpoints import resume, analysis, jobs

api_router = APIRouter()
api_router.include_router(resume.router, prefix="/resume", tags=["resume"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
