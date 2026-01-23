"""
Search service for managing search operations.
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload

from app.models.search_session import SearchSession
from app.models.job import Job
from app.core.pipeline import AsyncSearchPipeline
from app.schemas.search import SearchStart, SearchStatus, SearchResults

logger = logging.getLogger(__name__)


class SearchService:
    """Service for managing job searches."""
    
    def __init__(self):
        """Initialize search service."""
        self.pipeline = AsyncSearchPipeline()
    
    async def start_search(
        self,
        db: AsyncSession,
        search_data: SearchStart
    ) -> int:
        """
        Start a new search session.
        
        Args:
            db: Database session
            search_data: Search configuration
            
        Returns:
            Search session ID
        """
        # Create search session
        search_session = SearchSession(
            job_titles=search_data.job_titles,
            domains=search_data.domains,
            filters=search_data.filters.dict() if search_data.filters else {},
            status="pending",
            progress=0,
            started_at=datetime.now()
        )
        
        db.add(search_session)
        await db.commit()
        await db.refresh(search_session)
        
        # Start pipeline in background
        asyncio.create_task(
            self.pipeline.run_search(
                db=db,
                search_id=search_session.id,
                job_titles=search_data.job_titles,
                domains=search_data.domains,
                filters=search_data.filters.dict() if search_data.filters else {}
            )
        )
        
        return search_session.id
    
    async def get_search_status(
        self,
        db: AsyncSession,
        search_id: int
    ) -> Optional[SearchStatus]:
        """Get search session status."""
        result = await db.execute(
            select(SearchSession).where(SearchSession.id == search_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            return None
        
        return SearchStatus(
            search_id=session.id,
            status=session.status,
            progress=session.progress,
            current_step=session.current_step,
            urls_found=session.urls_found,
            jobs_extracted=session.jobs_extracted,
            jobs_parsed=session.jobs_parsed,
            jobs_saved=session.jobs_saved,
            error_message=session.error_message,
            started_at=session.started_at,
            completed_at=session.completed_at
        )
    
    async def get_search_results(
        self,
        db: AsyncSession,
        search_id: int
    ) -> Optional[SearchResults]:
        """Get jobs from a search session."""
        # Get jobs created after the search started
        result = await db.execute(
            select(SearchSession).where(SearchSession.id == search_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            return None
        
        # Get jobs created after search started
        jobs_result = await db.execute(
            select(Job)
            .where(Job.created_at >= session.started_at)
            .order_by(Job.relevance_score.desc())
        )
        jobs = jobs_result.scalars().all()
        
        # Convert to dicts
        jobs_list = [
            {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "remote": job.remote,
                "yoe_required": job.yoe_required,
                "relevance_score": job.relevance_score,
                "required_skills": job.required_skills,
                "resume_url": job.resume_url
            }
            for job in jobs
        ]
        
        return SearchResults(
            search_id=search_id,
            jobs=jobs_list,
            total=len(jobs_list)
        )
    
    async def cancel_search(
        self,
        db: AsyncSession,
        search_id: int
    ) -> bool:
        """Cancel a running search."""
        await db.execute(
            update(SearchSession)
            .where(SearchSession.id == search_id)
            .values(
                status="cancelled",
                completed_at=datetime.now()
            )
        )
        await db.commit()
        return True
