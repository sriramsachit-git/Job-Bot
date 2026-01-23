"""
Unextracted job model for tracking failed extractions.
"""
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime
from sqlalchemy.sql import func
from app.database import Base


class UnextractedJob(Base):
    """Unextracted job model."""
    __tablename__ = "unextracted_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False, index=True)
    title = Column(String)
    snippet = Column(Text)
    source_domain = Column(String, index=True)
    methods_attempted = Column(JSON)  # List of extraction methods tried
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
