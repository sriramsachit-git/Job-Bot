"""
FastAPI main application.
"""
import sys
from pathlib import Path

# Add project root to Python path so we can import from src
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging

from app.config import settings
from app.database import init_db
from app.api.routes import jobs, search, resumes, dashboard, settings as settings_routes

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation errors."""
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Job Search Pipeline API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


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
    return JSONResponse(
        status_code=404,
        content={"error": "Resume not found"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
