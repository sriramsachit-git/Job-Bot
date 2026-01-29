"""
Backend configuration management.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Dict, Any, Optional


def _default_resumes_dir() -> Path:
    """Single canonical resumes dir: project root data/resumes (absolute)."""
    # backend/app/config.py -> project root = parent.parent.parent
    project_root = Path(__file__).resolve().parent.parent.parent
    return (project_root / "data" / "resumes").resolve()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys (optional for testing, required for actual use)
    google_api_key: str = ""
    google_cse_id: str = ""
    openai_api_key: str = ""
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./data/jobs.db"
    
    # Paths
    data_dir: Path = Path("./data")
    # Single directory for all resumes (Option C). Default: project root data/resumes.
    # Set RESUMES_DIR to an absolute path to override, e.g. /path/to/job_search_pipeline/data/resumes
    resumes_dir: Path = Field(default_factory=_default_resumes_dir)
    
    # Cloud Storage
    cloud_storage_provider: str = "local"  # local, s3, gcs, r2
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    s3_bucket: str = ""
    s3_region: str = "us-east-1"
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


# Create settings instance
settings = Settings()

# Resolve resumes_dir to absolute path (single base for all resume files)
settings.resumes_dir = settings.resumes_dir.resolve()
# Ensure directories exist
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.resumes_dir.mkdir(parents=True, exist_ok=True)
