"""
FastAPI main application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path

from app.config import settings
from app.database import init_db
from app.api.routes import jobs, search, resumes, dashboard, settings as settings_routes

# Create FastAPI app
app = FastAPI(
    title="Job Search Pipeline API",
    description="Web-based job search pipeline with automated resume generation",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs.router)
app.include_router(search.router)
app.include_router(resumes.router)
app.include_router(dashboard.router)
app.include_router(settings_routes.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    await init_db()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Job Search Pipeline API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api/resumes/download/{filename}")
async def download_resume(filename: str):
    """Download resume PDF."""
    resume_path = settings.resumes_dir / filename
    if resume_path.exists():
        return FileResponse(
            str(resume_path),
            media_type="application/pdf",
            filename=filename
        )
    return {"error": "Resume not found"}, 404


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
