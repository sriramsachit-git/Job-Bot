"""
Script to fix resume URLs for existing resumes in the database.
Updates job.resume_url to use the resume_id-based endpoint.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from backend.app.database import get_async_session
from backend.app.models.job import Job
from backend.app.models.resume import Resume


async def fix_resume_urls():
    """Update resume_url for all jobs that have resumes."""
    async for db in get_async_session():
        try:
            # Get all jobs with resume_id
            result = await db.execute(
                select(Job).where(Job.resume_id.isnot(None))
            )
            jobs = result.scalars().all()
            
            print(f"Found {len(jobs)} jobs with resumes")
            
            updated = 0
            for job in jobs:
                # Get the resume
                resume_result = await db.execute(
                    select(Resume).where(Resume.id == job.resume_id)
                )
                resume = resume_result.scalar_one_or_none()
                
                if not resume:
                    print(f"  Job {job.id}: Resume {job.resume_id} not found")
                    continue
                
                # Update resume_url
                if resume.cloud_url:
                    new_url = resume.cloud_url
                elif resume.pdf_path:
                    new_url = f"/api/resumes/{resume.id}/download"
                else:
                    print(f"  Job {job.id}: No pdf_path or cloud_url")
                    continue
                
                if job.resume_url != new_url:
                    job.resume_url = new_url
                    updated += 1
                    print(f"  Job {job.id}: Updated resume_url to {new_url}")
            
            await db.commit()
            print(f"\nUpdated {updated} jobs")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
        finally:
            break


if __name__ == "__main__":
    asyncio.run(fix_resume_urls())
