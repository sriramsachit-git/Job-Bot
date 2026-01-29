"""
Backend API Integration Tests
Tests all API endpoints for correctness and error handling
"""
import pytest
import asyncio

from app.main import app
from app.models.job import Job
from app.models.resume import Resume
from app.models.search_session import SearchSession
from datetime import datetime


"""
NOTE: DB/session/client fixtures live in `tests/integration/conftest.py`.
"""


@pytest.fixture
async def sample_job(db_session):
    """Create a sample job for testing."""
    job = Job(
        url="https://example.com/job/1",
        title="AI Engineer",
        company="Test Company",
        location="San Francisco, CA",
        remote=True,
        yoe_required=2,
        relevance_score=75,
        status="new",
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)
    return job


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Test health check endpoint."""
    
    async def test_health_check(self, client):
        """Test health endpoint returns 200."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
class TestDashboardAPI:
    """Test dashboard endpoints."""
    
    async def test_get_dashboard_stats_empty(self, client):
        """Test dashboard stats with empty database."""
        response = await client.get("/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_jobs"] == 0
        assert data["applied"] == 0
        assert data["pending"] == 0
        assert data["resumes_generated"] == 0
    
    async def test_get_dashboard_stats_with_data(self, client, sample_job, db_session):
        """Test dashboard stats with data."""
        # Mark job as applied
        sample_job.applied = True
        await db_session.commit()
        
        response = await client.get("/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_jobs"] == 1
        assert data["applied"] == 1
    
    async def test_get_recent_jobs(self, client, sample_job):
        """Test recent jobs endpoint."""
        response = await client.get("/api/dashboard/recent-jobs?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["title"] == "AI Engineer"


@pytest.mark.asyncio
class TestJobsAPI:
    """Test jobs endpoints."""
    
    async def test_get_jobs_empty(self, client):
        """Test getting jobs from empty database."""
        response = await client.get("/api/jobs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["jobs"] == []
        assert data["page"] == 1
    
    async def test_get_jobs_with_data(self, client, sample_job):
        """Test getting jobs with data."""
        response = await client.get("/api/jobs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["jobs"]) >= 1
        assert data["jobs"][0]["title"] == "AI Engineer"
    
    async def test_get_job_by_id(self, client, sample_job):
        """Test getting a specific job."""
        response = await client.get(f"/api/jobs/{sample_job.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_job.id
        assert data["title"] == "AI Engineer"
    
    async def test_get_job_not_found(self, client):
        """Test getting non-existent job."""
        response = await client.get("/api/jobs/999999")
        assert response.status_code == 404
    
    async def test_filter_jobs_by_min_score(self, client, sample_job):
        """Test filtering jobs by minimum score."""
        response = await client.get("/api/jobs?min_score=80")
        assert response.status_code == 200
        data = response.json()
        # Should return empty since sample job has score 75
        assert all(job["relevance_score"] >= 80 for job in data["jobs"])
    
    async def test_filter_jobs_by_max_yoe(self, client, sample_job):
        """Test filtering jobs by max YOE."""
        response = await client.get("/api/jobs?max_yoe=1")
        assert response.status_code == 200
        data = response.json()
        assert all(job["yoe_required"] <= 1 for job in data["jobs"])
    
    async def test_filter_jobs_by_remote(self, client, sample_job):
        """Test filtering jobs by remote status."""
        response = await client.get("/api/jobs?remote=true")
        assert response.status_code == 200
        data = response.json()
        assert all(job["remote"] is True for job in data["jobs"])
    
    async def test_pagination(self, client, db_session):
        """Test pagination."""
        # Create multiple jobs
        for i in range(15):
            job = Job(
                url=f"https://example.com/job/{i}",
                title=f"Job {i}",
                company="Test",
                location="SF",
                relevance_score=50 + i,
            )
            db_session.add(job)
        await db_session.commit()
        
        # Test first page
        response1 = await client.get("/api/jobs?limit=10&offset=0")
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["jobs"]) == 10
        assert data1["page"] == 1
        
        # Test second page
        response2 = await client.get("/api/jobs?limit=10&offset=10")
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["jobs"]) == 5  # Remaining 5 jobs
        assert data2["page"] == 2
    
    async def test_update_job(self, client, sample_job):
        """Test updating a job."""
        update_data = {
            "status": "applied",
            "applied": True,
            "notes": "Applied on 2024-01-01"
        }
        response = await client.patch(f"/api/jobs/{sample_job.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "applied"
        assert data["applied"] is True
        assert data["notes"] == "Applied on 2024-01-01"
    
    async def test_delete_job(self, client, sample_job, db_session):
        """Test deleting a job."""
        job_id = sample_job.id
        response = await client.delete(f"/api/jobs/{job_id}")
        assert response.status_code == 200
        
        # Verify job is deleted
        get_response = await client.get(f"/api/jobs/{job_id}")
        assert get_response.status_code == 404


@pytest.mark.asyncio
class TestSearchAPI:
    """Test search endpoints."""
    
    async def test_start_search(self, client):
        """Test starting a search."""
        search_data = {
            "job_titles": ["AI Engineer", "ML Engineer"],
            "domains": ["greenhouse.io", "lever.co"],
            "filters": {
                "max_yoe": 3,
                "remote_only": False
            }
        }
        response = await client.post("/api/search/start", json=search_data)
        assert response.status_code == 200
        data = response.json()
        assert "search_id" in data
        assert data["status"] == "started"
    
    async def test_get_search_status(self, client):
        """Test getting search status."""
        # First create a search
        search_data = {
            "job_titles": ["AI Engineer"],
            "domains": ["greenhouse.io"]
        }
        create_response = await client.post("/api/search/start", json=search_data)
        search_id = create_response.json()["search_id"]
        
        # Get status
        response = await client.get(f"/api/search/{search_id}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["search_id"] == search_id
        assert "status" in data
    
    async def test_get_search_status_not_found(self, client):
        """Test getting status for non-existent search."""
        response = await client.get("/api/search/999999/status")
        assert response.status_code == 404
    
    async def test_cancel_search(self, client):
        """Test canceling a search."""
        # Create a search
        search_data = {
            "job_titles": ["AI Engineer"],
            "domains": ["greenhouse.io"]
        }
        create_response = await client.post("/api/search/start", json=search_data)
        search_id = create_response.json()["search_id"]
        
        # Cancel it
        response = await client.post(f"/api/search/cancel/{search_id}")
        assert response.status_code == 200


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling."""
    
    async def test_invalid_job_id(self, client):
        """Test invalid job ID format."""
        response = await client.get("/api/jobs/invalid")
        assert response.status_code == 422  # Validation error
    
    async def test_invalid_pagination(self, client):
        """Test invalid pagination parameters."""
        # Negative limit
        response = await client.get("/api/jobs?limit=-1")
        assert response.status_code == 422
        
        # Negative offset
        response = await client.get("/api/jobs?offset=-1")
        assert response.status_code == 422
    
    async def test_missing_required_fields(self, client):
        """Test missing required fields in POST requests."""
        response = await client.post("/api/search/start", json={})
        assert response.status_code == 422  # Validation error
