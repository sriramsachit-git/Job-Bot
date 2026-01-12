"""
Tests for storage module.
"""

import pytest
import tempfile
import os
from pathlib import Path
from src.storage import JobDatabase
from src.llm_parser import ParsedJob


class TestJobDatabase:
    """Test cases for JobDatabase class."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name
        
        db = JobDatabase(db_path)
        yield db
        
        db.close()
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_init_creates_tables(self, temp_db):
        """Test database initialization creates tables."""
        # Check if jobs table exists by querying it
        temp_db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'")
        assert temp_db.cursor.fetchone() is not None
    
    def test_save_job(self, temp_db):
        """Test saving a job."""
        job = ParsedJob(
            job_title="Test Engineer",
            company="Test Company",
            source_url="https://example.com/job1",
            source_domain="example.com"
        )
        result = temp_db.save_job(job, relevance_score=50)
        assert result is True
    
    def test_save_duplicate_job(self, temp_db):
        """Test saving duplicate job is skipped."""
        job = ParsedJob(
            job_title="Test Engineer",
            company="Test Company",
            source_url="https://example.com/job1",
            source_domain="example.com"
        )
        temp_db.save_job(job)
        result = temp_db.save_job(job)  # Try to save again
        assert result is False  # Should be skipped
    
    def test_get_jobs_empty(self, temp_db):
        """Test getting jobs from empty database."""
        jobs = temp_db.get_jobs()
        assert len(jobs) == 0
    
    def test_get_stats_empty(self, temp_db):
        """Test getting stats from empty database."""
        stats = temp_db.get_stats()
        assert stats["total"] == 0
        assert stats["applied_count"] == 0
