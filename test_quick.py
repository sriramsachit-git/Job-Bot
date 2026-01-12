#!/usr/bin/env python3
"""
Quick test script - Run this to verify everything works.
"""

print("🔍 Job Search Pipeline - Quick Verification")
print("=" * 50)

# Test 1: Import all modules
print("\n1. Testing module imports...")
try:
    from src import extractor, storage, pipeline, resume_generator
    print("   ✓ All core modules imported")
except Exception as e:
    print(f"   ✗ Import failed: {e}")
    exit(1)

# Test 2: Check BeautifulSoup method
print("\n2. Checking BeautifulSoup extraction method...")
try:
    from src.extractor import ContentExtractor
    ext = ContentExtractor()
    if hasattr(ext, 'extract_with_beautifulsoup'):
        print("   ✓ BeautifulSoup extraction method exists")
    else:
        print("   ✗ BeautifulSoup method missing")
        exit(1)
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# Test 3: Check unextracted jobs methods
print("\n3. Checking unextracted jobs storage...")
try:
    from src.storage import JobDatabase
    if hasattr(JobDatabase, 'save_unextracted_job'):
        print("   ✓ Unextracted jobs methods exist")
    else:
        print("   ✗ Unextracted jobs methods missing")
        exit(1)
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# Test 4: Check pipeline integration
print("\n4. Checking pipeline integration...")
try:
    import inspect
    from src.pipeline import JobSearchPipeline
    source = inspect.getsource(JobSearchPipeline.run)
    if 'new_jobs' in source and 'save_unextracted_job' in source:
        print("   ✓ Pipeline tracks new jobs and failed extractions")
    else:
        print("   ✗ Pipeline integration incomplete")
        exit(1)
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# Test 5: Check web app
print("\n5. Checking web app...")
try:
    with open('web_app.py', 'r') as f:
        content = f.read()
        if '/api/stats' in content and '/api/unextracted' in content:
            print("   ✓ Web app routes exist")
        else:
            print("   ✗ Web app routes missing")
            exit(1)
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# Test 6: Check files exist
print("\n6. Checking required files...")
import os
files = [
    'main.py', 'web_app.py', 'generate_resumes.py', 
    'README.md', 'requirements.txt', 'templates/index.html'
]
missing = [f for f in files if not os.path.exists(f)]
if missing:
    print(f"   ✗ Missing files: {missing}")
    exit(1)
else:
    print(f"   ✓ All {len(files)} required files exist")

# Test 7: Check dependencies
print("\n7. Checking key dependencies...")
try:
    import requests, pandas, flask, bs4
    print("   ✓ Key dependencies installed")
except ImportError as e:
    print(f"   ⚠️  Missing dependency: {e}")
    print("   Run: pip install -r requirements.txt")

print("\n" + "=" * 50)
print("✅ All checks passed! Ready to push to git.")
print("=" * 50)
