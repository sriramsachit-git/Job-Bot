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
from app.config import settings

logger = logging.getLogger(__name__)

# Get project root (go up from backend/app/services/ to project root)
# File is at: backend/app/services/resume_service.py
# Need to go: services -> app -> backend -> project_root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.resolve()


class ResumeService:
    """Service for generating resumes."""
    
    def __init__(self):
        """Initialize resume service."""
        # Lazy-load generator only when needed (to avoid errors if files don't exist)
        self._generator = None
        self._config_path = PROJECT_ROOT / "data" / "resume_config.yaml"
        self._projects_path = PROJECT_ROOT / "data" / "projects.json"
    
    @property
    def generator(self):
        """Lazy-load ResumeGenerator, checking for required files first."""
        if self._generator is None:
            # Check if config files exist
            if not self._config_path.exists():
                raise ValueError(
                    f"Resume config file not found: {self._config_path}\n"
                    f"Please create {self._config_path} with your resume information.\n"
                    f"See README.md for template."
                )
            if not self._projects_path.exists():
                raise ValueError(
                    f"Projects file not found: {self._projects_path}\n"
                    f"Please create {self._projects_path} with your project information.\n"
                    f"See README.md for template."
                )
            
            # Import here to avoid heavy imports at module level
            from src.resume_generator import ResumeGenerator
            
            # Single output dir (absolute) so all PDFs go to one place
            self._generator = ResumeGenerator(
                config_path=str(self._config_path),
                projects_path=str(self._projects_path),
                output_dir=str(settings.resumes_dir.resolve()),
            )
        return self._generator
    
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
            error_msg = results[0].get("error", "Unknown error") if results else "No results returned"
            logger.error(f"Resume generation failed: {error_msg}")
            raise ValueError(f"Failed to generate resume: {error_msg}")
        
        result_data = results[0]
        
        # Store only filename in DB (Option C: single base dir, resolve at download time)
        raw_pdf = result_data.get("pdf_path")
        raw_tex = result_data.get("tex_path")
        pdf_path = Path(raw_pdf).name if raw_pdf else None
        tex_path = Path(raw_tex).name if raw_tex else None
        
        if pdf_path and not (settings.resumes_dir / pdf_path).exists():
            logger.warning(f"PDF not in base dir: {settings.resumes_dir / pdf_path}")
        
        # Create resume record
        resume = Resume(
            job_id=job.id,
            job_title=job.title,
            company=job.company,
            resume_location=result_data.get("resume_location"),
            selected_projects=selected_projects,
            tex_path=tex_path,
            pdf_path=pdf_path,
            cloud_url=None  # Will be set after upload
        )
        
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        
        # Update job with resume URL
        # Always set resume_url to the download endpoint (it will handle missing pdf_path)
        resume_download_url = None
        if resume.cloud_url:
            resume_download_url = resume.cloud_url
        else:
            # Use resume_id-based download endpoint (will try to find PDF even if pdf_path is None)
            resume_download_url = f"/api/resumes/{resume.id}/download"
        
        job.resume_id = resume.id
        job.resume_url = resume_download_url
        await db.commit()
        
        logger.info(f"Set resume_url for job {job.id}: {resume_download_url}")
        
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
