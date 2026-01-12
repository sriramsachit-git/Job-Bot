"""
Extended tests for storage module including unextracted jobs.
"""

import pytest
import tempfile
import os
from src.storage import JobDatabase
from src.llm_parser import ParsedJob


class TestStorageExtended:
    """Extended test cases for JobDatabase class."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        db = JobDatabase(path)
        yield db
        db.close()
        os.unlink(path)
    
    def test_save_unextracted_job(self, temp_db):
        """Test saving an unextracted job."""
        success = temp_db.save_unextracted_job(
            url="https://example.com/job/123",
            title="Software Engineer",
            snippet="Looking for a software engineer...",
            source_domain="example.com",
            methods_attempted=["jina", "playwright", "beautifulsoup"],
            error_message="All methods failed"
        )
        assert success is True
        
        jobs = temp_db.get_unextracted_jobs()
        assert len(jobs) == 1
        assert jobs[0]["url"] == "https://example.com/job/123"
        assert jobs[0]["title"] == "Software Engineer"
        assert jobs[0]["retry_count"] == 1
    
    def test_save_unextracted_job_duplicate(self, temp_db):
        """Test saving duplicate unextracted job increments retry count."""
        temp_db.save_unextracted_job(
            url="https://example.com/job/123",
            methods_attempted=["jina"]
        )
        
        temp_db.save_unextracted_job(
            url="https://example.com/job/123",
            methods_attempted=["playwright"]
        )
        
        jobs = temp_db.get_unextracted_jobs()
        assert len(jobs) == 1
        assert jobs[0]["retry_count"] == 2
    
    def test_get_unextracted_jobs_with_retry_limit(self, temp_db):
        """Test getting unextracted jobs with retry limit."""
        # Add jobs with different retry counts
        temp_db.save_unextracted_job(url="https://example.com/job1", methods_attempted=[])
        temp_db.save_unextracted_job(url="https://example.com/job2", methods_attempted=[])
        temp_db.save_unextracted_job(url="https://example.com/job2", methods_attempted=[])  # retry_count = 2
        
        jobs = temp_db.get_unextracted_jobs(max_retries=1)
        assert len(jobs) == 1
        assert jobs[0]["url"] == "https://example.com/job1"
    
    def test_delete_unextracted_job(self, temp_db):
        """Test deleting an unextracted job."""
        temp_db.save_unextracted_job(url="https://example.com/job/123")
        
        success = temp_db.delete_unextracted_job("https://example.com/job/123")
        assert success is True
        
        jobs = temp_db.get_unextracted_jobs()
        assert len(jobs) == 0
    
    def test_unextracted_job_json_parsing(self, temp_db):
        """Test that methods_attempted is properly parsed from JSON."""
        methods = ["jina", "playwright", "beautifulsoup"]
        temp_db.save_unextracted_job(
            url="https://example.com/job/123",
            methods_attempted=methods
        )
        
        jobs = temp_db.get_unextracted_jobs()
        assert jobs[0]["extraction_methods_attempted"] == methods
