"""
Async pipeline orchestrator for FastAPI.
Adapts the existing synchronous pipeline to work with async FastAPI.
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.search_session import SearchSession
from app.models.job import Job
from app.services.job_service import JobService
from src.pipeline import JobSearchPipeline
from src.llm_parser import ParsedJob

logger = logging.getLogger(__name__)


class AsyncSearchPipeline:
    """
    Async wrapper around the synchronous JobSearchPipeline.
    Runs the pipeline in a thread pool to avoid blocking.
    """
    
    def __init__(self):
        """Initialize the pipeline."""
        self.pipeline = None
    
    async def run_search(
        self,
        db: AsyncSession,
        search_id: int,
        job_titles: List[str],
        domains: List[str],
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run search pipeline asynchronously.
        
        Args:
            db: Database session
            search_id: Search session ID
            job_titles: List of job titles to search
            domains: List of domains to search
            filters: Optional search filters
            
        Returns:
            Summary dict with results
        """
        # Update status callback
        async def update_status(step: str, progress: int, details: Dict[str, Any] = None):
            await self._update_search_status(db, search_id, step, progress, details)
        
        try:
            # Initialize pipeline
            if not self.pipeline:
                self.pipeline = JobSearchPipeline()
            
            # Update status to running
            await update_status("searching", 10, {"message": "Starting search..."})
            
            # Run pipeline and save to async database
            summary = await self._run_sync_pipeline_with_db_save(
                db,
                job_titles,
                domains,
                filters or {},
                search_id
            )
            
            # Update final status
            await update_status("completed", 100, {
                "urls_found": summary.get("searched", 0),
                "jobs_extracted": summary.get("extracted", 0),
                "jobs_parsed": summary.get("parsed", 0),
                "jobs_saved": summary.get("saved", 0)
            })
            
            # Mark search as completed
            await db.execute(
                update(SearchSession)
                .where(SearchSession.id == search_id)
                .values(
                    status="completed",
                    completed_at=datetime.now(),
                    urls_found=summary.get("searched", 0),
                    jobs_extracted=summary.get("extracted", 0),
                    jobs_parsed=summary.get("parsed", 0),
                    jobs_saved=summary.get("saved", 0)
                )
            )
            await db.commit()
            
            return summary
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            await update_status("failed", 0, {"error": str(e)})
            await db.execute(
                update(SearchSession)
                .where(SearchSession.id == search_id)
                .values(
                    status="failed",
                    error_message=str(e),
                    completed_at=datetime.now()
                )
            )
            await db.commit()
            raise
    
    async def _run_sync_pipeline_with_db_save(
        self,
        db: AsyncSession,
        job_titles: List[str],
        domains: List[str],
        filters: Dict[str, Any],
        search_id: int
    ) -> Dict[str, Any]:
        """
        Run the synchronous pipeline and save jobs to async database.
        """
        # Run pipeline in thread pool
        loop = asyncio.get_event_loop()
        summary = await loop.run_in_executor(
            None,
            self.pipeline.run,
            job_titles,
            domains,
            filters.get("num_results", 50),
            filters.get("date_restrict", "d1"),
            filters.get("min_score", 30)
        )
        
        # Get newly saved jobs from the pipeline's database
        # and save them to async database
        if summary.get("saved", 0) > 0:
            try:
                # Get jobs from the pipeline's database
                new_jobs = summary.get("new_jobs", [])
                if new_jobs:
                    # Convert to ParsedJob format and save to async DB
                    from src.llm_parser import ParsedJob
                    jobs_to_save = []
                    
                    for job_dict in new_jobs:
                        try:
                            # Reconstruct ParsedJob from dict
                            parsed_job = ParsedJob(
                                job_title=job_dict.get("title", ""),
                                company=job_dict.get("company", ""),
                                location=job_dict.get("location"),
                                remote=job_dict.get("remote"),
                                employment_type=job_dict.get("employment_type"),
                                salary_range=job_dict.get("salary"),
                                yoe_required=job_dict.get("yoe_required", 0),
                                required_skills=job_dict.get("required_skills", []),
                                nice_to_have_skills=job_dict.get("nice_to_have_skills", []),
                                responsibilities=job_dict.get("responsibilities", []),
                                job_summary=job_dict.get("job_summary"),
                                source_url=job_dict.get("url", ""),
                                source_domain=job_dict.get("source_domain", "")
                            )
                            score = job_dict.get("relevance_score", 0)
                            jobs_to_save.append((parsed_job, score))
                        except Exception as e:
                            logger.error(f"Error converting job: {e}")
                    
                    if jobs_to_save:
                        saved, skipped = await JobService.save_jobs_batch(db, jobs_to_save)
                        summary["async_saved"] = saved
                        summary["async_skipped"] = skipped
            except Exception as e:
                logger.error(f"Error saving jobs to async DB: {e}")
        
        return summary
    
    async def _update_search_status(
        self,
        db: AsyncSession,
        search_id: int,
        step: str,
        progress: int,
        details: Optional[Dict[str, Any]] = None
    ):
        """Update search session status."""
        try:
            await db.execute(
                update(SearchSession)
                .where(SearchSession.id == search_id)
                .values(
                    status="running",
                    current_step=step,
                    progress=progress,
                    **{k: v for k, v in (details or {}).items() if k in ["urls_found", "jobs_extracted", "jobs_parsed", "jobs_saved"]}
                )
            )
            await db.commit()
        except Exception as e:
            logger.error(f"Error updating search status: {e}")
