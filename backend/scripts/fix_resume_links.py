"""
Script to fix resume links for existing resumes.
1. Links resumes to jobs based on job_id
2. Sets resume_url for jobs
3. Checks if PDFs exist and updates pdf_path if found
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

from sqlalchemy import select, update
from app.database import AsyncSessionLocal
from app.models.job import Job
from app.models.resume import Resume
from app.config import settings


async def fix_resume_links():
    """Fix resume links and URLs."""
    async with AsyncSessionLocal() as db:
        try:
            # Get all resumes
            result = await db.execute(select(Resume))
            resumes = result.scalars().all()
            
            print(f"Found {len(resumes)} resumes")
            
            updated_jobs = 0
            found_pdfs = 0
            
            for resume in resumes:
                if not resume.job_id:
                    print(f"  Resume {resume.id}: No job_id, skipping")
                    continue
                
                # Get the job
                job_result = await db.execute(
                    select(Job).where(Job.id == resume.job_id)
                )
                job = job_result.scalar_one_or_none()
                
                if not job:
                    print(f"  Resume {resume.id}: Job {resume.job_id} not found")
                    continue
                
                # Check if PDF exists and update pdf_path if needed
                pdf_path = resume.pdf_path
                if not pdf_path or not Path(pdf_path).exists() if pdf_path else False:
                    # Try to find PDF in resumes directory
                    if resume.job_id:
                        # Look for PDFs matching the job
                        job_result = await db.execute(
                            select(Job).where(Job.id == resume.job_id)
                        )
                        job = job_result.scalar_one_or_none()
                        if job:
                            # Search for PDFs that might match
                            safe_title = "".join(c for c in job.title[:30] if c.isalnum() or c in (' ', '-', '_'))
                            safe_company = "".join(c for c in job.company[:30] if c.isalnum() or c in (' ', '-', '_'))
                            
                            # Try different patterns
                            patterns = [
                                f"*{safe_title}*{safe_company}*.pdf",
                                f"*{safe_company}*.pdf",
                                f"resume_*.pdf"
                            ]
                            
                            pdf_found = False
                            for pattern in patterns:
                                pdf_files = list(settings.resumes_dir.glob(pattern))
                                if pdf_files:
                                    # Use the most recent one
                                    pdf_file = max(pdf_files, key=lambda p: p.stat().st_mtime)
                                    resume.pdf_path = str(pdf_file)
                                    pdf_found = True
                                    found_pdfs += 1
                                    print(f"  Resume {resume.id}: Found PDF: {pdf_file.name}")
                                    break
                            
                            if not pdf_found:
                                print(f"  Resume {resume.id}: No PDF found for job {job.id} ({job.title} at {job.company})")
                
                # Update job with resume link and URL
                needs_update = False
                
                if job.resume_id != resume.id:
                    job.resume_id = resume.id
                    needs_update = True
                
                # Set resume_url
                resume_url = None
                if resume.cloud_url:
                    resume_url = resume.cloud_url
                else:
                    resume_url = f"/api/resumes/{resume.id}/download"
                
                if job.resume_url != resume_url:
                    job.resume_url = resume_url
                    needs_update = True
                
                if needs_update:
                    updated_jobs += 1
                    print(f"  Job {job.id}: Linked to resume {resume.id}, URL: {resume_url}")
            
            await db.commit()
            print(f"\n✓ Updated {updated_jobs} jobs")
            print(f"✓ Found {found_pdfs} PDF files")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()


if __name__ == "__main__":
    asyncio.run(fix_resume_links())
