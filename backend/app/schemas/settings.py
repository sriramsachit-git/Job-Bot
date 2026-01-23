"""
Settings schemas.
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class UserSettingsResponse(BaseModel):
    """User settings response."""
    default_job_titles: Optional[List[str]] = None
    default_domains: Optional[List[str]] = None
    max_yoe: int = 5
    preferred_locations: Optional[List[str]] = None
    remote_only: bool = False
    excluded_keywords: Optional[List[str]] = None
    cloud_storage_config: Optional[Dict[str, Any]] = None


class UserSettingsUpdate(BaseModel):
    """User settings update."""
    default_job_titles: Optional[List[str]] = None
    default_domains: Optional[List[str]] = None
    max_yoe: Optional[int] = None
    preferred_locations: Optional[List[str]] = None
    remote_only: Optional[bool] = None
    excluded_keywords: Optional[List[str]] = None
    cloud_storage_config: Optional[Dict[str, Any]] = None
