#!/usr/bin/env python3
"""
Resume Generation CLI

Generate tailored resumes for top job matches.

Usage:
    python generate_resumes.py                    # Interactive mode (top 10 jobs)
    python generate_resumes.py --top 5            # Top 5 jobs
    python generate_resumes.py --auto             # Auto-select projects (no prompts)
    python generate_resumes.py --job-id 42        # Single job by ID
    python generate_resumes.py --list-resumes     # List all generated resumes
"""

import argparse
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.storage import JobDatabase
from src.resume_generator import ResumeGenerator
from src.config import config

console = Console()


def display_banner():
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║         📄 RESUME GENERATOR v1.0.0 📄                     ║
    ║     Tailored Resumes for Your Top Job Matches             ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold blue")


def list_resumes(db: JobDatabase):
    """Display all generated resumes."""
    resumes = db.get_resumes_summary()
    
    if not resumes:
        console.print("[yellow]No resumes generated yet.[/yellow]")
        return
    
    table = Table(title="📄 Generated Resumes")
    table.add_column("ID", style="cyan", width=4)
    table.add_column("Job", width=30)
    table.add_column("Location", width=15)
    table.add_column("Projects", width=30)
    table.add_column("Files", width=30)
    table.add_column("Date", width=12)
    
    for r in resumes:
        projects = r.get('selected_projects', '[]')
        if isinstance(projects, str):
            try:
                import json
                projects = json.loads(projects)
            except:
                projects = []
        
        files = []
        if r.get('tex_path'):
            files.append(r['tex_path'].split('/')[-1])
        if r.get('pdf_path'):
            files.append(r['pdf_path'].split('/')[-1])
        
        created = r.get('created_at', '')[:10] if r.get('created_at') else ''
        
        table.add_row(
            str(r.get('id', '')),
            f"{r.get('job_title', '')[:25]}\n@ {r.get('company', '')[:20]}",
            r.get('resume_location', ''),
            "\n".join(projects[:3]) if isinstance(projects, list) else str(projects)[:30],
            "\n".join(files),
            created
        )
    
    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="Generate tailored resumes")
    
    parser.add_argument(
        "--top", "-t",
        type=int,
        default=10,
        help="Number of top jobs to process (default: 10)"
    )
    parser.add_argument(
        "--min-score", "-m",
        type=int,
        default=40,
        help="Minimum relevance score (default: 40)"
    )
    parser.add_argument(
        "--auto", "-a",
        action="store_true",
        help="Auto-select top 3 projects (skip interactive review)"
    )
    parser.add_argument(
        "--job-id", "-j",
        type=int,
        help="Generate resume for specific job ID"
    )
    parser.add_argument(
        "--config", "-c",
        default="data/resume_config.yaml",
        help="Path to resume config file"
    )
    parser.add_argument(
        "--projects", "-p",
        default="data/projects.json",
        help="Path to projects file"
    )
    parser.add_argument(
        "--list-resumes", "-l",
        action="store_true",
        help="List all generated resumes"
    )
    
    args = parser.parse_args()
    
    display_banner()
    
    try:
        # Initialize database
        db = JobDatabase(config.database_path)
        
        # List resumes mode
        if args.list_resumes:
            list_resumes(db)
            db.close()
            return 0
        
        # Initialize generator
        generator = ResumeGenerator(
            config_path=args.config,
            projects_path=args.projects
        )
        
        # Get jobs
        if args.job_id:
            job = db.get_job_by_id(args.job_id)
            if not job:
                console.print(f"[red]Job ID {args.job_id} not found[/red]")
                return 1
            jobs = [job]
        else:
            jobs = db.get_jobs(
                filters={"min_score": args.min_score},
                limit=args.top
            )
        
        if not jobs:
            console.print("[yellow]No jobs found matching criteria.[/yellow]")
            console.print("[dim]Run the job search pipeline first: python main.py --daily[/dim]")
            return 1
        
        console.print(f"[green]Found {len(jobs)} jobs to process[/green]")
        
        # Generate recommendations
        recommendations = generator.generate_recommendations(jobs)
        
        # Display summary
        generator.display_recommendations(recommendations)
        
        # Project selection
        if args.auto:
            console.print("\n[yellow]Auto-selecting top 3 projects for each job...[/yellow]")
            recommendations = generator.auto_select_top3(recommendations)
        else:
            recommendations = generator.interactive_review(recommendations)
        
        # Generate resumes
        results = generator.generate_resumes(recommendations)
        
        # Save to database
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
        
        # Display results
        generator.display_results(results)
        
        # Summary
        successful = sum(1 for r in results if r["success"])
        console.print(f"\n[bold green]✓ Generated {successful}/{len(results)} resumes[/bold green]")
        
        db.close()
        return 0
        
    except FileNotFoundError as e:
        console.print(f"[red]Configuration file not found: {e}[/red]")
        console.print("[dim]Make sure data/resume_config.yaml and data/projects.json exist[/dim]")
        return 1
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
