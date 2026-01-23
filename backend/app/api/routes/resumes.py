"""
Resume API routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.api.deps import get_database
from app.models.resume import Resume
from app.schemas.resume import ResumeCreate, ResumeResponse
from app.services.resume_service import ResumeService

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


@router.post("", response_model=ResumeResponse)
async def generate_resume(
    resume_data: ResumeCreate,
    db: AsyncSession = Depends(get_database)
):
    """Generate a resume for a job."""
    service = ResumeService()
    try:
        resume = await service.generate_resume(db, resume_data)
        return resume
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate resume: {str(e)}")


@router.post("/bulk-generate")
async def bulk_generate_resumes(
    job_ids: List[int],
    db: AsyncSession = Depends(get_database)
):
    """Generate resumes for multiple jobs."""
    service = ResumeService()
    results = []
    
    for job_id in job_ids:
        try:
            resume_data = ResumeCreate(job_id=job_id)
            resume = await service.generate_resume(db, resume_data)
            results.append({
                "job_id": job_id,
                "resume_id": resume.id,
                "pdf_url": resume.cloud_url or resume.pdf_path,
                "status": "success"
            })
        except Exception as e:
            results.append({
                "job_id": job_id,
                "status": "failed",
                "error": str(e)
            })
    
    return {"results": results}


@router.get("", response_model=List[ResumeResponse])
async def get_resumes(
    db: AsyncSession = Depends(get_database)
):
    """Get all resumes."""
    result = await db.execute(select(Resume).order_by(Resume.created_at.desc()))
    resumes = result.scalars().all()
    return [ResumeResponse.model_validate(r) for r in resumes]


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: int,
    db: AsyncSession = Depends(get_database)
):
    """Get a specific resume."""
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    return ResumeResponse.model_validate(resume)


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: int,
    db: AsyncSession = Depends(get_database)
):
    """Delete a resume."""
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    await db.delete(resume)
    await db.commit()
    
    return {"success": True}
