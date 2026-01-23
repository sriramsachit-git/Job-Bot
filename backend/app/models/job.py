"""
Job model for database.
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, Date, JSON, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Job(Base):
    """Job posting model."""
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False, index=True)
    location = Column(String, index=True)
    remote = Column(Boolean, default=False, index=True)
    employment_type = Column(String)
    salary_range = Column(String)
    yoe_required = Column(Integer, default=0, index=True)
    
    # Skills and requirements
    required_skills = Column(JSON)  # List of strings
    nice_to_have_skills = Column(JSON)  # List of strings
    responsibilities = Column(JSON)  # List of strings
    job_summary = Column(Text)
    
    # Metadata
    date_posted = Column(Date)
    source_domain = Column(String, index=True)
    relevance_score = Column(Integer, default=0, index=True)
    
    # Status tracking
    status = Column(String, default="new", index=True)  # new, reviewed, applied, rejected, interview
    applied = Column(Boolean, default=False, index=True)
    applied_date = Column(Date)
    notes = Column(Text)
    
    # Resume relationship
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    resume_url = Column(String, nullable=True)  # Cloud storage URL
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    resume = relationship("Resume", back_populates="job", foreign_keys=[resume_id])
