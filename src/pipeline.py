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
from src.usage_tracker import UsageTracker
from src.pre_filters import PreParseFilter

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
        self.pre_filter = PreParseFilter(max_yoe=USER_PROFILE.get("max_yoe", 5))
        self.usage_tracker = None
        
        console.print("[green]✓ Pipeline initialized successfully[/green]\n")
    
    def run(
        self,
        keywords: List[str],
        sites: Optional[List[str]] = None,
        num_results: int = 50,
        date_restrict: str = "d1",
        min_score: int = 30,
        per_site: Optional[int] = None,
        comprehensive: bool = False
    ) -> Dict[str, Any]:
        """
        Run the complete job search pipeline.
        
        Args:
            keywords: Job title keywords to search
            sites: Job board sites to search (default: DEFAULT_JOB_SITES)
            num_results: Maximum search results
            date_restrict: Date filter ("d1"=day, "w1"=week, "m1"=month)
            min_score: Minimum relevance score to save
            per_site: If set, search each site individually with N results per site
            comprehensive: If True, search each keyword × each site (matrix search)
            
        Returns:
            Summary dict with pipeline statistics
        """
        # Initialize usage tracker
        run_type = "comprehensive" if comprehensive else ("per_site" if per_site else "standard")
        self.usage_tracker = UsageTracker(run_type=run_type)
        
        summary = {
            "searched": 0,
            "extracted": 0,
            "pre_filtered": 0,
            "pre_filter_reasons": {},
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
            
            search_results = []
            search_usage_stats = None
            
            if comprehensive:
                # Comprehensive search: each keyword × each site
                search_results, search_usage_stats = self.searcher.search_all_comprehensive(
                    keywords=keywords,
                    sites=sites or DEFAULT_JOB_SITES,
                    results_per_query=num_results,
                    date_restrict=date_restrict
                )
                # Log to usage tracker
                if search_usage_stats:
                    self.usage_tracker.set_google_usage(
                        queries_made=search_usage_stats.get("total_queries", 0),
                        queries_successful=search_usage_stats.get("successful_queries", 0),
                        queries_failed=search_usage_stats.get("failed_queries", 0),
                        total_results=search_usage_stats.get("total_results_raw", 0),
                        unique_results=search_usage_stats.get("total_results_unique", 0)
                    )
            elif per_site:
                # Per-site search: one keyword across all sites
                keyword = keywords[0] if keywords else "engineer"
                search_results, search_usage_stats = self.searcher.search_per_site(
                    keyword=keyword,
                    sites=sites or DEFAULT_JOB_SITES,
                    results_per_site=per_site,
                    date_restrict=date_restrict
                )
                # Log to usage tracker
                if search_usage_stats:
                    self.usage_tracker.set_google_usage(
                        queries_made=search_usage_stats.get("total_queries", 0),
                        queries_successful=search_usage_stats.get("successful_queries", 0),
                        queries_failed=search_usage_stats.get("failed_queries", 0),
                        total_results=search_usage_stats.get("total_results_raw", 0),
                        unique_results=search_usage_stats.get("total_results_unique", 0)
                    )
            else:
                # Standard search
                search_results = self.searcher.search_jobs(
                    keywords=keywords,
                    sites=sites or DEFAULT_JOB_SITES,
                    date_restrict=date_restrict,
                    num_results=num_results
                )
                # Track single query (approximate)
                self.usage_tracker.set_google_usage(
                    queries_made=1,
                    queries_successful=1,
                    queries_failed=0,
                    total_results=len(search_results),
                    unique_results=len(search_results)
                )
            
            summary["searched"] = len(search_results)
            console.print(f"[green]Found {len(search_results)} job URLs[/green]\n")
            
            if not search_results:
                console.print("[yellow]No results found. Try different keywords.[/yellow]")
                return summary
            
            # Step 1.5: Early filtering to save credits (before extraction)
            console.print("[bold cyan]🔍 Step 1.5: Early filtering (saving credits)...[/bold cyan]")
            filtered_results = []
            skipped_count = 0
            skipped_reasons = {"keywords": 0, "location": 0}
            
            for result in search_results:
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                display_link = result.get("displayLink", "")
                
                # Check if should skip (checks both keywords and location)
                should_skip = self.filter.should_skip_early(title, snippet, display_link)
                
                if should_skip:
                    skipped_count += 1
                    # Determine reason for skipping
                    if self.filter._title_has_excluded_keywords(title) or \
                       (snippet and any(kw in snippet.lower() for kw in self.filter.exclude_keywords)):
                        skipped_reasons["keywords"] += 1
                    else:
                        skipped_reasons["location"] += 1
                    logger.debug(f"Skipping early: {title}")
                    continue
                
                filtered_results.append(result)
            
            if skipped_count > 0:
                reasons = []
                if skipped_reasons["keywords"] > 0:
                    reasons.append(f"{skipped_reasons['keywords']} excluded keywords")
                if skipped_reasons["location"] > 0:
                    reasons.append(f"{skipped_reasons['location']} non-USA locations")
                reason_text = " + ".join(reasons)
                console.print(f"[yellow]Skipped {skipped_count} jobs early ({reason_text}) - saved credits![/yellow]")
            
            if not filtered_results:
                console.print("[yellow]All jobs filtered out by early filtering.[/yellow]")
                return summary
            
            console.print(f"[green]Proceeding with {len(filtered_results)}/{len(search_results)} jobs[/green]\n")
            
            # Step 2: Extract content
            console.print("[bold cyan]📄 Step 2: Extracting job content...[/bold cyan]")
            urls = [r["link"] for r in filtered_results]
            # Limit batch size to prevent overwhelming the system
            max_extraction_batch = min(50, len(urls))  # Process max 50 at a time
            extracted = self.extractor.extract_batch(
                urls[:max_extraction_batch],
                delay=1.0,
                max_batch_size=max_extraction_batch
            )
            summary["extracted"] = sum(1 for e in extracted if e["success"])
            console.print(f"[green]Extracted {summary['extracted']}/{len(urls)} pages[/green]\n")
            
            # Store failed extractions and track usage
            failed_count = 0
            for i, result in enumerate(extracted):
                # Track extraction in usage tracker
                if self.usage_tracker:
                    self.usage_tracker.log_extraction(
                        url=result["url"],
                        method=result.get("method", "unknown"),
                        success=result.get("success", False),
                        error=result.get("error")
                    )
                
                if not result["success"]:
                    # Use filtered_results instead of search_results
                    search_result = filtered_results[i] if i < len(filtered_results) else {}
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
            
            # Step 3: Pre-parse filtering (NEW)
            if self.pre_filter:
                console.print("[bold cyan]📋 Step 3: Pre-filtering jobs...[/bold cyan]")
                passed_contents, filtered_contents = self.pre_filter.filter_batch(extracted)
                
                summary["pre_filtered"] = len(filtered_contents)
                summary["pre_filter_reasons"] = {}
                
                for item in filtered_contents:
                    reason = item.get("filter_reason", "unknown")
                    summary["pre_filter_reasons"][reason] = summary["pre_filter_reasons"].get(reason, 0) + 1
                    
                    search_result = next((r for r in filtered_results if r["link"] == item["url"]), {})
                    self.db.save_pre_filtered_job(
                        url=item["url"],
                        title=search_result.get("title"),
                        snippet=search_result.get("snippet"),
                        source_domain=self.extractor.get_domain(item["url"]),
                        filter_reason=item.get("filter_reason"),
                        filter_details=item.get("filter_details"),
                        raw_content=item.get("content")
                    )
                
                console.print(f"[yellow]Pre-filtered: {len(filtered_contents)} jobs excluded[/yellow]")
                for reason, count in summary["pre_filter_reasons"].items():
                    console.print(f"  - {reason}: {count}")
                console.print(f"[green]Continuing with {len(passed_contents)} jobs[/green]\n")
                
                if not passed_contents:
                    console.print("[yellow]No jobs passed pre-filtering.[/yellow]")
                    return summary
                
                contents_to_parse = passed_contents
            else:
                console.print("[yellow]Pre-filtering disabled (--no-pre-filter)[/yellow]\n")
                contents_to_parse = extracted
            
            # Step 4: Parse with LLM (renumber from Step 3)
            console.print("[bold cyan]🤖 Step 4: Parsing job details with AI...[/bold cyan]")
            jobs, token_usage = self.parser.parse_batch(contents_to_parse)
            summary["parsed"] = len(jobs)
            console.print(f"[green]Parsed {len(jobs)} job postings[/green]\n")
            
            # Track OpenAI usage
            if self.usage_tracker and token_usage:
                self.usage_tracker.log_openai_request(
                    request_type="job_parsing",
                    success=True,
                    prompt_tokens=token_usage.get("prompt_tokens", 0),
                    completion_tokens=token_usage.get("completion_tokens", 0)
                )
            
            if not jobs:
                console.print("[yellow]No jobs parsed successfully.[/yellow]")
                return summary
            
            # Track skill frequencies
            for job in jobs:
                all_skills = (job.required_skills or []) + (job.nice_to_have_skills or [])
                self.db.save_skill_frequencies(all_skills, job.job_title)
            
            # Step 5: Filter and score
            console.print("[bold cyan]🎯 Step 5: Filtering relevant jobs...[/bold cyan]")
            # Apply location filtering again (in case early filtering missed something)
            filtered = self.filter.filter_jobs(jobs, min_score=min_score, usa_only=True)
            summary["filtered"] = len(filtered)
            console.print(f"[green]Found {len(filtered)} relevant matches (score >= {min_score}, USA/Remote only)[/green]\n")
            
            # Step 6: Save to database
            console.print("[bold cyan]💾 Step 6: Saving to database...[/bold cyan]")
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
            
            # Step 7: Export to CSV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = f"data/jobs_{timestamp}.csv"
            self.db.export_csv(export_path)
            summary["export_path"] = export_path
            
            # Show top matches
            if filtered:
                self._display_top_matches(filtered[:5])
            
            # Finalize usage tracking
            if self.usage_tracker:
                self.usage_tracker.set_pipeline_results(
                    parsed=summary["parsed"],
                    filtered=summary["filtered"],
                    saved=summary["saved"],
                    duplicates=summary["skipped"]
                )
                self.usage_tracker.save_report()
                self.usage_tracker.print_summary()
                summary["usage_report"] = self.usage_tracker.report.to_dict()
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            summary["error"] = str(e)
            if self.usage_tracker:
                self.usage_tracker.log_error("pipeline", str(e))
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
