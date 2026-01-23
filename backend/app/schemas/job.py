"""
Job schemas for API validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


class JobBase(BaseModel):
    """Base job schema."""
    title: str
    company: str
    location: Optional[str] = None
    remote: bool = False
    yoe_required: int = 0
    required_skills: Optional[List[str]] = None
    nice_to_have_skills: Optional[List[str]] = None


class JobCreate(JobBase):
    """Schema for creating a job."""
    url: str
    employment_type: Optional[str] = None
    salary_range: Optional[str] = None
    responsibilities: Optional[List[str]] = None
    job_summary: Optional[str] = None
    date_posted: Optional[date] = None
    source_domain: Optional[str] = None
    relevance_score: int = 0


class JobUpdate(BaseModel):
    """Schema for updating a job."""
    status: Optional[str] = None
    applied: Optional[bool] = None
    applied_date: Optional[date] = None
    notes: Optional[str] = None


class JobResponse(JobBase):
    """Schema for job response."""
    id: int
    url: str
    employment_type: Optional[str] = None
    salary_range: Optional[str] = None
    responsibilities: Optional[List[str]] = None
    job_summary: Optional[str] = None
    date_posted: Optional[date] = None
    source_domain: Optional[str] = None
    relevance_score: int
    status: str
    applied: bool
    applied_date: Optional[date] = None
    notes: Optional[str] = None
    resume_id: Optional[int] = None
    resume_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Schema for paginated job list response."""
    jobs: List[JobResponse]
    total: int
    page: int
    pages: int
    limit: int
