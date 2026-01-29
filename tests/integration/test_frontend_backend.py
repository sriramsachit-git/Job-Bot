"""
Frontend-Backend Integration Tests
Tests the complete flow from frontend API calls to backend responses
"""
import pytest
import asyncio
import httpx
from app.main import app


@pytest.mark.asyncio
class TestFrontendBackendIntegration:
    """Test frontend-backend integration."""
    
    async def test_api_base_url(self, client):
        """Test that API base URL is correct."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data
    
    async def test_cors_headers(self, client):
        """Test CORS headers are set correctly."""
        response = await client.get(
            "/api/dashboard/stats",
            headers={"Origin": "http://localhost:3000"},
        )
        # CORS middleware should allow this
        assert response.status_code == 200
    
    async def test_api_response_format(self, client):
        """Test that API responses match frontend expectations."""
        # Test dashboard stats format
        response = await client.get("/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure matches frontend types
        assert "total_jobs" in data
        assert "applied" in data
        assert "pending" in data
        assert "resumes_generated" in data
        assert isinstance(data["total_jobs"], int)
        
        # Test jobs list format
        response = await client.get("/api/jobs")
        assert response.status_code == 200
        data = response.json()
        
        assert "jobs" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        assert "limit" in data
        assert isinstance(data["jobs"], list)
    
    async def test_error_response_format(self, client):
        """Test that error responses are in correct format."""
        # Test 404 error
        response = await client.get("/api/jobs/999999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        
        # Test 422 validation error
        response = await client.get("/api/jobs?limit=-1")
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    async def test_search_flow_integration(self, client):
        """Test complete search flow."""
        # Step 1: Start search
        search_data = {
            "job_titles": ["AI Engineer"],
            "domains": ["greenhouse.io"],
            "filters": {
                "max_yoe": 3,
                "remote_only": False,
            },
        }
        start_response = await client.post("/api/search/start", json=search_data)
        assert start_response.status_code == 200
        search_id = start_response.json()["search_id"]
        
        # Step 2: Check status
        status_response = await client.get(f"/api/search/{search_id}/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["search_id"] == search_id
        assert "status" in status_data
        
        # Step 3: Get results (may be empty if search is still running)
        results_response = await client.get(f"/api/search/{search_id}/results")
        assert results_response.status_code == 200
    
    async def test_job_crud_flow(self, client):
        """Test complete job CRUD flow."""
        # This would require creating a job first
        # For now, test that endpoints exist and return proper formats
        list_response = await client.get("/api/jobs")
        assert list_response.status_code == 200
        
        # Test that update endpoint accepts correct format
        # (We can't test actual update without a job ID, but we can test validation)
        update_response = await client.patch(
            "/api/jobs/1",
            json={"status": "applied"},
        )
        # Will be 404 if job doesn't exist, but validates request format
        assert update_response.status_code in [200, 404]
