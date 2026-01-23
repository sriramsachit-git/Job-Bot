"""
Dashboard schemas.
"""
from pydantic import BaseModel
from typing import List, Dict, Any


class DashboardStats(BaseModel):
    """Dashboard statistics."""
    total_jobs: int
    applied: int
    pending: int
    resumes_generated: int
    recent_searches: List[Dict[str, Any]]
