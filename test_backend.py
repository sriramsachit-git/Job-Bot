#!/usr/bin/env python3
"""
Test script for backend API.
Tests basic functionality without requiring API keys.
"""
import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    try:
        from app.config import settings
        print("✅ Config imported")
        
        from app.database import Base, engine, get_db
        print("✅ Database imported")
        
        from app.models import Job, Resume, SearchSession, UserSettings
        print("✅ Models imported")
        
        from app.schemas import JobResponse, SearchStart, DashboardStats
        print("✅ Schemas imported")
        
        from app.services import SearchService, ResumeService, StorageService
        print("✅ Services imported")
        
        from app.api.routes import jobs, search, resumes, dashboard, settings as settings_routes
        print("✅ Routes imported")
        
        from app.main import app
        print("✅ Main app imported")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_models():
    """Test database model definitions."""
    print("\nTesting database models...")
    try:
        from app.models.job import Job
        from app.models.resume import Resume
        from app.models.search_session import SearchSession
        
        # Check that models have required fields
        assert hasattr(Job, 'id')
        assert hasattr(Job, 'title')
        assert hasattr(Job, 'company')
        assert hasattr(Job, 'url')
        print("✅ Job model structure correct")
        
        assert hasattr(Resume, 'id')
        assert hasattr(Resume, 'job_id')
        assert hasattr(Resume, 'job_title')
        print("✅ Resume model structure correct")
        
        assert hasattr(SearchSession, 'id')
        assert hasattr(SearchSession, 'job_titles')
        assert hasattr(SearchSession, 'status')
        print("✅ SearchSession model structure correct")
        
        return True
    except Exception as e:
        print(f"❌ Model test error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_database_init():
    """Test database initialization."""
    print("\nTesting database initialization...")
    try:
        from app.database import init_db, engine
        from app.models import Job, Resume, SearchSession
        
        # Test database initialization
        await init_db()
        print("✅ Database initialized")
        
        # Test that tables can be queried (even if empty)
        from sqlalchemy import select
        from app.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Job))
            jobs = result.scalars().all()
            print(f"✅ Can query Job table (found {len(jobs)} jobs)")
            
            result = await session.execute(select(SearchSession))
            sessions = result.scalars().all()
            print(f"✅ Can query SearchSession table (found {len(sessions)} sessions)")
        
        return True
    except Exception as e:
        print(f"❌ Database init error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_schemas():
    """Test Pydantic schemas."""
    print("\nTesting schemas...")
    try:
        from app.schemas.job import JobCreate, JobUpdate, JobResponse
        from app.schemas.search import SearchStart, SearchStatus
        from app.schemas.resume import ResumeCreate
        
        # Test JobCreate
        job_data = {
            "title": "Test Job",
            "company": "Test Company",
            "url": "https://example.com/job",
            "yoe_required": 2
        }
        job = JobCreate(**job_data)
        assert job.title == "Test Job"
        print("✅ JobCreate schema works")
        
        # Test SearchStart
        search_data = {
            "job_titles": ["AI Engineer"],
            "domains": ["greenhouse.io"]
        }
        search = SearchStart(**search_data)
        assert len(search.job_titles) == 1
        print("✅ SearchStart schema works")
        
        return True
    except Exception as e:
        print(f"❌ Schema test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fastapi_app():
    """Test FastAPI app creation."""
    print("\nTesting FastAPI app...")
    try:
        from app.main import app
        
        # Check that app is created
        assert app is not None
        assert app.title == "Job Search Pipeline API"
        print("✅ FastAPI app created")
        
        # Check routes
        routes = [route.path for route in app.routes]
        assert "/" in routes
        assert "/health" in routes
        print(f"✅ App has {len(routes)} routes")
        
        return True
    except Exception as e:
        print(f"❌ FastAPI app test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Backend API Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test imports
    results.append(("Imports", test_imports()))
    
    # Test models
    results.append(("Database Models", test_database_models()))
    
    # Test schemas
    results.append(("Schemas", test_schemas()))
    
    # Test FastAPI app
    results.append(("FastAPI App", test_fastapi_app()))
    
    # Test database (async)
    try:
        results.append(("Database Init", asyncio.run(test_database_init())))
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        results.append(("Database Init", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
