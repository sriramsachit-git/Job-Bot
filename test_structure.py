#!/usr/bin/env python3
"""
Structure test - checks code structure without requiring dependencies.
"""
import os
import sys
from pathlib import Path

def test_file_structure():
    """Test that all required files exist."""
    print("Testing file structure...")
    
    base_path = Path(__file__).parent
    required_files = [
        # Backend
        "backend/app/main.py",
        "backend/app/config.py",
        "backend/app/database.py",
        "backend/app/models/job.py",
        "backend/app/models/resume.py",
        "backend/app/models/search_session.py",
        "backend/app/schemas/job.py",
        "backend/app/schemas/search.py",
        "backend/app/api/routes/jobs.py",
        "backend/app/api/routes/search.py",
        "backend/app/services/search_service.py",
        "backend/requirements.txt",
        "backend/Dockerfile",
        
        # Frontend
        "frontend/package.json",
        "frontend/vite.config.ts",
        "frontend/src/App.tsx",
        "frontend/src/main.tsx",
        "frontend/src/pages/Dashboard.tsx",
        "frontend/src/pages/NewSearch.tsx",
        "frontend/src/components/Dashboard/JobsTable.tsx",
        "frontend/src/components/Search/JobTitleSelector.tsx",
        "frontend/Dockerfile",
        
        # Docker
        "docker-compose.yml",
    ]
    
    missing = []
    for file_path in required_files:
        full_path = base_path / file_path
        if not full_path.exists():
            missing.append(file_path)
        else:
            print(f"  ✅ {file_path}")
    
    if missing:
        print(f"\n❌ Missing files: {missing}")
        return False
    
    print(f"\n✅ All {len(required_files)} required files exist")
    return True


def test_backend_structure():
    """Test backend code structure."""
    print("\nTesting backend structure...")
    
    base_path = Path(__file__).parent / "backend"
    
    # Check models
    models_path = base_path / "app" / "models"
    if models_path.exists():
        model_files = list(models_path.glob("*.py"))
        print(f"  ✅ Found {len(model_files)} model files")
    
    # Check schemas
    schemas_path = base_path / "app" / "schemas"
    if schemas_path.exists():
        schema_files = list(schemas_path.glob("*.py"))
        print(f"  ✅ Found {len(schema_files)} schema files")
    
    # Check routes
    routes_path = base_path / "app" / "api" / "routes"
    if routes_path.exists():
        route_files = list(routes_path.glob("*.py"))
        print(f"  ✅ Found {len(route_files)} route files")
    
    # Check services
    services_path = base_path / "app" / "services"
    if services_path.exists():
        service_files = list(services_path.glob("*.py"))
        print(f"  ✅ Found {len(service_files)} service files")
    
    return True


def test_frontend_structure():
    """Test frontend code structure."""
    print("\nTesting frontend structure...")
    
    base_path = Path(__file__).parent / "frontend"
    
    # Check components
    components_path = base_path / "src" / "components"
    if components_path.exists():
        component_dirs = [d for d in components_path.iterdir() if d.is_dir()]
        print(f"  ✅ Found {len(component_dirs)} component directories")
    
    # Check pages
    pages_path = base_path / "src" / "pages"
    if pages_path.exists():
        page_files = list(pages_path.glob("*.tsx"))
        print(f"  ✅ Found {len(page_files)} page files")
    
    # Check services
    services_path = base_path / "src" / "services"
    if services_path.exists():
        service_files = list(services_path.glob("*.ts"))
        print(f"  ✅ Found {len(service_files)} service files")
    
    return True


def test_code_content():
    """Test that key files have expected content."""
    print("\nTesting code content...")
    
    base_path = Path(__file__).parent
    
    # Test backend main.py has FastAPI app
    main_py = base_path / "backend" / "app" / "main.py"
    if main_py.exists():
        content = main_py.read_text()
        if "FastAPI" in content and "app = FastAPI" in content:
            print("  ✅ main.py has FastAPI app")
        else:
            print("  ❌ main.py missing FastAPI app")
            return False
    
    # Test frontend App.tsx has routing
    app_tsx = base_path / "frontend" / "src" / "App.tsx"
    if app_tsx.exists():
        content = app_tsx.read_text()
        if "BrowserRouter" in content and "Routes" in content:
            print("  ✅ App.tsx has routing")
        else:
            print("  ❌ App.tsx missing routing")
            return False
    
    # Test docker-compose exists
    docker_compose = base_path / "docker-compose.yml"
    if docker_compose.exists():
        content = docker_compose.read_text()
        if "backend:" in content and "frontend:" in content:
            print("  ✅ docker-compose.yml has services")
        else:
            print("  ❌ docker-compose.yml missing services")
            return False
    
    return True


def main():
    """Run all structure tests."""
    print("=" * 60)
    print("Code Structure Test Suite")
    print("=" * 60)
    
    results = []
    
    results.append(("File Structure", test_file_structure()))
    results.append(("Backend Structure", test_backend_structure()))
    results.append(("Frontend Structure", test_frontend_structure()))
    results.append(("Code Content", test_code_content()))
    
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
        print("\n🎉 All structure tests passed!")
        print("\nNote: To test with dependencies, install requirements:")
        print("  Backend: cd backend && pip install -r requirements.txt")
        print("  Frontend: cd frontend && npm install")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
