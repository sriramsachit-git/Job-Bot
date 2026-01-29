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

logger = logging.getLogger(__name__)


class AsyncSearchPipeline:
    """
    Async wrapper around the synchronous JobSearchPipeline.
    Runs the pipeline in a thread pool to avoid blocking.
    """
    
    def __init__(self):
        """Initialize the async pipeline wrapper."""
        # Pipeline is created per-execution in executor thread to avoid
        # SQLite thread-safety issues (connections are thread-local)
        pass
    
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
        # Update status callback (committed so websocket polling can see it)
        async def update_status(step: str, progress: int, details: Dict[str, Any] = None):
            await self._update_search_status(search_id, step, progress, details)
        
        try:
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
        
        Note: Pipeline must be created inside the executor thread to avoid
        SQLite thread-safety issues (connections are thread-local).
        """
        loop = asyncio.get_event_loop()
        progress_queue: "asyncio.Queue[tuple[str, int, Optional[Dict[str, Any]]]]" = asyncio.Queue()

        def _thread_progress(step: str, progress: int, details: Optional[Dict[str, Any]] = None):
            # Called from executor thread; forward safely to event loop
            loop.call_soon_threadsafe(progress_queue.put_nowait, (step, progress, details))

        async def _consume_progress():
            while True:
                step, progress, details = await progress_queue.get()
                if step == "__done__":
                    return
                try:
                    await self._update_search_status(search_id, step, progress, details)
                except Exception:
                    # Don't kill the pipeline on progress update failure
                    pass

        consumer_task = asyncio.create_task(_consume_progress())

        def _run_pipeline_in_thread():
            """Create pipeline and run it in the executor thread."""
            # Import here (lazy) so importing the FastAPI app does NOT
            # import heavy deps (pandas/numpy) unless a search is actually run.
            from src.pipeline import JobSearchPipeline

            # Create pipeline inside the executor thread so SQLite connection
            # is created and used in the same thread
            pipeline = JobSearchPipeline()
            return pipeline.run(
                job_titles,
                domains,
                filters.get("num_results", 50),
                filters.get("date_restrict", "d1"),
                filters.get("min_score", 30),
                progress_callback=_thread_progress
            )
        
        # Run pipeline in thread pool
        summary = await loop.run_in_executor(None, _run_pipeline_in_thread)
        # Stop consumer
        await progress_queue.put(("__done__", 0, None))
        await consumer_task
        
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
        search_id: int,
        step: str,
        progress: int,
        details: Optional[Dict[str, Any]] = None
    ):
        """Update search session status."""
        # Use a fresh session and COMMIT so websocket polling (separate sessions)
        # can see progress updates immediately.
        from app.database import AsyncSessionLocal
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(
                    update(SearchSession)
                    .where(SearchSession.id == search_id)
                    .values(
                        status="running",
                        current_step=step,
                        progress=progress,
                        **{k: v for k, v in (details or {}).items() if k in ["urls_found", "jobs_extracted", "jobs_parsed", "jobs_saved"]}
                    )
                )
                await session.commit()
        except Exception as e:
            logger.error(f"Error updating search status: {e}")
