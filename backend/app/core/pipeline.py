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
            
            # Run pipeline in thread pool (it's synchronous)
            loop = asyncio.get_event_loop()
            summary = await loop.run_in_executor(
                None,
                self._run_sync_pipeline,
                job_titles,
                domains,
                filters or {},
                update_status
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
    
    def _run_sync_pipeline(
        self,
        job_titles: List[str],
        domains: List[str],
        filters: Dict[str, Any],
        update_status_callback
    ) -> Dict[str, Any]:
        """
        Run the synchronous pipeline.
        This runs in a thread pool.
        """
        # Note: update_status_callback won't work here since it's async
        # We'll update status at key points instead
        summary = self.pipeline.run(
            keywords=job_titles,
            sites=domains,
            num_results=filters.get("num_results", 50),
            date_restrict=filters.get("date_restrict", "d1"),
            min_score=filters.get("min_score", 30)
        )
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
