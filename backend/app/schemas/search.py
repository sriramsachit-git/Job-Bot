"""
Search schemas for API validation.
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class SearchFilters(BaseModel):
    """Search filters."""
    max_yoe: Optional[int] = None
    remote_only: Optional[bool] = False
    locations: Optional[List[str]] = None
    excluded_keywords: Optional[List[str]] = None


class SearchStart(BaseModel):
    """Schema for starting a search."""
    job_titles: List[str]
    domains: List[str]
    filters: Optional[SearchFilters] = None


class SearchStatus(BaseModel):
    """Schema for search status response."""
    search_id: int
    status: str  # pending, running, completed, failed, cancelled
    progress: int  # 0-100
    current_step: Optional[str] = None
    urls_found: int = 0
    jobs_extracted: int = 0
    jobs_parsed: int = 0
    jobs_saved: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class SearchResults(BaseModel):
    """Schema for search results."""
    search_id: int
    jobs: List[Dict[str, Any]]  # List of job dictionaries
    total: int
