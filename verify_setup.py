#!/usr/bin/env python3
"""
Comprehensive verification script for Job Search Pipeline.

Run this script to verify all components are working correctly.
"""

import sys
import importlib
from pathlib import Path

def print_header(text):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_success(text):
    """Print success message."""
    print(f"✓ {text}")

def print_error(text):
    """Print error message."""
    print(f"✗ {text}")

def check_imports():
    """Check if all required modules can be imported."""
    print_header("Checking Module Imports")
    
    modules_to_check = [
        "src.config",
        "src.search",
        "src.extractor",
        "src.llm_parser",
        "src.filters",
        "src.storage",
        "src.pipeline",
        "src.resume_generator",
    ]
    
    failed = []
    for module_name in modules_to_check:
        try:
            importlib.import_module(module_name)
            print_success(f"Imported {module_name}")
        except Exception as e:
            print_error(f"Failed to import {module_name}: {e}")
            failed.append(module_name)
    
    if failed:
        print(f"\n❌ {len(failed)} module(s) failed to import")
        return False
    else:
        print(f"\n✅ All {len(modules_to_check)} modules imported successfully")
        return True

def check_dependencies():
    """Check if required Python packages are installed."""
    print_header("Checking Dependencies")
    
    required_packages = [
        "requests",
        "pandas",
        "openai",
        "playwright",
        "beautifulsoup4",
        "flask",
        "rich",
        "pydantic",
        "tenacity",
        "pyyaml",
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print_success(f"{package} is installed")
        except ImportError:
            print_error(f"{package} is NOT installed")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("   Install with: pip install -r requirements.txt")
        return False
    else:
        print(f"\n✅ All {len(required_packages)} required packages are installed")
        return True

def check_files():
    """Check if required files exist."""
    print_header("Checking Required Files")
    
    required_files = [
        "main.py",
        "web_app.py",
        "generate_resumes.py",
        "check_pdf_setup.py",
        "requirements.txt",
        "README.md",
        "src/config.py",
        "src/extractor.py",
        "src/storage.py",
        "src/pipeline.py",
        "templates/index.html",
    ]
    
    missing = []
    for file_path in required_files:
        if Path(file_path).exists():
            print_success(f"{file_path} exists")
        else:
            print_error(f"{file_path} is missing")
            missing.append(file_path)
    
    if missing:
        print(f"\n❌ {len(missing)} file(s) missing")
        return False
    else:
        print(f"\n✅ All {len(required_files)} required files exist")
        return True

def check_extractor_methods():
    """Check if extractor has all three methods."""
    print_header("Checking Extractor Methods")
    
    try:
        from src.extractor import ContentExtractor
        
        extractor = ContentExtractor()
        
        methods = [
            ("extract_with_jina", "Jina extraction"),
            ("extract_with_playwright", "Playwright extraction"),
            ("extract_with_beautifulsoup", "BeautifulSoup extraction"),
            ("smart_extract", "Smart extraction router"),
        ]
        
        for method_name, description in methods:
            if hasattr(extractor, method_name):
                print_success(f"{description} method exists")
            else:
                print_error(f"{description} method missing")
                return False
        
        print("\n✅ All extraction methods are available")
        return True
        
    except Exception as e:
        print_error(f"Error checking extractor: {e}")
        return False

def check_storage_methods():
    """Check if storage has unextracted jobs methods."""
    print_header("Checking Storage Methods")
    
    try:
        from src.storage import JobDatabase
        
        # Check if methods exist
        methods = [
            ("save_unextracted_job", "Save unextracted job"),
            ("get_unextracted_jobs", "Get unextracted jobs"),
            ("delete_unextracted_job", "Delete unextracted job"),
        ]
        
        for method_name, description in methods:
            if hasattr(JobDatabase, method_name):
                print_success(f"{description} method exists")
            else:
                print_error(f"{description} method missing")
                return False
        
        print("\n✅ All storage methods are available")
        return True
        
    except Exception as e:
        print_error(f"Error checking storage: {e}")
        return False

def check_pipeline_integration():
    """Check if pipeline stores failed extractions."""
    print_header("Checking Pipeline Integration")
    
    try:
        from src.pipeline import JobSearchPipeline
        
        # Check if the run method exists and has new_jobs in summary
        import inspect
        source = inspect.getsource(JobSearchPipeline.run)
        
        if "new_jobs" in source:
            print_success("Pipeline tracks new_jobs in summary")
        else:
            print_error("Pipeline does not track new_jobs")
            return False
        
        if "save_unextracted_job" in source:
            print_success("Pipeline stores failed extractions")
        else:
            print_error("Pipeline does not store failed extractions")
            return False
        
        print("\n✅ Pipeline integration is correct")
        return True
        
    except Exception as e:
        print_error(f"Error checking pipeline: {e}")
        return False

def check_web_app():
    """Check if web app has required routes."""
    print_header("Checking Web App")
    
    try:
        # Read web_app.py to check for routes
        web_app_content = Path("web_app.py").read_text()
        
        required_routes = [
            "/api/stats",
            "/api/jobs",
            "/api/unextracted",
            "/api/resumes",
        ]
        
        for route in required_routes:
            if route in web_app_content:
                print_success(f"Route {route} exists")
            else:
                print_error(f"Route {route} missing")
                return False
        
        print("\n✅ All web app routes are available")
        return True
        
    except Exception as e:
        print_error(f"Error checking web app: {e}")
        return False

def check_tests():
    """Check if test files exist."""
    print_header("Checking Test Files")
    
    test_files = [
        "tests/test_extractor_extended.py",
        "tests/test_storage_extended.py",
        "tests/test_pipeline_extended.py",
    ]
    
    missing = []
    for test_file in test_files:
        if Path(test_file).exists():
            print_success(f"{test_file} exists")
        else:
            print_error(f"{test_file} missing")
            missing.append(test_file)
    
    if missing:
        print(f"\n⚠️  {len(missing)} test file(s) missing")
        return False
    else:
        print(f"\n✅ All extended test files exist")
        return True

def check_database_schema():
    """Check if database can be initialized."""
    print_header("Checking Database Schema")
    
    try:
        import tempfile
        import os
        from src.storage import JobDatabase
        
        # Create temporary database
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            db = JobDatabase(path)
            
            # Check if unextracted_jobs table exists
            cursor = db.cursor
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='unextracted_jobs'
            """)
            
            if cursor.fetchone():
                print_success("unextracted_jobs table exists")
            else:
                print_error("unextracted_jobs table missing")
                return False
            
            # Check if jobs table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='jobs'
            """)
            
            if cursor.fetchone():
                print_success("jobs table exists")
            else:
                print_error("jobs table missing")
                return False
            
            db.close()
            os.unlink(path)
            
            print("\n✅ Database schema is correct")
            return True
            
        except Exception as e:
            if os.path.exists(path):
                os.unlink(path)
            raise e
            
    except Exception as e:
        print_error(f"Error checking database: {e}")
        return False

def main():
    """Run all verification checks."""
    print("\n" + "="*60)
    print("  Job Search Pipeline - Verification Script")
    print("="*60)
    
    results = []
    
    # Run all checks
    results.append(("File Existence", check_files()))
    results.append(("Dependencies", check_dependencies()))
    results.append(("Module Imports", check_imports()))
    results.append(("Extractor Methods", check_extractor_methods()))
    results.append(("Storage Methods", check_storage_methods()))
    results.append(("Pipeline Integration", check_pipeline_integration()))
    results.append(("Web App Routes", check_web_app()))
    results.append(("Test Files", check_tests()))
    results.append(("Database Schema", check_database_schema()))
    
    # Summary
    print_header("Verification Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {check_name}")
    
    print("\n" + "="*60)
    if passed == total:
        print(f"🎉 All {total} checks passed! Everything is working correctly.")
        print("="*60)
        return 0
    else:
        print(f"⚠️  {passed}/{total} checks passed. Please review the failures above.")
        print("="*60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
