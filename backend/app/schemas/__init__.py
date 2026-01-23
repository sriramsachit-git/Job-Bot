"""Pydantic schemas for API validation."""
from .job import JobCreate, JobUpdate, JobResponse, JobListResponse
from .resume import ResumeCreate, ResumeResponse
from .search import SearchStart, SearchStatus, SearchResults
from .dashboard import DashboardStats
from .settings import UserSettingsResponse, UserSettingsUpdate

__all__ = [
    "JobCreate", "JobUpdate", "JobResponse", "JobListResponse",
    "ResumeCreate", "ResumeResponse",
    "SearchStart", "SearchStatus", "SearchResults",
    "DashboardStats",
    "UserSettingsResponse", "UserSettingsUpdate"
]
