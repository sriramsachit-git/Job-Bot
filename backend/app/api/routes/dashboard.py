"""
Dashboard API routes.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import get_database
from app.models.job import Job
from app.models.resume import Resume
from app.models.search_session import SearchSession
from app.schemas.dashboard import DashboardStats

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_database)
):
    """Get dashboard statistics."""
    # Total jobs
    total_result = await db.execute(select(func.count(Job.id)))
    total_jobs = total_result.scalar() or 0
    
    # Applied jobs
    applied_result = await db.execute(
        select(func.count(Job.id)).where(Job.applied == True)
    )
    applied = applied_result.scalar() or 0
    
    # Pending jobs (status = 'new')
    pending_result = await db.execute(
        select(func.count(Job.id)).where(Job.status == "new")
    )
    pending = pending_result.scalar() or 0
    
    # Resumes generated
    resumes_result = await db.execute(select(func.count(Resume.id)))
    resumes_generated = resumes_result.scalar() or 0
    
    # Recent searches
    recent_searches_result = await db.execute(
        select(SearchSession)
        .order_by(SearchSession.created_at.desc())
        .limit(5)
    )
    recent_searches = recent_searches_result.scalars().all()
    
    recent_searches_list = [
        {
            "id": s.id,
            "job_titles": s.job_titles,
            "status": s.status,
            "jobs_saved": s.jobs_saved,
            "created_at": s.created_at.isoformat() if s.created_at else None
        }
        for s in recent_searches
    ]
    
    return DashboardStats(
        total_jobs=total_jobs,
        applied=applied,
        pending=pending,
        resumes_generated=resumes_generated,
        recent_searches=recent_searches_list
    )


@router.get("/recent-jobs")
async def get_recent_jobs(
    limit: int = 10,
    db: AsyncSession = Depends(get_database)
):
    """Get recent jobs."""
    result = await db.execute(
        select(Job)
        .order_by(Job.created_at.desc())
        .limit(limit)
    )
    jobs = result.scalars().all()
    
    from app.schemas.job import JobResponse
    from app.api.routes.jobs import job_to_dict
    
    return [JobResponse.model_validate(job_to_dict(job)) for job in jobs]
