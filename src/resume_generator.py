"""
Resume generation module with batch processing and project selection.
Generates tailored LaTeX resumes based on job postings and user config.
"""

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field

import yaml
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.panel import Panel

from src.config import config
from src.llm_parser import ParsedJob

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class ResumeConfig:
    """Resume configuration loaded from YAML."""
    contact: Dict[str, str]
    default_location: str
    approved_locations: List[str]
    location_mapping: Dict[str, str]
    education: Dict[str, Any]
    experience: List[Dict[str, Any]]
    skills: Dict[str, List[str]]


@dataclass
class Project:
    """Project data structure."""
    id: str
    name: str
    one_liner: str
    skills: List[str]
    metrics: str
    bullets: List[str]


@dataclass
class ResumeRecommendation:
    """Recommendation for a single job."""
    job_id: int
    job_title: str
    company: str
    job_url: str
    job_location: str
    resume_location: str
    job_skills: List[str]
    recommended_projects: List[Tuple[Project, float]] = field(default_factory=list)
    selected_projects: List[Project] = field(default_factory=list)


class ResumeGenerator:
    """
    Generates tailored LaTeX resumes with batch processing.
    """
    
    def __init__(
        self,
        config_path: str = "data/resume_config.yaml",
        projects_path: str = "data/projects.json",
        output_dir: str = "data/resumes",
        api_key: Optional[str] = None
    ):
        """Initialize resume generator."""
        self.api_key = api_key or config.openai_api_key
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=self.api_key)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.resume_config = self._load_config(config_path)
        self.projects = self._load_projects(projects_path)
        
        logger.info(f"ResumeGenerator initialized with {len(self.projects)} projects")
    
    def _load_config(self, path: str) -> ResumeConfig:
        """Load resume configuration from YAML."""
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Resume config not found: {path}")
        
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        return ResumeConfig(
            contact=data.get('contact', {}),
            default_location=data.get('default_location', 'San Diego, CA'),
            approved_locations=data.get('approved_locations', []),
            location_mapping=data.get('location_mapping', {}),
            education=data.get('education', {}),
            experience=data.get('experience', []),
            skills=data.get('skills', {})
        )
    
    def _load_projects(self, path: str) -> List[Project]:
        """Load projects from JSON."""
        projects_path = Path(path)
        if not projects_path.exists():
            raise FileNotFoundError(f"Projects file not found: {path}")
        
        with open(projects_path, 'r') as f:
            data = json.load(f)
        
        return [
            Project(
                id=p['id'],
                name=p['name'],
                one_liner=p['one_liner'],
                skills=p['skills'],
                metrics=p['metrics'],
                bullets=p['bullets']
            )
            for p in data['projects']
        ]
    
    def match_location(self, job_location: Optional[str]) -> str:
        """Match job location to approved resume location."""
        if not job_location:
            return self.resume_config.default_location
        
        job_loc_lower = job_location.lower().strip()
        
        # Check direct mapping first
        for key, value in self.resume_config.location_mapping.items():
            if key in job_loc_lower:
                logger.debug(f"Location mapped: {job_location} -> {value}")
                return value
        
        # Check approved locations
        for approved in self.resume_config.approved_locations:
            approved_lower = approved.lower()
            if approved_lower in job_loc_lower or job_loc_lower in approved_lower:
                logger.debug(f"Location matched: {job_location} -> {approved}")
                return approved
            city = approved.split(',')[0].lower()
            if city in job_loc_lower:
                logger.debug(f"Location city matched: {job_location} -> {approved}")
                return approved
        
        # Check for remote
        if 'remote' in job_loc_lower:
            return "Remote"
        
        logger.debug(f"Location defaulted: {job_location} -> {self.resume_config.default_location}")
        return self.resume_config.default_location

    PROJECT_RANKING_PROMPT = """You are an expert resume consultant. Rank these projects by relevance to the job.

## Job Details:
Title: {job_title}
Company: {company}
Required Skills: {required_skills}
Nice to Have: {nice_to_have}
Responsibilities: {responsibilities}

## Available Projects:
{projects_list}

## Instructions:
Rank ALL projects by how well they demonstrate relevant skills for this specific job.
Consider:
1. Skill overlap with job requirements
2. Domain relevance
3. Impact/metrics that would impress this employer

Return JSON only:
{{
    "rankings": [
        {{"project_id": "id", "score": 95, "reason": "brief reason"}},
        ...
    ]
}}

Rank all {num_projects} projects. Scores should be 0-100.
"""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5)
    )
    def _rank_projects(self, job: ParsedJob) -> List[Tuple[Project, float, str]]:
        """Use AI to rank projects by relevance to job."""
        projects_list = "\n".join([
            f"- ID: {p.id}\n  Name: {p.name}\n  Skills: {', '.join(p.skills)}\n  Description: {p.one_liner}"
            for p in self.projects
        ])
        
        prompt = self.PROJECT_RANKING_PROMPT.format(
            job_title=job.job_title,
            company=job.company,
            required_skills=", ".join(job.required_skills or []),
            nice_to_have=", ".join(job.nice_to_have_skills or []),
            responsibilities=", ".join(job.responsibilities or []),
            projects_list=projects_list,
            num_projects=len(self.projects)
        )
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=1500
        )
        
        result = json.loads(response.choices[0].message.content)
        
        project_map = {p.id: p for p in self.projects}
        ranked = []
        
        for item in result.get("rankings", []):
            project_id = item.get("project_id")
            if project_id in project_map:
                ranked.append((
                    project_map[project_id],
                    item.get("score", 0),
                    item.get("reason", "")
                ))
        
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked
    
    def generate_recommendations(
        self,
        jobs: List[Dict[str, Any]]
    ) -> List[ResumeRecommendation]:
        """Generate project recommendations for multiple jobs."""
        recommendations = []
        
        console.print(f"\n[bold cyan]Analyzing {len(jobs)} jobs for project matching...[/bold cyan]\n")
        
        for i, job_data in enumerate(jobs):
            console.print(f"[{i+1}/{len(jobs)}] Analyzing: {job_data['title']} @ {job_data['company']}")
            
            # Parse skills from JSON if stored as string
            required_skills = job_data.get('required_skills', [])
            if isinstance(required_skills, str):
                try:
                    required_skills = json.loads(required_skills)
                except:
                    required_skills = []
            
            nice_to_have = job_data.get('nice_to_have_skills', [])
            if isinstance(nice_to_have, str):
                try:
                    nice_to_have = json.loads(nice_to_have)
                except:
                    nice_to_have = []
            
            responsibilities = job_data.get('responsibilities', [])
            if isinstance(responsibilities, str):
                try:
                    responsibilities = json.loads(responsibilities)
                except:
                    responsibilities = []
            
            job = ParsedJob(
                job_title=job_data['title'],
                company=job_data['company'],
                location=job_data.get('location'),
                required_skills=required_skills,
                nice_to_have_skills=nice_to_have,
                responsibilities=responsibilities,
                yoe_required=job_data.get('yoe_required', 0),
                remote=job_data.get('remote'),
                source_url=job_data['url'],
                source_domain=job_data.get('source_domain', '')
            )
            
            resume_location = self.match_location(job.location)
            ranked_projects = self._rank_projects(job)
            
            rec = ResumeRecommendation(
                job_id=job_data['id'],
                job_title=job.job_title,
                company=job.company,
                job_url=job.source_url,
                job_location=job.location or "Not specified",
                resume_location=resume_location,
                job_skills=job.required_skills or [],
                recommended_projects=[(p, s) for p, s, r in ranked_projects],
                selected_projects=[]
            )
            
            recommendations.append(rec)
        
        return recommendations
    
    def display_recommendations(self, recommendations: List[ResumeRecommendation]):
        """Display recommendations summary table."""
        table = Table(title="📋 Resume Recommendations Summary")
        table.add_column("#", style="cyan", width=3)
        table.add_column("Job", style="green", width=30)
        table.add_column("Location", width=18)
        table.add_column("Top 3 Projects", width=50)
        
        for i, rec in enumerate(recommendations):
            top_3 = [f"{p.name} ({s:.0f}%)" for p, s in rec.recommended_projects[:3]]
            table.add_row(
                str(i + 1),
                f"{rec.job_title[:25]}\n@ {rec.company[:20]}",
                f"Job: {rec.job_location[:15]}\nResume: {rec.resume_location}",
                "\n".join(top_3)
            )
        
        console.print("\n")
        console.print(table)
    
    def interactive_review(
        self,
        recommendations: List[ResumeRecommendation]
    ) -> List[ResumeRecommendation]:
        """Interactive review and project selection."""
        console.print("\n[bold yellow]═══ Interactive Project Selection ═══[/bold yellow]\n")
        
        for i, rec in enumerate(recommendations):
            console.print(Panel(
                f"[bold]{rec.job_title}[/bold] @ {rec.company}\n"
                f"Location: {rec.job_location} → Resume: [green]{rec.resume_location}[/green]\n"
                f"URL: {rec.job_url}",
                title=f"Job {i+1}/{len(recommendations)}"
            ))
            
            console.print("\n[bold]Recommended Projects (ranked by AI):[/bold]")
            for j, (project, score) in enumerate(rec.recommended_projects):
                marker = "✓" if j < 3 else " "
                color = "green" if j < 3 else "dim"
                console.print(f"  [{color}][{j+1}] {marker} {project.name} ({score:.0f}%) - {project.one_liner[:50]}...[/{color}]")
            
            console.print(f"\n[dim]Default selection: 1,2,3[/dim]")
            selection = Prompt.ask(
                "Select 3 projects (comma-separated numbers)",
                default="1,2,3"
            )
            
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(",")]
                if len(indices) != 3:
                    console.print("[yellow]Warning: Selecting first 3 by default[/yellow]")
                    indices = [0, 1, 2]
                
                rec.selected_projects = [
                    rec.recommended_projects[idx][0] 
                    for idx in indices 
                    if idx < len(rec.recommended_projects)
                ]
            except (ValueError, IndexError):
                console.print("[yellow]Invalid input. Using top 3.[/yellow]")
                rec.selected_projects = [p for p, s in rec.recommended_projects[:3]]
            
            console.print(f"[green]Selected: {', '.join(p.name for p in rec.selected_projects)}[/green]\n")
            console.print("─" * 60 + "\n")
        
        return recommendations
    
    def auto_select_top3(
        self,
        recommendations: List[ResumeRecommendation]
    ) -> List[ResumeRecommendation]:
        """Auto-select top 3 projects for each job."""
        for rec in recommendations:
            rec.selected_projects = [p for p, s in rec.recommended_projects[:3]]
        return recommendations

    @staticmethod
    def _escape_latex(text: str) -> str:
        """Escape special LaTeX characters."""
        if not text:
            return ""
        # Escape % sign (LaTeX comment character)
        text = text.replace('%', '\\%')
        # Escape & sign
        text = text.replace('&', '\\&')
        # Escape # sign
        text = text.replace('#', '\\#')
        # Escape $ sign
        text = text.replace('$', '\\$')
        # Escape _ sign (but not in URLs)
        # text = text.replace('_', '\\_')  # Skip this, causes issues in URLs
        return text

    @staticmethod
    def _clean_url(url: str) -> str:
        """Clean URL for LaTeX href - remove https:// prefix if present."""
        if not url:
            return ""
        url = url.strip()
        # Remove any leading/trailing underscores
        url = url.strip('_')
        # Remove https:// or http:// prefix (we'll add it in template)
        if url.startswith('https://'):
            url = url[8:]
        elif url.startswith('http://'):
            url = url[7:]
        return url

    LATEX_TEMPLATE = r"""\documentclass[11pt,a4paper]{{article}}
\usepackage[margin=0.6in]{{geometry}}
\usepackage{{enumitem}}
\usepackage{{hyperref}}
\usepackage{{titlesec}}
\usepackage{{parskip}}

\pagestyle{{empty}}
\setlength{{\parindent}}{{0pt}}
\titleformat{{\section}}{{\large\bfseries}}{{}}{{0em}}{{}}[\titlerule]
\titlespacing{{\section}}{{0pt}}{{8pt}}{{4pt}}

\begin{{document}}

\begin{{center}}
    {{\LARGE\bfseries {name}}} \\[4pt]
    {location} \\[2pt]
    {email} | {phone} | \href{{https://{linkedin}}}{{LinkedIn}} | \href{{https://{github}}}{{GitHub}}
\end{{center}}

\section*{{Summary}}
{summary}

\section*{{Technical Skills}}
\textbf{{Languages \& ML:}} {languages}, {ml_frameworks} \\
\textbf{{Cloud \& Tools:}} {cloud_devops}, {ai_tools} \\
\textbf{{Domains:}} {domains}

\section*{{Experience}}
{experience_section}

\section*{{Projects}}
{projects_section}

\section*{{Education}}
\textbf{{{degree}}}, {school} \hfill GPA: {gpa} | {graduation} \\
\textit{{Relevant Coursework:}} {coursework}

\end{{document}}
"""

    def _generate_latex(self, rec: ResumeRecommendation) -> str:
        """Generate LaTeX resume for a recommendation."""
        summary = self._escape_latex(self._generate_summary(rec))
        
        experience_section = ""
        for exp in self.resume_config.experience:
            title = self._escape_latex(exp['title'])
            company = self._escape_latex(exp['company'])
            dates = self._escape_latex(exp['dates'])
            experience_section += f"\\textbf{{{title}}} | {company} \\hfill {dates} \\\\\n"
            experience_section += "\\begin{itemize}[leftmargin=*, nosep]\n"
            for bullet in exp['bullets'][:3]:
                experience_section += f"    \\item {self._escape_latex(bullet)}\n"
            experience_section += "\\end{itemize}\n\\vspace{4pt}\n"
        
        projects_section = ""
        for project in rec.selected_projects:
            name = self._escape_latex(project.name)
            metrics = self._escape_latex(project.metrics)
            projects_section += f"\\textbf{{{name}}} | \\textit{{{metrics}}} \\\\\n"
            projects_section += "\\begin{itemize}[leftmargin=*, nosep]\n"
            for bullet in project.bullets[:2]:
                projects_section += f"    \\item {self._escape_latex(bullet)}\n"
            projects_section += "\\end{itemize}\n\\vspace{4pt}\n"
        
        # Clean URLs - remove https:// if present (template adds it)
        linkedin = self._clean_url(self.resume_config.contact.get('linkedin', 'linkedin.com/in/'))
        github = self._clean_url(self.resume_config.contact.get('github', 'github.com/'))
        
        latex = self.LATEX_TEMPLATE.format(
            name=self._escape_latex(self.resume_config.contact.get('name', 'Your Name')),
            location=self._escape_latex(rec.resume_location),
            email=self.resume_config.contact.get('email', 'email@example.com'),
            phone=self.resume_config.contact.get('phone', 'xxx-xxx-xxxx'),
            linkedin=linkedin,
            github=github,
            summary=summary,
            languages=", ".join(self.resume_config.skills.get('languages', [])),
            ml_frameworks=", ".join(self.resume_config.skills.get('ml_frameworks', [])),
            cloud_devops=", ".join(self.resume_config.skills.get('cloud_devops', [])),
            ai_tools=", ".join(self.resume_config.skills.get('ai_tools', [])),
            domains=", ".join(self.resume_config.skills.get('domains', [])),
            experience_section=experience_section,
            projects_section=projects_section,
            degree=self._escape_latex(self.resume_config.education.get('degree', '')),
            school=self._escape_latex(self.resume_config.education.get('school', '')),
            gpa=self.resume_config.education.get('gpa', ''),
            graduation=self._escape_latex(self.resume_config.education.get('graduation', '')),
            coursework=", ".join(self.resume_config.education.get('coursework', []))
        )
        
        return latex
    
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=3))
    def _generate_summary(self, rec: ResumeRecommendation) -> str:
        """Generate tailored summary for job."""
        prompt = f"""Write a 2-3 sentence professional summary for a resume targeting this job:
        
Job: {rec.job_title} at {rec.company}
Key Skills Needed: {', '.join(rec.job_skills[:5]) if rec.job_skills else 'AI/ML skills'}

The candidate is an AI/ML Engineer with MS in Data Science, experience in ML pipelines, RAG systems, and deep learning.

Return ONLY the summary text, no quotes or labels. Keep it under 50 words."""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=150
        )
        
        return response.choices[0].message.content.strip()
    
    def _compile_pdf(self, latex: str, output_path: Path) -> Optional[Path]:
        """Compile LaTeX to PDF."""
        tex_path = output_path.with_suffix(".tex")
        tex_path.write_text(latex)
        
        try:
            for _ in range(2):
                subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", 
                     "-output-directory", str(output_path.parent), 
                     str(tex_path)],
                    capture_output=True,
                    timeout=60
                )
            
            pdf_path = output_path.with_suffix(".pdf")
            if pdf_path.exists():
                for ext in [".aux", ".log", ".out"]:
                    aux = output_path.with_suffix(ext)
                    if aux.exists():
                        aux.unlink()
                return pdf_path
        except FileNotFoundError:
            logger.warning("pdflatex not found - .tex file saved")
        except Exception as e:
            logger.error(f"PDF compilation error: {e}")
        
        return None
    
    def generate_resumes(
        self,
        recommendations: List[ResumeRecommendation]
    ) -> List[Dict[str, Any]]:
        """Generate LaTeX resumes for all recommendations."""
        results = []
        
        console.print("\n[bold cyan]Generating resumes...[/bold cyan]\n")
        
        for i, rec in enumerate(recommendations):
            console.print(f"[{i+1}/{len(recommendations)}] Generating: {rec.job_title} @ {rec.company}")
            
            safe_company = "".join(c for c in rec.company if c.isalnum())[:15]
            safe_title = "".join(c for c in rec.job_title if c.isalnum())[:15]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"resume_{safe_company}_{safe_title}_{timestamp}"
            output_path = self.output_dir / filename
            
            result = {
                "job_id": rec.job_id,
                "job_title": rec.job_title,
                "company": rec.company,
                "job_url": rec.job_url,
                "resume_location": rec.resume_location,
                "selected_projects": [p.name for p in rec.selected_projects],
                "tex_path": None,
                "pdf_path": None,
                "success": False,
                "error": None
            }
            
            try:
                latex = self._generate_latex(rec)
                
                tex_path = output_path.with_suffix(".tex")
                tex_path.write_text(latex)
                result["tex_path"] = str(tex_path)
                
                pdf_path = self._compile_pdf(latex, output_path)
                if pdf_path:
                    result["pdf_path"] = str(pdf_path)
                
                result["success"] = True
                console.print(f"  [green]✓ Saved: {tex_path.name}[/green]")
                
            except Exception as e:
                result["error"] = str(e)
                console.print(f"  [red]✗ Error: {e}[/red]")
            
            results.append(result)
        
        return results
    
    def display_results(self, results: List[Dict[str, Any]]):
        """Display final results table."""
        table = Table(title="📄 Generated Resumes")
        table.add_column("#", style="cyan", width=3)
        table.add_column("Job", width=30)
        table.add_column("Location", width=15)
        table.add_column("Projects", width=35)
        table.add_column("Files", width=25)
        
        for i, r in enumerate(results):
            status = "✓" if r["success"] else "✗"
            files = []
            if r["tex_path"]:
                files.append(Path(r["tex_path"]).name)
            if r["pdf_path"]:
                files.append(Path(r["pdf_path"]).name)
            
            table.add_row(
                str(i + 1),
                f"{r['job_title'][:25]}\n@ {r['company'][:20]}",
                r["resume_location"],
                "\n".join(r["selected_projects"]),
                f"{status}\n" + "\n".join(files) if files else f"✗ {r.get('error', 'Unknown')[:20]}"
            )
        
        console.print("\n")
        console.print(table)
        console.print(f"\n[dim]Resumes saved to: {self.output_dir}[/dim]")
