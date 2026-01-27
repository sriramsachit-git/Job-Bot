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
        self._migrate_schema()
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
        
        # Pre-filtered jobs table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS pre_filtered_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                snippet TEXT,
                source_domain TEXT,
                filter_reason TEXT,
                filter_details TEXT,
                raw_content_preview TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Skill frequency table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS skill_frequency (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name TEXT NOT NULL,
                job_title_category TEXT NOT NULL,
                times_seen INTEGER DEFAULT 1,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(skill_name, job_title_category)
            )
        """)
        
        # Resume changes table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS resume_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER NOT NULL,
                job_id INTEGER NOT NULL,
                location_used TEXT,
                skills_added TEXT,
                projects_selected TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (resume_id) REFERENCES resumes(id),
                FOREIGN KEY (job_id) REFERENCES jobs(id)
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
    
    def _migrate_schema(self):
        """
        Migrate database schema to add missing columns.
        Handles cases where existing databases don't have newer columns.
        """
        try:
            # Check if jobs table exists
            self.cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='jobs'
            """)
            if not self.cursor.fetchone():
                logger.debug("Jobs table doesn't exist yet, skipping migration")
                return
            
            # Get existing columns
            self.cursor.execute("PRAGMA table_info(jobs)")
            columns = {row[1] for row in self.cursor.fetchall()}
            logger.debug(f"Existing columns in jobs table: {sorted(columns)}")
            
            # Handle salary column migration
            # The code expects 'salary' but older databases may have 'salary_range'
            if 'salary' not in columns:
                logger.warning("Migrating: Adding missing 'salary' column to jobs table")
                try:
                    # Add the salary column
                    self.cursor.execute("ALTER TABLE jobs ADD COLUMN salary TEXT")
                    
                    # If salary_range exists, copy its data to salary
                    if 'salary_range' in columns:
                        logger.info("Migrating data from 'salary_range' to 'salary'")
                        self.cursor.execute("""
                            UPDATE jobs 
                            SET salary = salary_range 
                            WHERE salary IS NULL AND salary_range IS NOT NULL
                        """)
                        logger.info("✓ Data migrated from salary_range to salary")
                    
                    self.conn.commit()
                    logger.info("✓ Migration complete: 'salary' column added successfully")
                    
                    # Verify the column was added
                    self.cursor.execute("PRAGMA table_info(jobs)")
                    columns_after = {row[1] for row in self.cursor.fetchall()}
                    if 'salary' in columns_after:
                        logger.info("✓ Verified: 'salary' column exists after migration")
                    else:
                        logger.error("✗ Migration failed: 'salary' column still missing after ALTER TABLE")
                except sqlite3.Error as alter_error:
                    logger.error(f"Failed to add 'salary' column: {alter_error}")
                    self.conn.rollback()
                    raise
            else:
                logger.debug("'salary' column already exists, no migration needed")
        except sqlite3.Error as e:
            logger.error(f"Error during schema migration: {e}", exc_info=True)
            # Don't raise - allow the database to continue functioning
            # But log the error so we know what went wrong
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_prefilter_reason ON pre_filtered_jobs(filter_reason)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_skill_name ON skill_frequency(skill_name)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_skill_category ON skill_frequency(job_title_category)")
        
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
            query += " AND retry_count <= ?"
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
    
    def save_pre_filtered_job(self, url: str, title: str = None, snippet: str = None,
                              source_domain: str = None, filter_reason: str = None,
                              filter_details: str = None, raw_content: str = None) -> bool:
        """Save a job filtered before LLM parsing."""
        try:
            content_preview = raw_content[:500] if raw_content else None
            self.cursor.execute("""
                INSERT OR IGNORE INTO pre_filtered_jobs 
                (url, title, snippet, source_domain, filter_reason, filter_details, raw_content_preview)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (url, title, snippet, source_domain, filter_reason, filter_details, content_preview))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error saving pre-filtered job: {e}")
            return False
    
    def get_pre_filtered_jobs(self, reason: str = None, limit: int = 100) -> List[Dict]:
        """Get pre-filtered jobs, optionally by reason."""
        query = "SELECT * FROM pre_filtered_jobs WHERE 1=1"
        params = []
        if reason:
            query += " AND filter_reason = ?"
            params.append(reason)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_pre_filter_stats(self) -> Dict:
        """Get pre-filter statistics."""
        self.cursor.execute("""
            SELECT filter_reason, COUNT(*) as count
            FROM pre_filtered_jobs GROUP BY filter_reason
        """)
        return {"by_reason": [dict(row) for row in self.cursor.fetchall()]}
    
    def normalize_job_title_category(self, title: str) -> str:
        """Normalize job title to category."""
        title_lower = title.lower()
        if 'data scientist' in title_lower:
            return 'Data Scientist'
        elif 'machine learning' in title_lower or 'ml engineer' in title_lower:
            return 'ML Engineer'
        elif 'ai engineer' in title_lower or 'artificial intelligence' in title_lower:
            return 'AI Engineer'
        elif 'applied scientist' in title_lower:
            return 'Applied Scientist'
        elif 'research scientist' in title_lower or 'research engineer' in title_lower:
            return 'Research Scientist'
        elif 'data engineer' in title_lower:
            return 'Data Engineer'
        elif 'mlops' in title_lower or 'ml ops' in title_lower:
            return 'MLOps Engineer'
        else:
            return 'Other'
    
    def save_skill_frequencies(self, skills: List[str], job_title: str) -> None:
        """Save/update skill frequencies for a job title category."""
        category = self.normalize_job_title_category(job_title)
        
        for skill in skills:
            skill_normalized = skill.lower().strip()
            if not skill_normalized:
                continue
            
            try:
                self.cursor.execute("""
                    INSERT INTO skill_frequency (skill_name, job_title_category, times_seen, last_seen)
                    VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(skill_name, job_title_category) DO UPDATE SET
                        times_seen = times_seen + 1,
                        last_seen = CURRENT_TIMESTAMP
                """, (skill_normalized, category))
            except Exception as e:
                logger.error(f"Error saving skill frequency: {e}")
        
        self.conn.commit()
    
    def get_top_skills_by_category(self, category: str = None, limit: int = 50) -> List[Dict]:
        """Get top skills, optionally filtered by job category."""
        query = "SELECT skill_name, job_title_category, times_seen, last_seen FROM skill_frequency"
        params = []
        
        if category:
            query += " WHERE job_title_category = ?"
            params.append(category)
        
        query += " ORDER BY times_seen DESC LIMIT ?"
        params.append(limit)
        
        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_skill_distribution(self, skill_name: str) -> List[Dict]:
        """Get distribution of a skill across job categories."""
        self.cursor.execute("""
            SELECT job_title_category, times_seen 
            FROM skill_frequency 
            WHERE skill_name = ?
            ORDER BY times_seen DESC
        """, (skill_name.lower(),))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_skill_stats_summary(self) -> Dict:
        """Get overall skill tracking statistics."""
        self.cursor.execute("SELECT COUNT(DISTINCT skill_name) as unique_skills FROM skill_frequency")
        unique_skills = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT SUM(times_seen) as total_occurrences FROM skill_frequency")
        total_occurrences = self.cursor.fetchone()[0]
        
        self.cursor.execute("""
            SELECT job_title_category, COUNT(*) as skill_count, SUM(times_seen) as total
            FROM skill_frequency GROUP BY job_title_category ORDER BY total DESC
        """)
        by_category = [dict(row) for row in self.cursor.fetchall()]
        
        return {
            "unique_skills": unique_skills,
            "total_occurrences": total_occurrences,
            "by_category": by_category
        }
    
    def save_resume_changes(self, resume_id: int, job_id: int, location: str,
                            skills_added: List[str], projects: List[str]) -> None:
        """Save changes made to a resume."""
        try:
            self.cursor.execute("""
                INSERT INTO resume_changes (resume_id, job_id, location_used, skills_added, projects_selected)
                VALUES (?, ?, ?, ?, ?)
            """, (resume_id, job_id, location, json.dumps(skills_added), json.dumps(projects)))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error saving resume changes: {e}")
    
    def get_frequently_added_skills(self, limit: int = 20) -> List[Dict]:
        """Get skills most frequently added to resumes from JDs."""
        self.cursor.execute("SELECT skills_added FROM resume_changes WHERE skills_added IS NOT NULL")
        
        skill_counts = {}
        for row in self.cursor.fetchall():
            skills = json.loads(row[0]) if row[0] else []
            for skill in skills:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"skill": s, "times_added": c} for s, c in sorted_skills[:limit]]
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.debug("Database connection closed")
