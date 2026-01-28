#!/usr/bin/env python3
"""
Test script to verify database migrations and operations.
Tests the fixes for missing 'education' and 'extraction_methods_attempted' columns.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.storage import JobDatabase
from src.llm_parser import ParsedJob
import json
import sqlite3

def test_database_migrations():
    """Test that migrations add missing columns."""
    print("=" * 60)
    print("TEST 1: Database Migration")
    print("=" * 60)
    
    # Use a test database
    test_db_path = "data/test_jobs.db"
    
    # Remove test database if it exists
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print(f"✓ Removed existing test database: {test_db_path}")
    
    # Create database instance (this should trigger migrations)
    db = JobDatabase(test_db_path)
    
    # Check if education column exists in jobs table
    db.cursor.execute("PRAGMA table_info(jobs)")
    jobs_columns = {row[1] for row in db.cursor.fetchall()}
    
    print(f"\nJobs table columns: {sorted(jobs_columns)}")
    
    if 'education' in jobs_columns:
        print("✓ PASS: 'education' column exists in jobs table")
    else:
        print("✗ FAIL: 'education' column missing in jobs table")
        return False
    
    # Check if extraction_methods_attempted exists in unextracted_jobs table
    db.cursor.execute("PRAGMA table_info(unextracted_jobs)")
    unextracted_columns = {row[1] for row in db.cursor.fetchall()}
    
    print(f"\nUnextracted_jobs table columns: {sorted(unextracted_columns)}")
    
    if 'extraction_methods_attempted' in unextracted_columns:
        print("✓ PASS: 'extraction_methods_attempted' column exists in unextracted_jobs table")
    else:
        print("✗ FAIL: 'extraction_methods_attempted' column missing in unextracted_jobs table")
        return False
    
    db.close()
    print("\n✓ Migration test passed!")
    return True


def test_save_job_with_education():
    """Test saving a job with education field."""
    print("\n" + "=" * 60)
    print("TEST 2: Save Job with Education Field")
    print("=" * 60)
    
    test_db_path = "data/test_jobs.db"
    db = JobDatabase(test_db_path)
    
    # Create a test ParsedJob with education
    test_job = ParsedJob(
        job_title="Test AI Engineer",
        company="Test Company",
        location="San Francisco, CA",
        remote=True,
        employment_type="Full-time",
        salary_range="$120k - $180k",
        yoe_required=2,
        required_skills=["Python", "Machine Learning"],
        nice_to_have_skills=["AWS", "Docker"],
        education="BS in Computer Science or related field",  # This is the field we're testing
        responsibilities=["Build ML models", "Deploy to production"],
        qualifications=["2+ years experience", "Strong Python skills"],
        benefits=["Health insurance", "401k"],
        job_summary="Test job summary",
        apply_url="https://example.com/apply",
        source_domain="example.com",
        source_url="https://example.com/job/123"
    )
    
    try:
        result = db.save_job(test_job, relevance_score=85)
        if result:
            print("✓ PASS: Successfully saved job with education field")
            
            # Verify the job was saved with education
            db.cursor.execute("""
                SELECT education FROM jobs WHERE url = ?
            """, (test_job.source_url,))
            row = db.cursor.fetchone()
            
            if row and row[0] == test_job.education:
                print(f"✓ PASS: Education field correctly saved: '{row[0]}'")
                return True
            else:
                print(f"✗ FAIL: Education field not saved correctly. Expected: '{test_job.education}', Got: '{row[0] if row else None}'")
                return False
        else:
            print("✗ FAIL: save_job returned False")
            return False
    except Exception as e:
        print(f"✗ FAIL: Error saving job: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_save_unextracted_job():
    """Test saving an unextracted job with extraction_methods_attempted."""
    print("\n" + "=" * 60)
    print("TEST 3: Save Unextracted Job with Extraction Methods")
    print("=" * 60)
    
    test_db_path = "data/test_jobs.db"
    db = JobDatabase(test_db_path)
    
    test_url = "https://example.com/failed-job"
    test_title = "Failed Extraction Test Job"
    test_snippet = "This is a test snippet"
    test_domain = "example.com"
    test_methods = ["jina", "playwright", "beautifulsoup"]
    test_error = "All extraction methods failed"
    
    try:
        # Now test saving unextracted job (skip pre-filtered for this test)
        result = db.save_unextracted_job(
            url=test_url,
            title=test_title,
            snippet=test_snippet,
            source_domain=test_domain,
            methods_attempted=test_methods,
            error_message=test_error
        )
        
        if result:
            print("✓ PASS: Successfully saved unextracted job with extraction_methods_attempted")
            
            # Verify the job was saved with extraction_methods_attempted
            db.cursor.execute("""
                SELECT extraction_methods_attempted FROM unextracted_jobs WHERE url = ?
            """, (test_url,))
            row = db.cursor.fetchone()
            
            if row and row[0]:
                methods_saved = json.loads(row[0])
                if methods_saved == test_methods:
                    print(f"✓ PASS: Extraction methods correctly saved: {methods_saved}")
                    return True
                else:
                    print(f"✗ FAIL: Methods not saved correctly. Expected: {test_methods}, Got: {methods_saved}")
                    return False
            else:
                print(f"✗ FAIL: Extraction methods not saved. Got: {row[0] if row else None}")
                return False
        else:
            print("✗ FAIL: save_unextracted_job returned False")
            return False
    except Exception as e:
        print(f"✗ FAIL: Error saving unextracted job: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_existing_database_migration():
    """Test that existing database gets migrated correctly."""
    print("\n" + "=" * 60)
    print("TEST 4: Existing Database Migration")
    print("=" * 60)
    
    test_db_path = "data/test_migration.db"
    
    # Remove test database if it exists
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    # Create a database without the new columns (simulate old database)
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    
    # Create old schema without education and extraction_methods_attempted
    cursor.execute("""
        CREATE TABLE jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            salary TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE unextracted_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            title TEXT,
            error_message TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    
    print("✓ Created old schema database (without new columns)")
    
    # Now initialize with JobDatabase (should trigger migration)
    db = JobDatabase(test_db_path)
    
    # Check if columns were added
    db.cursor.execute("PRAGMA table_info(jobs)")
    jobs_columns = {row[1] for row in db.cursor.fetchall()}
    
    db.cursor.execute("PRAGMA table_info(unextracted_jobs)")
    unextracted_columns = {row[1] for row in db.cursor.fetchall()}
    
    if 'education' in jobs_columns:
        print("✓ PASS: Migration added 'education' column to existing jobs table")
    else:
        print("✗ FAIL: Migration did not add 'education' column")
        return False
    
    if 'extraction_methods_attempted' in unextracted_columns:
        print("✓ PASS: Migration added 'extraction_methods_attempted' column to existing unextracted_jobs table")
    else:
        print("✗ FAIL: Migration did not add 'extraction_methods_attempted' column")
        return False
    
    db.close()
    print("\n✓ Existing database migration test passed!")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("DATABASE FIX VERIFICATION TESTS")
    print("=" * 60)
    
    results = []
    
    # Test 1: Migration on new database
    results.append(("Migration (New DB)", test_database_migrations()))
    
    # Test 2: Save job with education
    results.append(("Save Job with Education", test_save_job_with_education()))
    
    # Test 3: Save unextracted job
    results.append(("Save Unextracted Job", test_save_unextracted_job()))
    
    # Test 4: Migration on existing database
    results.append(("Migration (Existing DB)", test_existing_database_migration()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    # Cleanup test databases
    test_dbs = ["data/test_jobs.db", "data/test_migration.db"]
    for db_path in test_dbs:
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"✓ Cleaned up: {db_path}")
    
    if passed == total:
        print("\n🎉 All tests passed! Database fixes are working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
