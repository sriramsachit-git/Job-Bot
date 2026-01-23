"""
User settings model.
"""
from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime
from sqlalchemy.sql import func
from app.database import Base


class UserSettings(Base):
    """User settings model."""
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, default=1)  # Single row
    default_job_titles = Column(JSON)  # List of default job titles
    default_domains = Column(JSON)  # List of default domains
    max_yoe = Column(Integer, default=5)
    preferred_locations = Column(JSON)  # List of locations
    remote_only = Column(Boolean, default=False)
    excluded_keywords = Column(JSON)  # List of keywords to exclude
    cloud_storage_config = Column(JSON)  # Cloud storage credentials/config
    
    # Timestamps
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
