"""
Job API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from typing import Optional, List
from math import ceil

from app.api.deps import get_database
from app.models.job import Job
from app.schemas.job import JobResponse, JobUpdate, JobListResponse

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=JobListResponse)
async def get_jobs(
    status: Optional[str] = Query(None),
    min_score: Optional[int] = Query(None),
    max_yoe: Optional[int] = Query(None),
    remote: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_database)
):
    """Get jobs with filtering and pagination."""
    query = select(Job)
    
    # Apply filters
    if status:
        query = query.where(Job.status == status)
    if min_score is not None:
        query = query.where(Job.relevance_score >= min_score)
    if max_yoe is not None:
        query = query.where(Job.yoe_required <= max_yoe)
    if remote is not None:
        query = query.where(Job.remote == remote)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.order_by(Job.relevance_score.desc(), Job.created_at.desc())
    query = query.limit(limit).offset(offset)
    
    # Execute
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    return JobListResponse(
        jobs=[JobResponse.model_validate(job) for job in jobs],
        total=total,
        page=(offset // limit) + 1,
        pages=ceil(total / limit) if total > 0 else 0,
        limit=limit
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_database)
):
    """Get a specific job by ID."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobResponse.model_validate(job)


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_update: JobUpdate,
    db: AsyncSession = Depends(get_database)
):
    """Update a job."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Update fields
    update_data = job_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)
    
    await db.commit()
    await db.refresh(job)
    
    return JobResponse.model_validate(job)


@router.delete("/{job_id}")
async def delete_job(
    job_id: int,
    db: AsyncSession = Depends(get_database)
):
    """Delete a job."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    await db.delete(job)
    await db.commit()
    
    return {"success": True}
