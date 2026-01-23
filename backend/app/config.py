"""
Backend configuration management.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List, Dict, Any


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    google_api_key: str
    google_cse_id: str
    openai_api_key: str
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./data/jobs.db"
    
    # Paths
    data_dir: Path = Path("./data")
    resumes_dir: Path = Path("./data/resumes")
    
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


# Create settings instance
settings = Settings()

# Ensure directories exist
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.resumes_dir.mkdir(parents=True, exist_ok=True)
