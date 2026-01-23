"""
Resume schemas for API validation.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ResumeCreate(BaseModel):
    """Schema for creating a resume."""
    job_id: int
    selected_projects: Optional[List[str]] = None  # Auto-select if not provided


class ResumeResponse(BaseModel):
    """Schema for resume response."""
    id: int
    job_id: Optional[int]
    job_title: str
    company: str
    resume_location: Optional[str]
    selected_projects: List[str]
    tex_path: Optional[str]
    pdf_path: Optional[str]
    cloud_url: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
