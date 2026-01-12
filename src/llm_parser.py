"""
LLM-based job posting parser.
Uses GPT-4o-mini to extract structured data from raw job posting text.
"""

import json
import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn

from src.config import config
from src.extractor import ContentExtractor

logger = logging.getLogger(__name__)
console = Console()


class ParsedJob(BaseModel):
    """Structured job posting data model."""
    
    job_title: str = Field(description="Job title")
    company: str = Field(description="Company name")
    location: Optional[str] = Field(default=None, description="Job location")
    remote: Optional[bool] = Field(default=None, description="Is remote work available")
    employment_type: Optional[str] = Field(default=None, description="full-time/part-time/contract/intern")
    salary_range: Optional[str] = Field(default=None, description="Salary range if mentioned")
    yoe_required: int = Field(default=0, description="Minimum years of experience required")
    required_skills: List[str] = Field(default_factory=list, description="Required technical skills")
    nice_to_have_skills: List[str] = Field(default_factory=list, description="Preferred/bonus skills")
    education: Optional[str] = Field(default=None, description="Education requirements")
    responsibilities: List[str] = Field(default_factory=list, description="Key responsibilities")
    qualifications: List[str] = Field(default_factory=list, description="Required qualifications")
    benefits: List[str] = Field(default_factory=list, description="Benefits offered")
    job_summary: Optional[str] = Field(default=None, description="Brief job summary")
    apply_url: Optional[str] = Field(default=None, description="Direct application URL")
    source_url: str = Field(description="Source URL where job was found")
    source_domain: str = Field(description="Domain of the source")


class JobParser:
    """
    LLM-based job posting parser.
    
    Uses OpenAI's GPT-4o-mini to extract structured data from
    raw job posting text with high accuracy.
    """
    
    # Prompt template for job extraction
    EXTRACTION_PROMPT = """Extract job posting details from this content. Return valid JSON only.

Required JSON schema:
{{
    "job_title": "string - exact job title",
    "company": "string - company name",
    "location": "string or null - job location",
    "remote": "boolean or null - true if remote/hybrid mentioned",
    "employment_type": "string or null - full-time/part-time/contract/intern",
    "salary_range": "string or null - salary if mentioned",
    "yoe_required": "integer - minimum years of experience (0 if not specified or entry-level)",
    "required_skills": ["array of required technical skills"],
    "nice_to_have_skills": ["array of preferred/bonus skills"],
    "education": "string or null - education requirements",
    "responsibilities": ["array of key responsibilities - max 5"],
    "qualifications": ["array of key qualifications - max 5"],
    "benefits": ["array of benefits - max 5"],
    "job_summary": "string - 2-3 sentence summary"
}}

Important:
- For yoe_required: Extract MINIMUM years. "3-5 years" = 3, "5+ years" = 5, "entry level" = 0
- For skills: Include programming languages, frameworks, tools, cloud platforms
- Use null for fields not found in the posting
- Keep arrays concise (max 5 items each)

Raw job posting content:
{content}
"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the job parser.
        
        Args:
            api_key: OpenAI API key. Defaults to config.openai_api_key
        """
        self.api_key = api_key or config.openai_api_key
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=self.api_key)
        self.extractor = ContentExtractor()  # For domain extraction
        logger.info("JobParser initialized successfully")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5)
    )
    def _call_llm(self, content: str) -> Dict[str, Any]:
        """
        Make LLM API call with retry logic.
        
        Args:
            content: Raw job posting content
            
        Returns:
            Parsed JSON response as dictionary
        """
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": self.EXTRACTION_PROMPT.format(content=content[:7000])
            }],
            response_format={"type": "json_object"},
            temperature=0.1,  # Low temperature for consistent extraction
            max_tokens=1500
        )
        
        return json.loads(response.choices[0].message.content)
    
    def extract_job_details(
        self,
        raw_text: str,
        url: str
    ) -> Optional[ParsedJob]:
        """
        Extract structured job details from raw text.
        
        Args:
            raw_text: Raw job posting text
            url: Source URL of the job posting
            
        Returns:
            ParsedJob object or None if extraction failed
        """
        # Validate input
        if not raw_text or len(raw_text) < 200:
            logger.warning(f"Content too short for {url}: {len(raw_text) if raw_text else 0} chars")
            return None
        
        try:
            # Call LLM for extraction
            result = self._call_llm(raw_text)
            
            # Add source metadata
            result["source_url"] = url
            result["source_domain"] = self.extractor.get_domain(url)
            
            # Validate and create ParsedJob
            job = ParsedJob(**result)
            
            logger.debug(f"Successfully parsed: {job.job_title} @ {job.company}")
            return job
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Extraction error for {url}: {e}")
            return None
    
    def parse_batch(
        self,
        extracted_contents: List[Dict[str, Any]]
    ) -> List[ParsedJob]:
        """
        Parse multiple extracted contents into structured jobs.
        
        Args:
            extracted_contents: List of dicts with url and content
            
        Returns:
            List of successfully parsed ParsedJob objects
        """
        jobs: List[ParsedJob] = []
        
        # Filter to only successful extractions
        valid_contents = [c for c in extracted_contents if c.get("content")]
        
        if not valid_contents:
            logger.warning("No valid content to parse")
            return jobs
        
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Parsing jobs...", total=len(valid_contents))
            
            for item in valid_contents:
                url = item["url"]
                content = item["content"]
                
                job = self.extract_job_details(content, url)
                
                if job:
                    jobs.append(job)
                    progress.update(task, description=f"✓ {job.job_title[:30]}...")
                else:
                    progress.update(task, description=f"✗ Failed to parse")
                
                progress.advance(task)
        
        console.print(f"[green]Parsed: {len(jobs)}/{len(valid_contents)} jobs[/green]")
        return jobs
