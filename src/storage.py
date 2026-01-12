"""
SQLite database storage for job postings and resumes.
Handles persistence, deduplication, and querying.
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import pandas as pd
from rich.console import Console

from src.llm_parser import ParsedJob

logger = logging.getLogger(__name__)
console = Console()


class JobDatabase:
    """
    SQLite database manager for job postings and resumes.
    
    Provides CRUD operations, deduplication, filtering,
    and export functionality.
    """
    
    def __init__(self, db_path: str = "data/jobs.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access
        self.cursor = self.conn.cursor()
        
        self._create_tables()
        logger.info(f"Database initialized: {db_path}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def _create_tables(self):
        """Create database tables if they don't exist."""
        # Jobs table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                remote BOOLEAN,
                employment_type TEXT,
                salary TEXT,
                yoe_required INTEGER DEFAULT 0,
                required_skills TEXT,
                nice_to_have_skills TEXT,
                education TEXT,
                responsibilities TEXT,
                qualifications TEXT,
                benefits TEXT,
                job_summary TEXT,
                apply_url TEXT,
                source_domain TEXT,
                relevance_score INTEGER DEFAULT 0,
                applied BOOLEAN DEFAULT FALSE,
                saved BOOLEAN DEFAULT FALSE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Resumes table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                job_title TEXT,
                company TEXT,
                job_url TEXT,
                resume_location TEXT,
                selected_projects TEXT,
                tex_path TEXT,
                pdf_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES jobs(id)
            )
        """)
        
        # Unextracted jobs table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS unextracted_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                snippet TEXT,
                source_domain TEXT,
                extraction_methods_attempted TEXT,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for common queries
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_company ON jobs(company)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_yoe ON jobs(yoe_required)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_score ON jobs(relevance_score)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_applied ON jobs(applied)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_resume_job ON resumes(job_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_unextracted_url ON unextracted_jobs(url)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_unextracted_retry ON unextracted_jobs(retry_count)")
        
        self.conn.commit()
        logger.debug("Database tables created/verified")
    
    def save_job(self, job: ParsedJob, relevance_score: int = 0) -> bool:
        """
        Save a job to the database.
        
        Uses INSERT OR IGNORE to skip duplicates (by URL).
        
        Args:
            job: ParsedJob object to save
            relevance_score: Calculated relevance score
            
        Returns:
            True if saved, False if duplicate or error
        """
        try:
            self.cursor.execute("""
                INSERT OR IGNORE INTO jobs (
                    url, title, company, location, remote, employment_type,
                    salary, yoe_required, required_skills, nice_to_have_skills,
                    education, responsibilities, qualifications, benefits,
                    job_summary, apply_url, source_domain, relevance_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.source_url,
                job.job_title,
                job.company,
                job.location,
                job.remote,
                job.employment_type,
                job.salary_range,
                job.yoe_required,
                json.dumps(job.required_skills),
                json.dumps(job.nice_to_have_skills),
                job.education,
                json.dumps(job.responsibilities),
                json.dumps(job.qualifications),
                json.dumps(job.benefits),
                job.job_summary,
                job.apply_url,
                job.source_domain,
                relevance_score
            ))
            
            self.conn.commit()
            
            if self.cursor.rowcount > 0:
                logger.debug(f"Saved: {job.job_title} @ {job.company}")
                return True
            else:
                logger.debug(f"Skipped duplicate: {job.source_url}")
                return False
                
        except sqlite3.Error as e:
            logger.error(f"Database error saving job: {e}")
            return False
    
    def save_batch(
        self,
        jobs: List[Tuple[ParsedJob, int]]
    ) -> Tuple[int, int]:
        """
        Save multiple jobs to the database.
        
        Args:
            jobs: List of (ParsedJob, relevance_score) tuples
            
        Returns:
            Tuple of (saved_count, skipped_count)
        """
        saved = 0
        skipped = 0
        
        for job, score in jobs:
            if self.save_job(job, score):
                saved += 1
            else:
                skipped += 1
        
        logger.info(f"Batch save: {saved} saved, {skipped} skipped")
        return saved, skipped
    
    def get_jobs(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query jobs with optional filters.
        
        Args:
            filters: Dict with filter options:
                - max_yoe: Maximum years of experience
                - min_score: Minimum relevance score
                - company: Company name (partial match)
                - location: Location (partial match)
                - remote: Boolean for remote jobs
                - applied: Boolean for applied status
                - saved: Boolean for saved status
            limit: Maximum number of results
            
        Returns:
            List of job dictionaries
        """
        query = "SELECT * FROM jobs WHERE 1=1"
        params = []
        
        if filters:
            if "max_yoe" in filters:
                query += " AND yoe_required <= ?"
                params.append(filters["max_yoe"])
            
            if "min_score" in filters:
                query += " AND relevance_score >= ?"
                params.append(filters["min_score"])
            
            if "company" in filters:
                query += " AND company LIKE ?"
                params.append(f"%{filters['company']}%")
            
            if "location" in filters:
                query += " AND location LIKE ?"
                params.append(f"%{filters['location']}%")
            
            if "remote" in filters:
                query += " AND remote = ?"
                params.append(filters["remote"])
            
            if "applied" in filters:
                query += " AND applied = ?"
                params.append(filters["applied"])
            
            if "saved" in filters:
                query += " AND saved = ?"
                params.append(filters["saved"])
        
        query += " ORDER BY relevance_score DESC, created_at DESC LIMIT ?"
        params.append(limit)
        
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        
        # Convert to list of dicts
        jobs = []
        for row in rows:
            job = dict(row)
            # Parse JSON fields
            for field in ["required_skills", "nice_to_have_skills", "responsibilities", "qualifications", "benefits"]:
                if job.get(field):
                    try:
                        job[field] = json.loads(job[field])
                    except json.JSONDecodeError:
                        job[field] = []
            jobs.append(job)
        
        return jobs
    
    def get_job_by_id(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get a single job by ID."""
        self.cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = self.cursor.fetchone()
        if row:
            job = dict(row)
            for field in ["required_skills", "nice_to_have_skills", "responsibilities", "qualifications", "benefits"]:
                if job.get(field):
                    try:
                        job[field] = json.loads(job[field])
                    except json.JSONDecodeError:
                        job[field] = []
            return job
        return None
    
    def update_job(self, job_id: int, updates: Dict[str, Any]) -> bool:
        """Update job fields."""
        if not updates:
            return False
        
        updates["updated_at"] = datetime.now().isoformat()
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [job_id]
        
        try:
            self.cursor.execute(
                f"UPDATE jobs SET {set_clause} WHERE id = ?",
                values
            )
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Update error: {e}")
            return False
    
    def mark_applied(self, job_id: int) -> bool:
        """Mark a job as applied."""
        return self.update_job(job_id, {"applied": True})
    
    def mark_saved(self, job_id: int) -> bool:
        """Mark a job as saved."""
        return self.update_job(job_id, {"saved": True})
    
    def add_note(self, job_id: int, note: str) -> bool:
        """Add a note to a job."""
        return self.update_job(job_id, {"notes": note})
    
    def delete_job(self, job_id: int) -> bool:
        """Delete a job by ID."""
        try:
            self.cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Delete error: {e}")
            return False
    
    # Resume methods
    def save_resume(self, resume_data: Dict[str, Any]) -> int:
        """Save generated resume to database."""
        projects = resume_data.get("selected_projects", [])
        if isinstance(projects, list):
            projects = json.dumps(projects)
        
        try:
            self.cursor.execute("""
                INSERT INTO resumes (
                    job_id, job_title, company, job_url, 
                    resume_location, selected_projects, tex_path, pdf_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                resume_data.get("job_id"),
                resume_data.get("job_title"),
                resume_data.get("company"),
                resume_data.get("job_url"),
                resume_data.get("resume_location"),
                projects,
                resume_data.get("tex_path"),
                resume_data.get("pdf_path")
            ))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Error saving resume: {e}")
            return -1
    
    def get_resume_for_job(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get resume linked to a job."""
        self.cursor.execute("SELECT * FROM resumes WHERE job_id = ?", (job_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_resumes(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all generated resumes with job info."""
        self.cursor.execute("""
            SELECT r.*, j.relevance_score 
            FROM resumes r 
            LEFT JOIN jobs j ON r.job_id = j.id
            ORDER BY r.created_at DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_resumes_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all resumes for display."""
        self.cursor.execute("""
            SELECT 
                r.id,
                r.job_title,
                r.company,
                r.job_url,
                r.resume_location,
                r.selected_projects,
                r.tex_path,
                r.pdf_path,
                r.created_at,
                j.relevance_score
            FROM resumes r
            LEFT JOIN jobs j ON r.job_id = j.id
            ORDER BY r.created_at DESC
        """)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def export_csv(
        self,
        filepath: str,
        filters: Optional[Dict[str, Any]] = None
    ):
        """Export jobs to CSV file."""
        jobs = self.get_jobs(filters, limit=10000)
        
        if not jobs:
            logger.warning("No jobs to export")
            return
        
        df = pd.DataFrame(jobs)
        
        # Convert list columns to strings for CSV
        for col in ["required_skills", "nice_to_have_skills", "responsibilities", "qualifications", "benefits"]:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
        
        df.to_csv(filepath, index=False)
        logger.info(f"Exported {len(jobs)} jobs to {filepath}")
        console.print(f"[green]Exported {len(jobs)} jobs to {filepath}[/green]")
    
    def get_new_jobs_since(self, since_timestamp: str) -> List[Dict[str, Any]]:
        """
        Get jobs created after a specific timestamp.
        
        Args:
            since_timestamp: ISO format timestamp string
            
        Returns:
            List of job dictionaries
        """
        query = "SELECT * FROM jobs WHERE created_at > ? ORDER BY relevance_score DESC, created_at DESC"
        self.cursor.execute(query, (since_timestamp,))
        rows = self.cursor.fetchall()
        
        # Convert to list of dicts
        jobs = []
        for row in rows:
            job = dict(row)
            # Parse JSON fields
            for field in ["required_skills", "nice_to_have_skills", "responsibilities", "qualifications", "benefits"]:
                if job.get(field):
                    try:
                        job[field] = json.loads(job[field])
                    except json.JSONDecodeError:
                        job[field] = []
            jobs.append(job)
        
        return jobs
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats = {}
        
        # Total count
        self.cursor.execute("SELECT COUNT(*) FROM jobs")
        stats["total"] = self.cursor.fetchone()[0]
        
        # Applied count
        self.cursor.execute("SELECT COUNT(*) FROM jobs WHERE applied = TRUE")
        stats["applied_count"] = self.cursor.fetchone()[0]
        
        # Saved count
        self.cursor.execute("SELECT COUNT(*) FROM jobs WHERE saved = TRUE")
        stats["saved_count"] = self.cursor.fetchone()[0]
        
        # Resume count
        self.cursor.execute("SELECT COUNT(*) FROM resumes")
        stats["resume_count"] = self.cursor.fetchone()[0]
        
        # Top companies
        self.cursor.execute("""
            SELECT company, COUNT(*) as count 
            FROM jobs 
            GROUP BY company 
            ORDER BY count DESC 
            LIMIT 10
        """)
        stats["by_company"] = [dict(row) for row in self.cursor.fetchall()]
        
        # Top domains
        self.cursor.execute("""
            SELECT source_domain, COUNT(*) as count 
            FROM jobs 
            GROUP BY source_domain 
            ORDER BY count DESC 
            LIMIT 10
        """)
        stats["by_domain"] = [dict(row) for row in self.cursor.fetchall()]
        
        # Average YOE
        self.cursor.execute("SELECT AVG(yoe_required) FROM jobs")
        stats["avg_yoe"] = round(self.cursor.fetchone()[0] or 0, 1)
        
        return stats
    
    def save_unextracted_job(
        self,
        url: str,
        title: Optional[str] = None,
        snippet: Optional[str] = None,
        source_domain: Optional[str] = None,
        methods_attempted: Optional[List[str]] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Save a job that failed extraction to the unextracted_jobs table.
        
        Args:
            url: URL that failed extraction
            title: Job title if available from search snippet
            snippet: Search snippet text
            source_domain: Domain of the job posting
            methods_attempted: List of extraction methods that were tried
            error_message: Error message from last attempt
            
        Returns:
            True if saved, False if duplicate or error
        """
        try:
            methods_str = json.dumps(methods_attempted) if methods_attempted else None
            
            self.cursor.execute("""
                INSERT OR REPLACE INTO unextracted_jobs (
                    url, title, snippet, source_domain, 
                    extraction_methods_attempted, error_message, 
                    retry_count, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 
                    COALESCE((SELECT retry_count FROM unextracted_jobs WHERE url = ?), 0) + 1,
                    CURRENT_TIMESTAMP
                )
            """, (
                url, title, snippet, source_domain,
                methods_str, error_message, url
            ))
            
            self.conn.commit()
            
            if self.cursor.rowcount > 0:
                logger.debug(f"Saved unextracted job: {url}")
                return True
            else:
                return False
                
        except sqlite3.Error as e:
            logger.error(f"Database error saving unextracted job: {e}")
            return False
    
    def get_unextracted_jobs(
        self,
        limit: int = 100,
        max_retries: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get unextracted jobs that can be retried.
        
        Args:
            limit: Maximum number of results
            max_retries: Maximum retry count to include (None = all)
            
        Returns:
            List of unextracted job dictionaries
        """
        query = "SELECT * FROM unextracted_jobs WHERE 1=1"
        params = []
        
        if max_retries is not None:
            query += " AND retry_count < ?"
            params.append(max_retries)
        
        query += " ORDER BY retry_count ASC, created_at DESC LIMIT ?"
        params.append(limit)
        
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        
        jobs = []
        for row in rows:
            job = dict(row)
            # Parse JSON fields
            if job.get("extraction_methods_attempted"):
                try:
                    job["extraction_methods_attempted"] = json.loads(job["extraction_methods_attempted"])
                except json.JSONDecodeError:
                    job["extraction_methods_attempted"] = []
            jobs.append(job)
        
        return jobs
    
    def delete_unextracted_job(self, url: str) -> bool:
        """Delete an unextracted job (e.g., after successful extraction)."""
        try:
            self.cursor.execute("DELETE FROM unextracted_jobs WHERE url = ?", (url,))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Delete error: {e}")
            return False
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.debug("Database connection closed")
