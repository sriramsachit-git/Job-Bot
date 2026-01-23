"""
Resume generation service.
"""
import logging
from pathlib import Path
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.job import Job
from app.models.resume import Resume
from app.schemas.resume import ResumeCreate, ResumeResponse
from src.resume_generator import ResumeGenerator
from app.config import settings

logger = logging.getLogger(__name__)


class ResumeService:
    """Service for generating resumes."""
    
    def __init__(self):
        """Initialize resume service."""
        self.generator = ResumeGenerator(
            config_path="data/resume_config.yaml",
            projects_path="data/projects.json",
            output_dir=str(settings.resumes_dir)
        )
    
    async def generate_resume(
        self,
        db: AsyncSession,
        resume_data: ResumeCreate
    ) -> ResumeResponse:
        """
        Generate a resume for a job.
        
        Args:
            db: Database session
            resume_data: Resume creation data
            
        Returns:
            Generated resume
        """
        # Get job
        result = await db.execute(
            select(Job).where(Job.id == resume_data.job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise ValueError(f"Job {resume_data.job_id} not found")
        
        # Convert job to dict format expected by generator
        job_dict = {
            'id': job.id,
            'title': job.title,
            'company': job.company,
            'url': job.url,
            'location': job.location,
            'required_skills': job.required_skills or [],
            'nice_to_have_skills': job.nice_to_have_skills or [],
            'responsibilities': job.responsibilities or [],
            'yoe_required': job.yoe_required,
            'remote': job.remote,
            'source_domain': job.source_domain
        }
        
        # Generate recommendations
        recommendations = self.generator.generate_recommendations([job_dict])
        
        if not recommendations:
            raise ValueError("Failed to generate recommendations")
        
        rec = recommendations[0]
        
        # Auto-select projects if not provided
        if not resume_data.selected_projects:
            rec = self.generator.auto_select_top3([rec])[0]
            selected_projects = [p.name for p in rec.selected_projects]
        else:
            selected_projects = resume_data.selected_projects
        
        # Generate resume
        results = self.generator.generate_resumes([rec])
        
        if not results or not results[0].get("success"):
            raise ValueError("Failed to generate resume")
        
        result_data = results[0]
        
        # Create resume record
        resume = Resume(
            job_id=job.id,
            job_title=job.title,
            company=job.company,
            resume_location=result_data.get("resume_location"),
            selected_projects=selected_projects,
            tex_path=result_data.get("tex_path"),
            pdf_path=result_data.get("pdf_path"),
            cloud_url=None  # Will be set after upload
        )
        
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        
        # Update job with resume URL
        job.resume_id = resume.id
        job.resume_url = resume.cloud_url or resume.pdf_path
        await db.commit()
        
        return ResumeResponse(
            id=resume.id,
            job_id=resume.job_id,
            job_title=resume.job_title,
            company=resume.company,
            resume_location=resume.resume_location,
            selected_projects=resume.selected_projects or [],
            tex_path=resume.tex_path,
            pdf_path=resume.pdf_path,
            cloud_url=resume.cloud_url,
            created_at=resume.created_at
        )
