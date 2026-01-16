"""
Usage tracking and reporting for API calls.
Tracks Google Search API queries and OpenAI token usage.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class UsageReport:
    """Comprehensive usage report for a pipeline run."""
    
    # Run metadata
    run_id: str = ""
    started_at: str = ""
    completed_at: str = ""
    run_type: str = ""  # "daily", "custom", "comprehensive", "per_site"
    
    # Google Search API
    google_queries_made: int = 0
    google_queries_successful: int = 0
    google_queries_failed: int = 0
    google_results_total: int = 0
    google_results_unique: int = 0
    google_cost_estimate: float = 0.0  # $5 per 1000 after free tier
    
    # OpenAI API
    openai_requests_made: int = 0
    openai_requests_successful: int = 0
    openai_requests_failed: int = 0
    openai_tokens_prompt: int = 0
    openai_tokens_completion: int = 0
    openai_tokens_total: int = 0
    openai_cost_estimate: float = 0.0
    
    # Extraction stats
    extraction_attempted: int = 0
    extraction_jina_success: int = 0
    extraction_playwright_success: int = 0
    extraction_beautifulsoup_success: int = 0
    extraction_failed: int = 0
    
    # Pipeline results
    jobs_parsed: int = 0
    jobs_filtered: int = 0
    jobs_saved: int = 0
    jobs_duplicates: int = 0
    resumes_generated: int = 0
    
    # Detailed logs
    query_log: list = field(default_factory=list)
    extraction_log: list = field(default_factory=list)
    openai_log: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def calculate_costs(self):
        """Calculate estimated costs."""
        # Google: Free 100/day, then $5 per 1000
        if self.google_queries_made > 100:
            self.google_cost_estimate = ((self.google_queries_made - 100) / 1000) * 5
        
        # OpenAI GPT-4o-mini: $0.15 per 1M input, $0.60 per 1M output
        input_cost = (self.openai_tokens_prompt / 1_000_000) * 0.15
        output_cost = (self.openai_tokens_completion / 1_000_000) * 0.60
        self.openai_cost_estimate = input_cost + output_cost
    
    def total_cost(self) -> float:
        self.calculate_costs()
        return self.google_cost_estimate + self.openai_cost_estimate


class UsageTracker:
    """Tracks API usage across a pipeline run."""
    
    def __init__(self, run_type: str = "custom"):
        self.report = UsageReport(
            run_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
            started_at=datetime.now().isoformat(),
            run_type=run_type
        )
        self.reports_dir = Path("data/usage_reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def log_google_query(self, keyword: str, site: str, success: bool, results_count: int, error: str = None):
        """Log a Google Search API query."""
        self.report.google_queries_made += 1
        if success:
            self.report.google_queries_successful += 1
            self.report.google_results_total += results_count
        else:
            self.report.google_queries_failed += 1
        
        self.report.query_log.append({
            "timestamp": datetime.now().isoformat(),
            "keyword": keyword,
            "site": site,
            "success": success,
            "results_count": results_count,
            "error": error
        })
    
    def log_openai_request(self, request_type: str, success: bool, 
                          prompt_tokens: int = 0, completion_tokens: int = 0, 
                          error: str = None):
        """Log an OpenAI API request."""
        self.report.openai_requests_made += 1
        if success:
            self.report.openai_requests_successful += 1
            self.report.openai_tokens_prompt += prompt_tokens
            self.report.openai_tokens_completion += completion_tokens
            self.report.openai_tokens_total += prompt_tokens + completion_tokens
        else:
            self.report.openai_requests_failed += 1
        
        self.report.openai_log.append({
            "timestamp": datetime.now().isoformat(),
            "type": request_type,
            "success": success,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "error": error
        })
    
    def log_extraction(self, url: str, method: str, success: bool, error: str = None):
        """Log an extraction attempt."""
        self.report.extraction_attempted += 1
        if success:
            if method == "jina":
                self.report.extraction_jina_success += 1
            elif method == "playwright":
                self.report.extraction_playwright_success += 1
            elif method == "beautifulsoup":
                self.report.extraction_beautifulsoup_success += 1
        else:
            self.report.extraction_failed += 1
        
        self.report.extraction_log.append({
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "method": method,
            "success": success,
            "error": error
        })
    
    def log_error(self, component: str, error: str):
        """Log an error."""
        self.report.errors.append({
            "timestamp": datetime.now().isoformat(),
            "component": component,
            "error": error
        })
    
    def set_pipeline_results(self, parsed: int, filtered: int, saved: int, duplicates: int):
        """Set pipeline results."""
        self.report.jobs_parsed = parsed
        self.report.jobs_filtered = filtered
        self.report.jobs_saved = saved
        self.report.jobs_duplicates = duplicates
    
    def set_unique_results(self, unique_count: int):
        """Set unique results count after deduplication."""
        self.report.google_results_unique = unique_count
    
    def set_google_usage(self, queries_made: int, queries_successful: int, queries_failed: int, 
                        total_results: int, unique_results: int):
        """Set Google Search API usage stats."""
        self.report.google_queries_made = queries_made
        self.report.google_queries_successful = queries_successful
        self.report.google_queries_failed = queries_failed
        self.report.google_results_total = total_results
        self.report.google_results_unique = unique_results
    
    def finalize(self) -> UsageReport:
        """Finalize the report."""
        self.report.completed_at = datetime.now().isoformat()
        self.report.calculate_costs()
        return self.report
    
    def save_report(self) -> Path:
        """Save report to JSON file."""
        self.finalize()
        filepath = self.reports_dir / f"usage_{self.report.run_id}.json"
        with open(filepath, 'w') as f:
            json.dump(self.report.to_dict(), f, indent=2)
        logger.info(f"Usage report saved: {filepath}")
        return filepath
    
    def print_summary(self):
        """Print a summary of usage to console."""
        from rich.console import Console
        from rich.table import Table
        
        console = Console()
        self.finalize()
        r = self.report
        
        # Create summary table
        table = Table(title="📊 Usage Report", show_header=True)
        table.add_column("Metric", style="cyan", width=35)
        table.add_column("Value", style="green", justify="right", width=15)
        
        # Google API section
        table.add_row("─── Google Search API ───", "")
        table.add_row("Queries Made", str(r.google_queries_made))
        table.add_row("Queries Successful", str(r.google_queries_successful))
        table.add_row("Queries Failed", str(r.google_queries_failed))
        table.add_row("Total Results (raw)", str(r.google_results_total))
        table.add_row("Unique Results", str(r.google_results_unique))
        table.add_row("Est. Cost", f"${r.google_cost_estimate:.4f}")
        
        # OpenAI section
        table.add_row("─── OpenAI API ───", "")
        table.add_row("Requests Made", str(r.openai_requests_made))
        table.add_row("Requests Successful", str(r.openai_requests_successful))
        table.add_row("Prompt Tokens", f"{r.openai_tokens_prompt:,}")
        table.add_row("Completion Tokens", f"{r.openai_tokens_completion:,}")
        table.add_row("Total Tokens", f"{r.openai_tokens_total:,}")
        table.add_row("Est. Cost", f"${r.openai_cost_estimate:.4f}")
        
        # Extraction section
        table.add_row("─── Extraction ───", "")
        table.add_row("Total Attempted", str(r.extraction_attempted))
        table.add_row("Jina Success", str(r.extraction_jina_success))
        table.add_row("Playwright Success", str(r.extraction_playwright_success))
        table.add_row("BeautifulSoup Success", str(r.extraction_beautifulsoup_success))
        table.add_row("Failed", str(r.extraction_failed))
        
        # Pipeline section
        table.add_row("─── Pipeline Results ───", "")
        table.add_row("Jobs Parsed", str(r.jobs_parsed))
        table.add_row("Jobs Filtered", str(r.jobs_filtered))
        table.add_row("Jobs Saved", str(r.jobs_saved))
        table.add_row("Duplicates Skipped", str(r.jobs_duplicates))
        
        # Total cost
        table.add_row("─── TOTAL ───", "")
        table.add_row("[bold]Total Est. Cost[/bold]", f"[bold]${r.total_cost():.4f}[/bold]")
        
        console.print("\n")
        console.print(table)
        console.print(f"\n[dim]Report saved to: data/usage_reports/usage_{r.run_id}.json[/dim]")


def get_historical_usage(days: int = 7) -> Dict[str, Any]:
    """Get aggregated usage stats for the last N days."""
    reports_dir = Path("data/usage_reports")
    if not reports_dir.exists():
        return {}
    
    from datetime import timedelta
    cutoff = datetime.now() - timedelta(days=days)
    
    totals = {
        "google_queries": 0,
        "openai_tokens": 0,
        "openai_cost": 0.0,
        "google_cost": 0.0,
        "jobs_saved": 0,
        "reports_count": 0
    }
    
    for filepath in reports_dir.glob("usage_*.json"):
        try:
            with open(filepath, 'r') as f:
                report = json.load(f)
            
            # Check if within date range
            started = datetime.fromisoformat(report.get("started_at", ""))
            if started >= cutoff:
                totals["google_queries"] += report.get("google_queries_made", 0)
                totals["openai_tokens"] += report.get("openai_tokens_total", 0)
                totals["openai_cost"] += report.get("openai_cost_estimate", 0)
                totals["google_cost"] += report.get("google_cost_estimate", 0)
                totals["jobs_saved"] += report.get("jobs_saved", 0)
                totals["reports_count"] += 1
        except Exception:
            continue
    
    totals["total_cost"] = totals["openai_cost"] + totals["google_cost"]
    return totals
