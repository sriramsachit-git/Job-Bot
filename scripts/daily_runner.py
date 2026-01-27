#!/usr/bin/env python3
"""
Daily Job Search Pipeline Runner

Automated daily job search that:
1. Runs job search at scheduled time (default: 9 AM)
2. Extracts and parses new job postings
3. Generates tailored resumes for top matches
4. Starts web server for viewing results

Usage:
    python daily_runner.py                    # Run once now
    python daily_runner.py --daemon           # Run as daemon (scheduled)
    python daily_runner.py --schedule "09:00" # Custom schedule time
    python daily_runner.py --no-web           # Skip web server
"""

import argparse
import sys
import os
import time
import signal
import subprocess
import threading
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Ensure we can import from src
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.logging import RichHandler

console = Console()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)


class DailyJobSearchRunner:
    """
    Orchestrates the complete daily job search workflow.
    
    Flow:
    1. Search for new jobs (Google Custom Search)
    2. Extract job content (Jina/Playwright/BeautifulSoup)
    3. Parse with LLM (GPT-4o-mini)
    4. Filter by relevance score
    5. Save to database
    6. Generate resumes for top matches
    7. Start web server for viewing
    """
    
    def __init__(
        self,
        schedule_time: str = "09:00",
        auto_resume: bool = True,
        start_web: bool = True,
        web_port: int = 5000,
        open_browser: bool = True,
        min_score: int = 30,
        top_jobs_for_resume: int = 5
    ):
        """
        Initialize the daily runner.
        
        Args:
            schedule_time: Time to run daily (HH:MM format)
            auto_resume: Automatically generate resumes
            start_web: Start web server after run
            web_port: Port for web server
            open_browser: Open browser automatically
            min_score: Minimum relevance score for jobs
            top_jobs_for_resume: Number of top jobs to generate resumes for
        """
        self.schedule_time = schedule_time
        self.auto_resume = auto_resume
        self.start_web = start_web
        self.web_port = web_port
        self.open_browser = open_browser
        self.min_score = min_score
        self.top_jobs_for_resume = top_jobs_for_resume
        
        self.web_process = None
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        console.print("\n[yellow]Received shutdown signal. Cleaning up...[/yellow]")
        self.running = False
        self.stop_web_server()
        sys.exit(0)
    
    def display_banner(self):
        """Display startup banner."""
        banner = """
╔═══════════════════════════════════════════════════════════════╗
║        🤖 AUTOMATED DAILY JOB SEARCH PIPELINE 🤖              ║
║                                                               ║
║   • Searches job boards automatically at scheduled time       ║
║   • Extracts and parses job postings with AI                  ║
║   • Generates tailored resumes for top matches                ║
║   • Provides web dashboard for easy viewing                   ║
╚═══════════════════════════════════════════════════════════════╝
        """
        console.print(banner, style="bold blue")
    
    def run_pipeline(self) -> dict:
        """
        Run the complete job search pipeline.
        
        Returns:
            Summary dictionary with results
        """
        from src.pipeline import JobSearchPipeline
        from src.resume_generator import ResumeGenerator
        from src.config import config
        
        console.print(Panel.fit(
            f"[bold green]🚀 Starting Daily Job Search[/bold green]\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            border_style="green"
        ))
        
        results = {
            "started_at": datetime.now().isoformat(),
            "jobs_found": 0,
            "jobs_saved": 0,
            "resumes_generated": 0,
            "errors": []
        }
        
        pipeline = None
        
        try:
            # Step 1-6: Run job search pipeline
            console.print("\n[bold cyan]═══ PHASE 1: Job Search & Extraction ═══[/bold cyan]\n")
            
            pipeline = JobSearchPipeline()
            summary = pipeline.run_daily()
            
            results["jobs_found"] = summary.get("searched", 0)
            results["jobs_saved"] = summary.get("saved", 0)
            results["new_jobs"] = summary.get("new_jobs", [])
            
            # Display results
            self._display_pipeline_results(summary)
            
            # Step 7: Generate resumes for new jobs
            if self.auto_resume and results["new_jobs"]:
                console.print("\n[bold cyan]═══ PHASE 2: Resume Generation ═══[/bold cyan]\n")
                
                resume_count = self._generate_resumes(
                    results["new_jobs"][:self.top_jobs_for_resume],
                    pipeline.db
                )
                results["resumes_generated"] = resume_count
            
            results["completed_at"] = datetime.now().isoformat()
            results["success"] = True
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            results["errors"].append(str(e))
            results["success"] = False
            import traceback
            traceback.print_exc()
        
        finally:
            if pipeline:
                pipeline.cleanup()
        
        # Display final summary
        self._display_final_summary(results)
        
        return results
    
    def _display_pipeline_results(self, summary: dict):
        """Display pipeline results in a table."""
        table = Table(title="📊 Pipeline Results", show_header=True)
        table.add_column("Metric", style="cyan", width=25)
        table.add_column("Count", style="green", justify="right", width=10)
        
        table.add_row("URLs Found", str(summary.get("searched", 0)))
        table.add_row("Content Extracted", str(summary.get("extracted", 0)))
        table.add_row("Jobs Parsed", str(summary.get("parsed", 0)))
        table.add_row("Relevant Matches", str(summary.get("filtered", 0)))
        table.add_row("New Jobs Saved", str(summary.get("saved", 0)))
        table.add_row("Duplicates Skipped", str(summary.get("skipped", 0)))
        
        console.print(table)
    
    def _generate_resumes(self, jobs: list, db) -> int:
        """Generate resumes for top jobs."""
        try:
            from src.resume_generator import ResumeGenerator
            
            if not jobs:
                console.print("[yellow]No new jobs to generate resumes for.[/yellow]")
                return 0
            
            console.print(f"[green]Generating resumes for top {len(jobs)} jobs...[/green]\n")
            
            generator = ResumeGenerator(
                config_path="data/resume_config.yaml",
                projects_path="data/projects.json"
            )
            
            # Format jobs for generator
            jobs_for_generation = []
            for job in jobs:
                jobs_for_generation.append({
                    'id': job.get('id'),
                    'title': job.get('title', ''),
                    'company': job.get('company', ''),
                    'url': job.get('url', ''),
                    'location': job.get('location'),
                    'required_skills': job.get('required_skills', []),
                    'nice_to_have_skills': job.get('nice_to_have_skills', []),
                    'responsibilities': job.get('responsibilities', []),
                    'yoe_required': job.get('yoe_required', 0),
                    'remote': job.get('remote'),
                    'source_domain': job.get('source_domain', '')
                })
            
            # Generate recommendations
            recommendations = generator.generate_recommendations(jobs_for_generation)
            
            # Auto-select top 3 projects
            recommendations = generator.auto_select_top3(recommendations)
            
            # Generate resumes
            results = generator.generate_resumes(recommendations)
            
            # Save to database
            successful = 0
            for result in results:
                if result["success"]:
                    resume_id = db.save_resume(result)
                    # Save resume changes tracking
                    if resume_id > 0:
                        job_id = result.get("job_id")
                        location = result.get("resume_location")
                        skills_added = result.get("skills_added", [])
                        projects = result.get("selected_projects", [])
                        if job_id:
                            db.save_resume_changes(
                                resume_id=resume_id,
                                job_id=job_id,
                                location=location,
                                skills_added=skills_added,
                                projects=projects
                            )
                    successful += 1
            
            # Display results
            generator.display_results(results)
            
            return successful
            
        except FileNotFoundError as e:
            console.print(f"[red]Resume config not found: {e}[/red]")
            console.print("[dim]Create data/resume_config.yaml and data/projects.json[/dim]")
            return 0
        except Exception as e:
            console.print(f"[red]Resume generation error: {e}[/red]")
            return 0
    
    def _display_final_summary(self, results: dict):
        """Display final summary."""
        console.print("\n")
        
        status = "✅ SUCCESS" if results.get("success") else "❌ FAILED"
        
        panel_content = f"""
[bold]{status}[/bold]

📊 Jobs Found: {results.get('jobs_found', 0)}
💾 Jobs Saved: {results.get('jobs_saved', 0)}
📄 Resumes Generated: {results.get('resumes_generated', 0)}

⏰ Started: {results.get('started_at', 'N/A')[:19]}
⏱️  Completed: {results.get('completed_at', 'N/A')[:19]}
        """
        
        if results.get("errors"):
            panel_content += f"\n⚠️  Errors: {len(results['errors'])}"
        
        console.print(Panel(panel_content, title="📋 Daily Run Summary", border_style="cyan"))
    
    def start_web_server(self):
        """Start the web server in a subprocess."""
        if not self.start_web:
            return
        
        console.print(f"\n[bold cyan]🌐 Starting Web Server on port {self.web_port}...[/bold cyan]")
        
        try:
            # Start web server as subprocess
            self.web_process = subprocess.Popen(
                [sys.executable, "web_app.py", "--host", "0.0.0.0", "--port", str(self.web_port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait a moment for server to start
            time.sleep(2)
            
            if self.web_process.poll() is None:
                console.print(f"[green]✓ Web server running at http://localhost:{self.web_port}[/green]")
                
                # Open browser if requested
                if self.open_browser:
                    console.print("[dim]Opening browser...[/dim]")
                    webbrowser.open(f"http://localhost:{self.web_port}")
            else:
                console.print("[red]✗ Web server failed to start[/red]")
                
        except Exception as e:
            console.print(f"[red]Error starting web server: {e}[/red]")
    
    def stop_web_server(self):
        """Stop the web server."""
        if self.web_process:
            console.print("[yellow]Stopping web server...[/yellow]")
            self.web_process.terminate()
            self.web_process.wait(timeout=5)
            self.web_process = None
    
    def calculate_next_run(self) -> datetime:
        """Calculate the next scheduled run time."""
        now = datetime.now()
        hour, minute = map(int, self.schedule_time.split(":"))
        
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If scheduled time has passed today, schedule for tomorrow
        if next_run <= now:
            next_run += timedelta(days=1)
        
        return next_run
    
    def run_once(self):
        """Run the pipeline once immediately."""
        self.display_banner()
        
        console.print("[bold green]Running pipeline once...[/bold green]\n")
        
        results = self.run_pipeline()
        
        # Start web server
        self.start_web_server()
        
        if self.start_web and self.web_process:
            console.print("\n[bold cyan]Web server is running. Press Ctrl+C to stop.[/bold cyan]")
            try:
                while self.running and self.web_process.poll() is None:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                self.stop_web_server()
        
        return results
    
    def run_daemon(self):
        """Run as a daemon with scheduled execution."""
        self.display_banner()
        
        console.print(f"[bold green]Starting daemon mode...[/bold green]")
        console.print(f"[cyan]Scheduled time: {self.schedule_time} daily[/cyan]")
        
        # Start web server immediately
        self.start_web_server()
        
        while self.running:
            next_run = self.calculate_next_run()
            
            console.print(f"\n[dim]Next run scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
            
            # Wait until next scheduled run
            while self.running and datetime.now() < next_run:
                time.sleep(60)  # Check every minute
            
            if not self.running:
                break
            
            # Run the pipeline
            console.print("\n[bold yellow]⏰ Scheduled run triggered![/bold yellow]\n")
            self.run_pipeline()
        
        self.stop_web_server()


def setup_cron_job(schedule_time: str = "09:00"):
    """
    Setup a cron job for daily execution.
    
    Args:
        schedule_time: Time to run (HH:MM format)
    """
    hour, minute = schedule_time.split(":")
    
    script_path = Path(__file__).resolve()
    python_path = sys.executable
    
    cron_entry = f"{minute} {hour} * * * cd {script_path.parent} && {python_path} {script_path} --run-once >> /var/log/job_search.log 2>&1"
    
    console.print(Panel.fit(
        f"""[bold cyan]Cron Job Setup[/bold cyan]

To run this pipeline daily at {schedule_time}, add this to your crontab:

[green]{cron_entry}[/green]

To edit crontab, run:
[yellow]crontab -e[/yellow]

Then paste the line above.
        """,
        border_style="cyan"
    ))


def setup_systemd_service():
    """Generate systemd service file for daemon mode."""
    script_path = Path(__file__).resolve()
    python_path = sys.executable
    
    service_content = f"""[Unit]
Description=Daily Job Search Pipeline
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'pi')}
WorkingDirectory={script_path.parent}
ExecStart={python_path} {script_path} --daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    console.print(Panel.fit(
        f"""[bold cyan]Systemd Service Setup[/bold cyan]

Create file: /etc/systemd/system/job-search.service

[green]{service_content}[/green]

Then run:
[yellow]sudo systemctl daemon-reload
sudo systemctl enable job-search
sudo systemctl start job-search[/yellow]

Check status with:
[yellow]sudo systemctl status job-search[/yellow]
        """,
        border_style="cyan"
    ))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Automated Daily Job Search Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python daily_runner.py                    # Run once now
  python daily_runner.py --daemon           # Run as daemon (scheduled)
  python daily_runner.py --schedule "08:30" # Custom schedule time
  python daily_runner.py --no-web           # Skip web server
  python daily_runner.py --setup-cron       # Show cron setup instructions
  python daily_runner.py --setup-systemd    # Show systemd setup instructions
        """
    )
    
    parser.add_argument(
        "--daemon", "-d",
        action="store_true",
        help="Run as daemon with scheduled execution"
    )
    parser.add_argument(
        "--schedule", "-s",
        default="09:00",
        help="Schedule time in HH:MM format (default: 09:00)"
    )
    parser.add_argument(
        "--no-web",
        action="store_true",
        help="Don't start web server"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't open browser automatically"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=5000,
        help="Web server port (default: 5000)"
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Don't generate resumes automatically"
    )
    parser.add_argument(
        "--top-jobs", "-t",
        type=int,
        default=5,
        help="Number of top jobs to generate resumes for (default: 5)"
    )
    parser.add_argument(
        "--min-score", "-m",
        type=int,
        default=30,
        help="Minimum relevance score (default: 30)"
    )
    parser.add_argument(
        "--setup-cron",
        action="store_true",
        help="Show cron setup instructions"
    )
    parser.add_argument(
        "--setup-systemd",
        action="store_true",
        help="Show systemd service setup instructions"
    )
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run pipeline once (for cron jobs)"
    )
    
    args = parser.parse_args()
    
    # Setup instructions
    if args.setup_cron:
        setup_cron_job(args.schedule)
        return 0
    
    if args.setup_systemd:
        setup_systemd_service()
        return 0
    
    # Initialize runner
    runner = DailyJobSearchRunner(
        schedule_time=args.schedule,
        auto_resume=not args.no_resume,
        start_web=not args.no_web,
        web_port=args.port,
        open_browser=not args.no_browser,
        min_score=args.min_score,
        top_jobs_for_resume=args.top_jobs
    )
    
    try:
        if args.daemon:
            runner.run_daemon()
        elif args.run_once:
            # For cron: run without web server
            runner.start_web = False
            runner.run_pipeline()
        else:
            runner.run_once()
        
        return 0
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        return 130
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
