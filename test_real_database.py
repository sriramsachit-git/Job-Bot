#!/usr/bin/env python3
"""
Test the actual database to verify migrations work on the real database file.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.storage import JobDatabase
import sqlite3

def test_real_database():
    """Test the actual database file."""
    print("=" * 60)
    print("TESTING REAL DATABASE")
    print("=" * 60)
    
    db_path = "data/jobs.db"
    
    if not Path(db_path).exists():
        print(f"⚠️  Database file not found: {db_path}")
        print("Creating new database...")
    
    # Initialize database (should trigger migrations if needed)
    print(f"\nInitializing database: {db_path}")
    db = JobDatabase(db_path)
    
    # Check columns
    print("\nChecking jobs table columns...")
    db.cursor.execute("PRAGMA table_info(jobs)")
    jobs_columns = {row[1] for row in db.cursor.fetchall()}
    
    print(f"Total columns: {len(jobs_columns)}")
    
    # Check for education column
    if 'education' in jobs_columns:
        print("✓ 'education' column exists")
    else:
        print("✗ 'education' column MISSING - migration may have failed")
        return False
    
    # Check for extraction_methods_attempted in unextracted_jobs
    print("\nChecking unextracted_jobs table columns...")
    db.cursor.execute("PRAGMA table_info(unextracted_jobs)")
    unextracted_columns = {row[1] for row in db.cursor.fetchall()}
    
    print(f"Total columns: {len(unextracted_columns)}")
    
    if 'extraction_methods_attempted' in unextracted_columns:
        print("✓ 'extraction_methods_attempted' column exists")
    else:
        print("✗ 'extraction_methods_attempted' column MISSING - migration may have failed")
        return False
    
    # Check job count
    db.cursor.execute("SELECT COUNT(*) FROM jobs")
    job_count = db.cursor.fetchone()[0]
    print(f"\nTotal jobs in database: {job_count}")
    
    # Check unextracted jobs count
    db.cursor.execute("SELECT COUNT(*) FROM unextracted_jobs")
    unextracted_count = db.cursor.fetchone()[0]
    print(f"Total unextracted jobs: {unextracted_count}")
    
    # Try to query with education field (should not error)
    try:
        db.cursor.execute("SELECT COUNT(*) FROM jobs WHERE education IS NOT NULL")
        jobs_with_education = db.cursor.fetchone()[0]
        print(f"Jobs with education field: {jobs_with_education}")
        print("✓ Can query education field without errors")
    except sqlite3.Error as e:
        print(f"✗ Error querying education field: {e}")
        return False
    
    # Try to query extraction_methods_attempted (should not error)
    try:
        db.cursor.execute("SELECT COUNT(*) FROM unextracted_jobs WHERE extraction_methods_attempted IS NOT NULL")
        unextracted_with_methods = db.cursor.fetchone()[0]
        print(f"Unextracted jobs with methods: {unextracted_with_methods}")
        print("✓ Can query extraction_methods_attempted field without errors")
    except sqlite3.Error as e:
        print(f"✗ Error querying extraction_methods_attempted field: {e}")
        return False
    
    db.close()
    
    print("\n" + "=" * 60)
    print("✓ REAL DATABASE TEST PASSED")
    print("=" * 60)
    print("\nYour database is ready to use!")
    print("The missing columns have been added and migrations are working correctly.")
    
    return True

if __name__ == "__main__":
    success = test_real_database()
    sys.exit(0 if success else 1)
