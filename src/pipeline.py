"""
Main pipeline orchestrator.
Coordinates search, extraction, parsing, filtering, and storage.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from src.config import config, DEFAULT_JOB_SITES, USER_PROFILE
from src.search import GoogleJobSearch
from src.extractor import ContentExtractor
from src.llm_parser import JobParser
from src.storage import JobDatabase
from src.filters import JobFilter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)
console = Console()


class JobSearchPipeline:
    """
    Main pipeline orchestrator for job searching.
    
    Coordinates all components:
    1. Google Search API for finding job URLs
    2. Content Extractor for fetching job postings
    3. LLM Parser for extracting structured data
    4. Job Filter for relevance scoring
    5. Database for persistence
    """
    
    def __init__(self):
        """Initialize all pipeline components."""
        console.print("[bold blue]Initializing Job Search Pipeline...[/bold blue]")
        
        # Validate configuration
        config.validate()
        
        # Initialize components
        self.searcher = GoogleJobSearch()
        self.extractor = ContentExtractor()
        self.parser = JobParser()
        self.db = JobDatabase(config.database_path)
        self.filter = JobFilter(USER_PROFILE)
        
        console.print("[green]✓ Pipeline initialized successfully[/green]\n")
    
    def run(
        self,
        keywords: List[str],
        sites: Optional[List[str]] = None,
        num_results: int = 50,
        date_restrict: str = "d1",
        min_score: int = 30
    ) -> Dict[str, Any]:
        """
        Run the complete job search pipeline.
        
        Args:
            keywords: Job title keywords to search
            sites: Job board sites to search (default: DEFAULT_JOB_SITES)
            num_results: Maximum search results
            date_restrict: Date filter ("d1"=day, "w1"=week, "m1"=month)
            min_score: Minimum relevance score to save
            
        Returns:
            Summary dict with pipeline statistics
        """
        summary = {
            "searched": 0,
            "extracted": 0,
            "parsed": 0,
            "filtered": 0,
            "saved": 0,
            "skipped": 0,
            "started_at": datetime.now().isoformat(),
            "new_jobs": []
        }
        
        try:
            # Step 1: Search Google
            console.print("\n[bold cyan]🔍 Step 1: Searching for jobs...[/bold cyan]")
            search_results = self.searcher.search_jobs(
                keywords=keywords,
                sites=sites or DEFAULT_JOB_SITES,
                date_restrict=date_restrict,
                num_results=num_results
            )
            summary["searched"] = len(search_results)
            console.print(f"[green]Found {len(search_results)} job URLs[/green]\n")
            
            if not search_results:
                console.print("[yellow]No results found. Try different keywords.[/yellow]")
                return summary
            
            # Step 2: Extract content
            console.print("[bold cyan]📄 Step 2: Extracting job content...[/bold cyan]")
            urls = [r["link"] for r in search_results]
            extracted = self.extractor.extract_batch(urls)
            summary["extracted"] = sum(1 for e in extracted if e["success"])
            console.print(f"[green]Extracted {summary['extracted']}/{len(urls)} pages[/green]\n")
            
            # Store failed extractions
            failed_count = 0
            for i, result in enumerate(extracted):
                if not result["success"]:
                    search_result = search_results[i] if i < len(search_results) else {}
                    self.db.save_unextracted_job(
                        url=result["url"],
                        title=search_result.get("title"),
                        snippet=search_result.get("snippet"),
                        source_domain=self.extractor.get_domain(result["url"]),
                        methods_attempted=[result.get("method", "unknown")],
                        error_message=result.get("error")
                    )
                    failed_count += 1
            
            if failed_count > 0:
                console.print(f"[yellow]⚠️  {failed_count} failed extractions saved for retry[/yellow]\n")
            
            # Step 3: Parse with LLM
            console.print("[bold cyan]🤖 Step 3: Parsing job details with AI...[/bold cyan]")
            jobs = self.parser.parse_batch(extracted)
            summary["parsed"] = len(jobs)
            console.print(f"[green]Parsed {len(jobs)} job postings[/green]\n")
            
            if not jobs:
                console.print("[yellow]No jobs parsed successfully.[/yellow]")
                return summary
            
            # Step 4: Filter and score
            console.print("[bold cyan]🎯 Step 4: Filtering relevant jobs...[/bold cyan]")
            filtered = self.filter.filter_jobs(jobs, min_score=min_score)
            summary["filtered"] = len(filtered)
            console.print(f"[green]Found {len(filtered)} relevant matches (score >= {min_score})[/green]\n")
            
            # Step 5: Save to database
            console.print("[bold cyan]💾 Step 5: Saving to database...[/bold cyan]")
            # Get timestamp just before saving (with small buffer for safety)
            before_time = datetime.now() - timedelta(seconds=2)
            before_timestamp = before_time.isoformat()
            
            saved, skipped = self.db.save_batch(filtered)
            summary["saved"] = saved
            summary["skipped"] = skipped
            console.print(f"[green]Saved {saved} new jobs, skipped {skipped} duplicates[/green]\n")
            
            # Get newly saved jobs (created after the before_timestamp)
            if saved > 0:
                new_jobs = self.db.get_new_jobs_since(before_timestamp)
                # Limit to the number we actually saved
                summary["new_jobs"] = new_jobs[:saved]
            
            # Step 6: Export to CSV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = f"data/jobs_{timestamp}.csv"
            self.db.export_csv(export_path)
            summary["export_path"] = export_path
            
            # Show top matches
            if filtered:
                self._display_top_matches(filtered[:5])
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            summary["error"] = str(e)
            raise
        
        summary["completed_at"] = datetime.now().isoformat()
        return summary
    
    def run_quick(
        self,
        keywords: List[str],
        num_results: int = 20
    ) -> Dict[str, Any]:
        """Quick search with default settings."""
        return self.run(
            keywords=keywords,
            num_results=num_results,
            date_restrict="d1",
            min_score=25
        )
    
    def run_daily(self) -> Dict[str, Any]:
        """
        Run daily automated job search.
        
        Uses predefined keywords for AI/ML engineering positions.
        """
        keywords = [
            "AI engineer",
            "ML engineer", 
            "machine learning engineer",
            "data scientist",
            "applied scientist"
        ]
        
        console.print("[bold magenta]🚀 Running Daily Job Search[/bold magenta]")
        console.print(f"Keywords: {', '.join(keywords)}")
        console.print(f"Sites: {', '.join(DEFAULT_JOB_SITES[:5])}...\n")
        
        return self.run(
            keywords=keywords,
            sites=DEFAULT_JOB_SITES,
            num_results=50,
            date_restrict="d1",
            min_score=30
        )
    
    def _display_top_matches(self, matches: List[tuple]):
        """Display top job matches in a table."""
        table = Table(title="🎯 Top Matches")
        table.add_column("Score", style="cyan", width=6)
        table.add_column("Title", style="green")
        table.add_column("Company", style="yellow")
        table.add_column("Location")
        table.add_column("YOE", width=4)
        
        for job, score in matches:
            table.add_row(
                str(score),
                job.job_title[:35] + "..." if len(job.job_title) > 35 else job.job_title,
                job.company[:20] + "..." if len(job.company) > 20 else job.company,
                (job.location or "N/A")[:20],
                str(job.yoe_required)
            )
        
        console.print(table)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        return self.db.get_stats()
    
    def export_top_jobs(self, filepath: str, top_n: int = 50):
        """Export top N jobs by relevance score."""
        self.db.export_csv(filepath, filters={"min_score": 30})
    
    def cleanup(self):
        """Clean up resources."""
        self.db.close()
        logger.info("Pipeline cleanup completed")
