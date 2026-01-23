"""
Resume model for database.
"""
from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Resume(Base):
    """Resume model."""
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True, index=True)
    job_title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    resume_location = Column(String)  # Location shown on resume
    
    # Selected projects
    selected_projects = Column(JSON)  # List of project names
    
    # File paths
    tex_path = Column(String)  # Local LaTeX file
    pdf_path = Column(String)  # Local PDF file
    cloud_url = Column(String)  # S3/GCS URL for PDF
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    job = relationship("Job", back_populates="resume", foreign_keys=[job_id])
