"""
Configuration management for the job search pipeline.
Loads environment variables and provides typed configuration objects.
"""

import os
from typing import Set, Dict, List, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""
    
    # API Keys - These are the main credentials
    api_key: str = os.getenv("GOOGLE_API_KEY", "")
    cx_id: str = os.getenv("GOOGLE_CSE_ID", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Paths
    database_path: str = os.getenv("DATABASE_PATH", "data/jobs.db")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Rate limiting
    request_delay: float = 1.0
    max_retries: int = 3
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that all required config values are present."""
        required = ["api_key", "cx_id", "openai_api_key"]
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        return True


# Create singleton instance
config = Config()


# Sites that require JavaScript rendering (Playwright)
JS_HEAVY_SITES: Set[str] = {
    "greenhouse.io",
    "lever.co",
    "ashbyhq.com",
    "myworkdayjobs.com",
    "icims.com",
    "smartrecruiters.com",
    "jobvite.com",
    "oraclecloud.com",
    "workforcenow.adp.com",
    "rippling-ats.com",
    "rippling.com",
    "recruitee.com",
    "pinpointhq.com",
    "recruiting.paylocity.com",
}

# Sites that work well with Jina Reader
JINA_FRIENDLY_SITES: Set[str] = {
    "workable.com",
    "wellfound.com",
    "builtin.com",
    "teamtailor.com",
    "workatastartup.com",
    "breezy.hr",
    "homerun.co",
    "notion.site",
    "dover.io",
    "keka.com",
    "careerpuck.com",
}

# Default job board sites for searching
DEFAULT_JOB_SITES: List[str] = [
    "greenhouse.io",
    "lever.co",
    "ashbyhq.com",
    "myworkdayjobs.com",
    "jobs.workable.com",
    "wellfound.com",
    "builtin.com",
    "icims.com",
    "smartrecruiters.com",
    "jobvite.com",
]

# User profile for job filtering - CUSTOMIZE THIS
USER_PROFILE: Dict[str, Any] = {
    "max_yoe": 5,
    "required_skills": [
        "python", 
        "sql", 
        "machine learning", 
        "data science",
        "pytorch",
        "tensorflow"
    ],
    "preferred_skills": [
        "aws", 
        "spark", 
        "kubernetes", 
        "docker",
        "mlops",
        "llm",
        "rag",
        "langchain",
        "deep learning",
        "nlp",
        "computer vision"
    ],
    "preferred_locations": [
        "San Francisco", 
        "Remote", 
        "New York", 
        "San Jose", 
        "Seattle",
        "San Diego",
        "Los Angeles",
        "Austin"
    ],
    "remote_only": False,
    "exclude_title_keywords": [
        "senior", 
        "staff", 
        "principal", 
        "director", 
        "lead", 
        "manager", 
        "head of", 
        "vp",
        "vice president",
        "chief",
        "architect"
    ],
}
