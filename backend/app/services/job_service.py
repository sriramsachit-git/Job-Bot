"""
Job service for saving jobs to async database.
"""
import json
import logging
from datetime import datetime
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert

from app.models.job import Job
from src.llm_parser import ParsedJob

logger = logging.getLogger(__name__)


class JobService:
    """Service for managing jobs in async database."""
    
    @staticmethod
    async def save_jobs_batch(
        db: AsyncSession,
        jobs: List[Tuple[ParsedJob, int]]
    ) -> Tuple[int, int]:
        """
        Save multiple jobs to async database.
        
        Args:
            db: Database session
            jobs: List of (ParsedJob, relevance_score) tuples
            
        Returns:
            Tuple of (saved_count, skipped_count)
        """
        saved = 0
        skipped = 0
        
        for parsed_job, relevance_score in jobs:
            try:
                # Check if job already exists
                result = await db.execute(
                    select(Job).where(Job.url == parsed_job.source_url)
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    skipped += 1
                    logger.debug(f"Skipped duplicate: {parsed_job.source_url}")
                    continue
                
                # Create new job
                job = Job(
                    url=parsed_job.source_url,
                    title=parsed_job.job_title,
                    company=parsed_job.company,
                    location=parsed_job.location,
                    remote=parsed_job.remote or False,
                    employment_type=parsed_job.employment_type,
                    salary_range=parsed_job.salary_range,
                    yoe_required=parsed_job.yoe_required,
                    required_skills=parsed_job.required_skills or [],
                    nice_to_have_skills=parsed_job.nice_to_have_skills or [],
                    responsibilities=parsed_job.responsibilities or [],
                    job_summary=parsed_job.job_summary,
                    date_posted=None,  # Can be extracted if available
                    source_domain=parsed_job.source_domain,
                    relevance_score=relevance_score,
                    status="new"
                )
                
                db.add(job)
                saved += 1
                logger.debug(f"Saved: {parsed_job.job_title} @ {parsed_job.company}")
                
            except Exception as e:
                logger.error(f"Error saving job {parsed_job.source_url}: {e}")
                skipped += 1
        
        await db.commit()
        logger.info(f"Batch save: {saved} saved, {skipped} skipped")
        return saved, skipped
