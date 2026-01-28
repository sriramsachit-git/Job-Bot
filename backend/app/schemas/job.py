"""
Job schemas for API validation.
"""
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import date, datetime


class JobBase(BaseModel):
    """Base job schema."""
    title: str
    company: str
    location: Optional[str] = None
    remote: Optional[bool] = False  # Optional to handle NULL values from old DB
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
    status: Optional[str] = "new"  # Optional to handle NULL values from old DB
    applied: Optional[bool] = False  # Optional to handle NULL values from old DB
    applied_date: Optional[date] = None
    notes: Optional[str] = None
    resume_id: Optional[int] = None
    resume_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
    
    @model_validator(mode='before')
    @classmethod
    def set_defaults_for_none(cls, data):
        """Set defaults for None values from database."""
        # Handle SQLAlchemy model objects (when from_attributes=True)
        if hasattr(data, '__dict__') and not isinstance(data, dict):
            # Convert to dict and set defaults
            result = {}
            for key in cls.model_fields.keys():
                try:
                    value = getattr(data, key, None)
                except AttributeError:
                    value = None
                if value is None:
                    if key == 'remote':
                        value = False
                    elif key == 'status':
                        value = "new"
                    elif key == 'applied':
                        value = False
                result[key] = value
            return result
        # Handle dict input (Pydantic might convert SQLAlchemy to dict first)
        elif isinstance(data, dict):
            if data.get('remote') is None:
                data['remote'] = False
            if data.get('status') is None:
                data['status'] = "new"
            if data.get('applied') is None:
                data['applied'] = False
        return data


class JobListResponse(BaseModel):
    """Schema for paginated job list response."""
    jobs: List[JobResponse]
    total: int
    page: int
    pages: int
    limit: int
