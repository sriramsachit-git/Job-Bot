#!/usr/bin/env python3
"""
Job Search Pipeline - Main Entry Point

Automated job searching, extraction, and filtering pipeline
for AI/ML engineering positions.

Usage:
    python main.py                              # Run daily search
    python main.py --keywords "AI engineer"     # Custom keywords
    python main.py --num-results 100            # More results
    python main.py --stats                      # Show database stats
    python main.py --help                       # Show help

Examples:
    python main.py --keywords "ML engineer" "data scientist" --num-results 30
    python main.py --daily
    python main.py --sites greenhouse.io lever.co
"""

import argparse
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm

from src.pipeline import JobSearchPipeline
from src.storage import JobDatabase
from src.resume_generator import ResumeGenerator
from src.config import config

console = Console()


def display_results(summary: dict):
    """Display search results in a formatted table."""
    table = Table(title="📊 Pipeline Results", show_header=True)
    table.add_column("Metric", style="cyan", width=25)
    table.add_column("Count", style="green", justify="right", width=10)
    
    table.add_row("URLs Found", str(summary.get("searched", 0)))
    table.add_row("Content Extracted", str(summary.get("extracted", 0)))
    table.add_row("Jobs Parsed", str(summary.get("parsed", 0)))
    table.add_row("Relevant Matches", str(summary.get("filtered", 0)))
    table.add_row("New Jobs Saved", str(summary.get("saved", 0)))
    table.add_row("Duplicates Skipped", str(summary.get("skipped", 0)))
    
    console.print("\n")
    console.print(table)
    
    if summary.get("export_path"):
        console.print(f"\n[dim]📁 Results exported to: {summary['export_path']}[/dim]")


def display_new_jobs(new_jobs: list):
    """Display newly saved jobs with YOE and key details."""
    if not new_jobs:
        return
    
    console.print("\n")
    console.print(Panel.fit(
        f"[bold cyan]🆕 {len(new_jobs)} New Jobs Found[/bold cyan]",
        border_style="cyan"
    ))
    
    table = Table(title="New Jobs Details", show_header=True)
    table.add_column("#", style="cyan", width=3)
    table.add_column("Title", style="green", width=30)
    table.add_column("Company", style="yellow", width=20)
    table.add_column("Location", width=20)
    table.add_column("YOE", style="magenta", width=6, justify="center")
    table.add_column("Score", style="blue", width=6, justify="center")
    table.add_column("Key Skills", width=40)
    
    for i, job in enumerate(new_jobs, 1):
        # Get key skills (first 3-4 required skills)
        required_skills = job.get("required_skills", [])
        if isinstance(required_skills, str):
            try:
                import json
                required_skills = json.loads(required_skills)
            except:
                required_skills = []
        
        key_skills = ", ".join(required_skills[:4]) if required_skills else "N/A"
        if len(key_skills) > 40:
            key_skills = key_skills[:37] + "..."
        
        location = job.get("location", "N/A")
        if location and len(location) > 20:
            location = location[:17] + "..."
        
        title = job.get("title", "N/A")
        if len(title) > 30:
            title = title[:27] + "..."
        
        company = job.get("company", "N/A")
        if len(company) > 20:
            company = company[:17] + "..."
        
        table.add_row(
            str(i),
            title,
            company,
            location,
            str(job.get("yoe_required", 0)),
            str(job.get("relevance_score", 0)),
            key_skills
        )
    
    console.print("\n")
    console.print(table)
    console.print("\n")


def generate_resumes_for_new_jobs(new_jobs: list, pipeline: JobSearchPipeline):
    """Generate resumes for new jobs."""
    if not new_jobs:
        return
    
    try:
        console.print("\n[bold cyan]📄 Initializing Resume Generator...[/bold cyan]\n")
        
        generator = ResumeGenerator(
            config_path="data/resume_config.yaml",
            projects_path="data/projects.json"
        )
        
        # Convert job dicts to format expected by generator
        jobs_for_generation = []
        for job in new_jobs:
            # Ensure all fields are properly formatted
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
        
        console.print(f"[green]Processing {len(jobs_for_generation)} jobs for resume generation...[/green]\n")
        
        # Generate recommendations
        recommendations = generator.generate_recommendations(jobs_for_generation)
        
        # Display recommendations
        generator.display_recommendations(recommendations)
        
        # Auto-select top 3 projects for each job
        console.print("\n[yellow]Auto-selecting top 3 projects for each job...[/yellow]")
        recommendations = generator.auto_select_top3(recommendations)
        
        # Generate resumes
        results = generator.generate_resumes(recommendations)
        
        # Save to database
        for result in results:
            if result["success"]:
                pipeline.db.save_resume(result)
        
        # Display results
        generator.display_results(results)
        
        # Summary
        successful = sum(1 for r in results if r["success"])
        console.print(f"\n[bold green]✓ Generated {successful}/{len(results)} resumes[/bold green]")
        
    except FileNotFoundError as e:
        console.print(f"[red]Configuration file not found: {e}[/red]")
        console.print("[dim]Make sure data/resume_config.yaml and data/projects.json exist[/dim]")
    except Exception as e:
        console.print(f"[red]Error generating resumes: {e}[/red]")
        import traceback
        traceback.print_exc()


def display_stats(stats: dict):
    """Display database statistics."""
    console.print(Panel.fit(
        "[bold cyan]📊 Database Statistics[/bold cyan]",
        border_style="cyan"
    ))
    
    console.print(f"\n[bold]Total Jobs:[/bold] {stats.get('total', 0)}")
    console.print(f"[bold]Applied:[/bold] {stats.get('applied_count', 0)}")
    console.print(f"[bold]Saved:[/bold] {stats.get('saved_count', 0)}")
    console.print(f"[bold]Avg YOE Required:[/bold] {stats.get('avg_yoe', 0)}")
    
    if stats.get("by_company"):
        console.print("\n[bold]Top Companies:[/bold]")
        for company_data in stats["by_company"][:5]:
            if isinstance(company_data, dict):
                company = company_data.get("company", "Unknown")
                count = company_data.get("count", 0)
            else:
                company, count = company_data
            console.print(f"  • {company}: {count}")
    
    if stats.get("by_domain"):
        console.print("\n[bold]Top Sources:[/bold]")
        for domain_data in stats["by_domain"][:5]:
            if isinstance(domain_data, dict):
                domain = domain_data.get("source_domain", "Unknown")
                count = domain_data.get("count", 0)
            else:
                domain, count = domain_data
            console.print(f"  • {domain}: {count}")


def display_banner():
    """Display application banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║           🔍 JOB SEARCH PIPELINE v1.0.0 🔍                ║
    ║     Automated Job Search, Extraction & Filtering          ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold blue")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Automated Job Search Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --daily                           Run daily automated search
  python main.py --keywords "AI engineer"          Search specific keywords
  python main.py --num-results 100                 Get more results
  python main.py --stats                           View database statistics
        """
    )
    
    parser.add_argument(
        "--keywords", "-k",
        nargs="+",
        help="Search keywords (e.g., 'AI engineer' 'ML engineer')"
    )
    parser.add_argument(
        "--sites", "-s",
        nargs="+",
        help="Job sites to search (e.g., greenhouse.io lever.co)"
    )
    parser.add_argument(
        "--num-results", "-n",
        type=int,
        default=50,
        help="Maximum number of results (default: 50, max: 100)"
    )
    parser.add_argument(
        "--date-restrict", "-d",
        default="d1",
        choices=["d1", "d3", "w1", "w2", "m1"],
        help="Date filter: d1=day, d3=3days, w1=week, w2=2weeks, m1=month"
    )
    parser.add_argument(
        "--min-score", "-m",
        type=int,
        default=30,
        help="Minimum relevance score to save (default: 30)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Display database statistics"
    )
    parser.add_argument(
        "--daily",
        action="store_true",
        help="Run daily automated search"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Reduce output verbosity"
    )
    
    args = parser.parse_args()
    
    # Display banner
    if not args.quiet:
        display_banner()
    
    pipeline = None
    
    try:
        pipeline = JobSearchPipeline()
        
        # Stats mode
        if args.stats:
            stats = pipeline.get_stats()
            display_stats(stats)
            return 0
        
        # Daily search mode
        if args.daily:
            console.print("[bold green]🚀 Running daily job search...[/bold green]\n")
            summary = pipeline.run_daily()
            display_results(summary)
            
            # Display new jobs and prompt for resume generation
            new_jobs = summary.get("new_jobs", [])
            if new_jobs:
                display_new_jobs(new_jobs)
                if Confirm.ask("\n[bold yellow]Would you like to generate resumes for these new jobs?[/bold yellow]", default=True):
                    generate_resumes_for_new_jobs(new_jobs, pipeline)
            
            return 0
        
        # Custom search mode
        if args.keywords:
            console.print(f"[bold green]🚀 Searching for: {', '.join(args.keywords)}[/bold green]\n")
            summary = pipeline.run(
                keywords=args.keywords,
                sites=args.sites,
                num_results=args.num_results,
                date_restrict=args.date_restrict,
                min_score=args.min_score
            )
            display_results(summary)
            
            # Display new jobs and prompt for resume generation
            new_jobs = summary.get("new_jobs", [])
            if new_jobs:
                display_new_jobs(new_jobs)
                if Confirm.ask("\n[bold yellow]Would you like to generate resumes for these new jobs?[/bold yellow]", default=True):
                    generate_resumes_for_new_jobs(new_jobs, pipeline)
            
            return 0
        
        # Default: run daily search
        console.print("[bold green]🚀 Running daily job search (default)...[/bold green]\n")
        summary = pipeline.run_daily()
        display_results(summary)
        
        # Display new jobs and prompt for resume generation
        new_jobs = summary.get("new_jobs", [])
        if new_jobs:
            display_new_jobs(new_jobs)
            if Confirm.ask("\n[bold yellow]Would you like to generate resumes for these new jobs?[/bold yellow]", default=True):
                generate_resumes_for_new_jobs(new_jobs, pipeline)
        
        return 0
        
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Search cancelled by user[/yellow]")
        return 130
    except ValueError as e:
        console.print(f"\n[red]❌ Configuration error: {e}[/red]")
        console.print("[dim]Please check your .env file has all required API keys.[/dim]")
        return 1
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        return 1
    finally:
        if pipeline:
            pipeline.cleanup()


if __name__ == "__main__":
    sys.exit(main())
