"""
Resume API routes.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.api.deps import get_database
from app.models.resume import Resume
from app.schemas.resume import ResumeCreate, ResumeResponse
from app.services.resume_service import ResumeService

logger = logging.getLogger(__name__)
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
        # ValueError usually means missing config files or invalid input
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        # FileNotFoundError means config files are missing
        raise HTTPException(
            status_code=400,
            detail=f"Resume configuration files not found. {str(e)}\n\n"
                  f"Please create:\n"
                  f"- data/resume_config.yaml\n"
                  f"- data/projects.json\n\n"
                  f"See RESUME_SETUP.md or README.md for templates."
        )
    except Exception as e:
        import traceback
        logger.error(f"Resume generation error: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate resume: {str(e)}\n\n"
                  f"Check backend logs for details."
        )


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


# #region agent log
DEBUG_LOG = "/Users/sriramsachitchunduri/Documents/Project/Job/job_search_pipeline/.cursor/debug.log"
def _debug_log(payload: dict) -> None:
    import json
    import os
    try:
        os.makedirs(os.path.dirname(DEBUG_LOG), exist_ok=True)
        with open(DEBUG_LOG, "a") as f:
            f.write(json.dumps({**payload, "timestamp": __import__("time").time() * 1000}) + "\n")
    except Exception:
        pass
# #endregion

@router.get("/{resume_id}/download")
async def download_resume_by_id(
    resume_id: int,
    db: AsyncSession = Depends(get_database)
):
    """Download resume PDF by resume ID."""
    from fastapi.responses import FileResponse, RedirectResponse
    from pathlib import Path
    from app.config import settings
    
    # #region agent log
    _debug_log({"location": "resumes.py:download_resume_by_id:entry", "message": "download_resume_by_id", "data": {"resume_id": resume_id}, "sessionId": "debug-session", "hypothesisId": "A"})
    # #endregion
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    # #region agent log
    _debug_log({"location": "resumes.py:download_resume_by_id:after_lookup", "message": "resume_lookup", "data": {"resume_id": resume_id, "resume_found": resume is not None, "pdf_path": getattr(resume, "pdf_path", None), "cloud_url": getattr(resume, "cloud_url", None), "resumes_dir": str(settings.resumes_dir)}, "sessionId": "debug-session", "hypothesisId": "A,B"})
    # #endregion
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Try cloud URL first
    if resume.cloud_url:
        return RedirectResponse(url=resume.cloud_url)
    
    # Determine PDF path
    pdf_path = None
    
    if resume.pdf_path:
        # Store is filename only; resolve against single base (no path traversal)
        filename = Path(resume.pdf_path).name
        pdf_path = settings.resumes_dir / filename
        # #region agent log
        _debug_log({"location": "resumes.py:download_resume_by_id:resolved_path", "message": "pdf_path_resolved", "data": {"resume_id": resume_id, "pdf_path_db": resume.pdf_path, "filename": filename, "resolved_path": str(pdf_path), "resumes_dir": str(settings.resumes_dir), "file_exists": pdf_path.exists()}, "sessionId": "debug-session", "hypothesisId": "C,D,E"})
        # #endregion
    else:
        # Try to find PDF by looking for files matching the resume pattern
        logger.warning(f"Resume {resume_id} has no pdf_path, searching for PDF file...")
        if resume.job_id:
            # Try to find PDF in resumes directory
            from app.models.job import Job
            job_result = await db.execute(select(Job).where(Job.id == resume.job_id))
            job = job_result.scalar_one_or_none()
            if job:
                # Look for PDFs matching the job title/company
                import re
                safe_title = re.sub(r'[^\w\s-]', '', job.title)[:20].strip()
                safe_company = re.sub(r'[^\w\s-]', '', job.company)[:20].strip()
                
                # Try multiple patterns
                patterns = [
                    f"*{safe_company}*{safe_title}*.pdf",
                    f"*{safe_title}*{safe_company}*.pdf",
                    f"*{safe_company}*.pdf",
                ]
                
                pdf_files = []
                for pattern in patterns:
                    pdf_files = list(settings.resumes_dir.glob(pattern))
                    if pdf_files:
                        break
                
                if pdf_files:
                    # Use the most recent PDF
                    pdf_path = max(pdf_files, key=lambda p: p.stat().st_mtime)
                    logger.info(f"Found PDF file: {pdf_path}")
                else:
                    # Try to find any PDF that might match (broader search)
                    all_pdfs = list(settings.resumes_dir.glob("*.pdf"))
                    if all_pdfs:
                        # Use most recent as fallback
                        pdf_path = max(all_pdfs, key=lambda p: p.stat().st_mtime)
                        logger.warning(f"Using most recent PDF as fallback: {pdf_path}")
                    else:
                        raise HTTPException(
                            status_code=404,
                            detail=f"Resume PDF not found. pdf_path is None and no matching PDF found in {settings.resumes_dir}"
                        )
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Resume PDF not found (pdf_path is None and job not found)"
                )
        else:
            raise HTTPException(
                status_code=404,
                detail="Resume PDF not found (pdf_path is None and no job_id)"
            )
    
    # #region agent log
    _debug_log({"location": "resumes.py:download_resume_by_id:before_exists_check", "message": "before_exists_check", "data": {"resume_id": resume_id, "pdf_path_str": str(pdf_path) if pdf_path else None, "exists": pdf_path.exists() if pdf_path else False}, "sessionId": "debug-session", "hypothesisId": "C,D,E", "runId": "post-fix"})
    # #endregion
    if not pdf_path.exists():
        # Fallback: PDFs may live under backend/data/resumes when backend runs from backend dir or DB is there
        backend_dir = Path(__file__).resolve().parent.parent.parent.parent
        fallback_resumes_dir = backend_dir / "data" / "resumes"
        fallback_path = fallback_resumes_dir / pdf_path.name if pdf_path else None
        if fallback_path and fallback_path.exists():
            pdf_path = fallback_path
            logger.info(f"Serving resume from fallback dir: {pdf_path}")
            # #region agent log
            _debug_log({"location": "resumes.py:download_resume_by_id:fallback_used", "message": "fallback_used", "data": {"resume_id": resume_id, "served_path": str(pdf_path)}, "sessionId": "debug-session", "runId": "post-fix"})
            # #endregion
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Resume file not found at: {pdf_path}. Checked: {pdf_path.resolve()}"
            )
    
    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        filename=pdf_path.name
    )


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


@router.get("/{resume_id}/info")
async def get_resume_info(
    resume_id: int,
    db: AsyncSession = Depends(get_database)
):
    """Get resume info for debugging."""
    from pathlib import Path
    from app.config import settings
    
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Check file existence
    pdf_exists = False
    pdf_path_checked = None
    if resume.pdf_path:
        # Filename only; resolve against single base
        pdf_path_checked = str(settings.resumes_dir / Path(resume.pdf_path).name)
        pdf_exists = Path(pdf_path_checked).exists()
    
    return {
        "resume_id": resume.id,
        "job_id": resume.job_id,
        "pdf_path": resume.pdf_path,
        "pdf_path_checked": pdf_path_checked,
        "pdf_exists": pdf_exists,
        "cloud_url": resume.cloud_url,
        "resumes_dir": str(settings.resumes_dir),
        "download_url": f"/api/resumes/{resume.id}/download" if resume.pdf_path or resume.cloud_url else None
    }


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: int,
    db: AsyncSession = Depends(get_database)
):
    """Delete a resume."""
    from sqlalchemy import delete
    
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Use delete statement for async SQLAlchemy
    await db.execute(delete(Resume).where(Resume.id == resume_id))
    await db.commit()
    
    return {"success": True}
