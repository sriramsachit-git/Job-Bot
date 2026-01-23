"""
Search session model for tracking search operations.
"""
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime
from sqlalchemy.sql import func
from app.database import Base


class SearchSession(Base):
    """Search session model."""
    __tablename__ = "search_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    job_titles = Column(JSON, nullable=False)  # List of job titles
    domains = Column(JSON, nullable=False)  # List of domains
    filters = Column(JSON)  # Search filters dict
    
    # Results
    urls_found = Column(Integer, default=0)
    jobs_extracted = Column(Integer, default=0)
    jobs_parsed = Column(Integer, default=0)
    jobs_saved = Column(Integer, default=0)
    
    # Status
    status = Column(String, default="pending", index=True)  # pending, running, completed, failed, cancelled
    error_message = Column(Text, nullable=True)
    progress = Column(Integer, default=0)  # 0-100
    current_step = Column(String)  # searching, extracting, filtering, parsing, scoring, saving
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
