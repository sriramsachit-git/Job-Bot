"""
Job filtering and relevance scoring module.
Scores jobs based on user profile matching.
"""

import logging
from typing import List, Tuple, Dict, Any
from src.llm_parser import ParsedJob
from src.config import USER_PROFILE

logger = logging.getLogger(__name__)


class JobFilter:
    """
    Job filtering and relevance scoring.
    
    Calculates a 0-100 relevance score based on:
    - Years of experience match
    - Required skills match
    - Preferred skills match
    - Location preferences
    - Remote work preferences
    - Title exclusion keywords
    """
    
    def __init__(self, user_profile: Dict[str, Any] = None):
        """
        Initialize the job filter.
        
        Args:
            user_profile: User profile dict with preferences.
                         Defaults to USER_PROFILE from config.
        """
        self.profile = user_profile or USER_PROFILE
        
        # Normalize skills to lowercase for matching
        self.required_skills = set(
            self._normalize(s) for s in self.profile.get("required_skills", [])
        )
        self.preferred_skills = set(
            self._normalize(s) for s in self.profile.get("preferred_skills", [])
        )
        self.preferred_locations = set(
            self._normalize(loc) for loc in self.profile.get("preferred_locations", [])
        )
        self.exclude_keywords = set(
            self._normalize(kw) for kw in self.profile.get("exclude_title_keywords", [])
        )
        
        self.max_yoe = self.profile.get("max_yoe", 3)
        self.remote_only = self.profile.get("remote_only", False)
        
        logger.info(f"JobFilter initialized with max_yoe={self.max_yoe}")
    
    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize text for comparison."""
        return text.lower().strip()
    
    def _skills_match_count(
        self,
        job_skills: List[str],
        target_skills: set
    ) -> int:
        """Count matching skills between job and target."""
        if not job_skills:
            return 0
        
        job_skills_normalized = set(self._normalize(s) for s in job_skills)
        
        # Check for partial matches too (e.g., "pytorch" matches "pytorch/tensorflow")
        matches = 0
        for job_skill in job_skills_normalized:
            for target in target_skills:
                if target in job_skill or job_skill in target:
                    matches += 1
                    break
        
        return matches
    
    def _title_has_excluded_keywords(self, title: str) -> bool:
        """Check if job title contains excluded keywords."""
        if not title:
            return False
        
        title_lower = title.lower()
        return any(kw in title_lower for kw in self.exclude_keywords)
    
    def _is_location_usa_or_remote(self, text: str) -> bool:
        """
        Check if text indicates USA location or remote work.
        
        Args:
            text: Text to check (title, snippet, etc.)
            
        Returns:
            True if location appears to be USA or remote, False otherwise
        """
        if not text:
            return True  # If no location info, allow it (will be checked later)
        
        text_lower = text.lower()
        
        # Check for remote indicators
        remote_keywords = ["remote", "work from home", "wfh", "hybrid", "anywhere"]
        if any(kw in text_lower for kw in remote_keywords):
            return True
        
        # Check for USA indicators
        usa_keywords = [
            "united states", "usa", "u.s.", "us", "america",
            "san francisco", "new york", "seattle", "austin", "boston",
            "chicago", "los angeles", "san diego", "san jose", "denver",
            "atlanta", "dallas", "houston", "philadelphia", "phoenix",
            "miami", "portland", "nashville", "detroit", "minneapolis",
            "california", "texas", "new york", "florida", "washington",
            "massachusetts", "illinois", "colorado", "georgia", "north carolina",
            "virginia", "arizona", "tennessee", "oregon", "michigan"
        ]
        if any(kw in text_lower for kw in usa_keywords):
            return True
        
        # Check for non-USA country indicators (exclude these)
        non_usa_countries = [
            "canada", "toronto", "vancouver", "montreal", "ottawa",
            "uk", "united kingdom", "london", "england", "britain",
            "germany", "berlin", "munich", "france", "paris",
            "india", "bangalore", "mumbai", "delhi", "hyderabad",
            "china", "beijing", "shanghai", "singapore", "australia",
            "sydney", "melbourne", "japan", "tokyo", "netherlands",
            "amsterdam", "sweden", "stockholm", "switzerland", "zurich",
            "spain", "madrid", "italy", "rome", "milan", "brazil",
            "sao paulo", "mexico", "mexico city", "poland", "warsaw",
            "ireland", "dublin", "israel", "tel aviv", "south korea",
            "seoul", "taiwan", "taipei", "hong kong", "philippines",
            "manila", "indonesia", "jakarta", "thailand", "bangkok",
            "vietnam", "ho chi minh", "malaysia", "kuala lumpur"
        ]
        
        # If we find non-USA country indicators, skip it
        if any(country in text_lower for country in non_usa_countries):
            logger.debug(f"Non-USA location detected: {text}")
            return False
        
        # If no location info found, allow it (will be checked after parsing)
        return True
    
    def should_skip_early(self, title: str, snippet: str = "", display_link: str = "") -> bool:
        """
        Early filtering before extraction/parsing to save credits.
        
        Checks title and snippet for:
        1. Excluded keywords (senior, staff, etc.)
        2. Location (only USA or remote allowed)
        
        This is called BEFORE expensive extraction/parsing operations.
        
        Args:
            title: Job title from search results
            snippet: Search snippet text (optional)
            display_link: Display link/domain (optional)
            
        Returns:
            True if job should be skipped
        """
        if not title:
            return False
        
        # Check 1: Excluded keywords in title
        if self._title_has_excluded_keywords(title):
            logger.debug(f"Skipping early: {title} (excluded keyword in title)")
            return True
        
        # Check 2: Excluded keywords in snippet
        if snippet:
            snippet_lower = snippet.lower()
            if any(kw in snippet_lower for kw in self.exclude_keywords):
                logger.debug(f"Skipping early: {title} (excluded keyword in snippet)")
                return True
        
        # Check 3: Location filtering (only USA or remote)
        # Combine all text sources for location check
        location_text = f"{title} {snippet} {display_link}".strip()
        if not self._is_location_usa_or_remote(location_text):
            logger.debug(f"Skipping early: {title} (non-USA location)")
            return True
        
        return False
    
    def _location_matches(self, location: str) -> bool:
        """Check if job location matches preferences."""
        if not location:
            return False
        
        location_lower = location.lower()
        
        # Check for remote
        if "remote" in location_lower:
            return True
        
        # Check for preferred locations
        return any(loc in location_lower for loc in self.preferred_locations)
    
    def calculate_relevance_score(self, job: ParsedJob) -> int:
        """
        Calculate relevance score for a job.
        
        Scoring breakdown (0-100):
        - YOE match: +30 points (or -50 if over max)
        - Required skills: +5 per match (max 25)
        - Preferred skills: +3 per match (max 15)
        - Location match: +15 points
        - Remote match: +10 points (if remote_only)
        - Title exclusion: -40 points
        
        Args:
            job: ParsedJob object to score
            
        Returns:
            Relevance score (0-100)
        """
        score = 0
        
        # 1. YOE check (most important)
        if job.yoe_required <= self.max_yoe:
            score += 30
        else:
            score -= 50  # Heavy penalty for over-qualified positions
        
        # 2. Required skills match (+5 each, max 25)
        all_job_skills = (job.required_skills or []) + (job.nice_to_have_skills or [])
        required_matches = self._skills_match_count(all_job_skills, self.required_skills)
        score += min(required_matches * 5, 25)
        
        # 3. Preferred skills match (+3 each, max 15)
        preferred_matches = self._skills_match_count(all_job_skills, self.preferred_skills)
        score += min(preferred_matches * 3, 15)
        
        # 4. Location match (+15)
        if self._location_matches(job.location):
            score += 15
        
        # 5. Remote match (+10 if user wants remote and job is remote)
        if self.remote_only and job.remote:
            score += 10
        elif not self.remote_only and job.remote:
            score += 5  # Bonus for remote flexibility
        
        # 6. Title exclusion penalty (-40)
        if self._title_has_excluded_keywords(job.job_title):
            score -= 40
        
        # Clamp to 0-100
        score = max(0, min(100, score))
        
        logger.debug(f"Score for {job.job_title}: {score}")
        return score
    
    def filter_jobs(
        self,
        jobs: List[ParsedJob],
        min_score: int = 30,
        usa_only: bool = True
    ) -> List[Tuple[ParsedJob, int]]:
        """
        Filter and score jobs.
        
        Args:
            jobs: List of ParsedJob objects
            min_score: Minimum score to include (default 30)
            usa_only: Only include USA or remote jobs (default True)
            
        Returns:
            List of (job, score) tuples, sorted by score descending
        """
        scored_jobs = []
        location_filtered = 0
        
        for job in jobs:
            # Location filtering (if enabled)
            if usa_only and job.location:
                if not self._is_location_usa_or_remote(job.location):
                    location_filtered += 1
                    logger.debug(f"Filtered out: {job.job_title} @ {job.company} - Location: {job.location}")
                    continue
            
            # Also check if job is remote (always allow remote)
            if usa_only and job.remote:
                # Remote jobs are always allowed
                pass
            elif usa_only and not job.location:
                # If no location specified, allow it (might be remote)
                pass
            
            score = self.calculate_relevance_score(job)
            if score >= min_score:
                scored_jobs.append((job, score))
        
        if location_filtered > 0:
            logger.info(f"Location filtered: {location_filtered} non-USA jobs removed")
        
        # Sort by score descending
        scored_jobs.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Filtered: {len(scored_jobs)}/{len(jobs)} jobs above score {min_score}")
        return scored_jobs
    
    def get_top_matches(
        self,
        jobs: List[ParsedJob],
        top_n: int = 20
    ) -> List[Tuple[ParsedJob, int]]:
        """Get top N jobs by relevance score."""
        all_scored = self.filter_jobs(jobs, min_score=0)
        return all_scored[:top_n]
    
    def explain_score(self, job: ParsedJob) -> Dict[str, Any]:
        """Get detailed score breakdown for a job."""
        breakdown = {
            "job_title": job.job_title,
            "company": job.company,
            "total_score": 0,
            "components": {}
        }
        
        # YOE
        if job.yoe_required <= self.max_yoe:
            breakdown["components"]["yoe_match"] = f"+30 (requires {job.yoe_required}, max {self.max_yoe})"
            breakdown["total_score"] += 30
        else:
            breakdown["components"]["yoe_match"] = f"-50 (requires {job.yoe_required}, max {self.max_yoe})"
            breakdown["total_score"] -= 50
        
        # Skills
        all_skills = (job.required_skills or []) + (job.nice_to_have_skills or [])
        req_matches = self._skills_match_count(all_skills, self.required_skills)
        pref_matches = self._skills_match_count(all_skills, self.preferred_skills)
        
        breakdown["components"]["required_skills"] = f"+{min(req_matches * 5, 25)} ({req_matches} matches)"
        breakdown["components"]["preferred_skills"] = f"+{min(pref_matches * 3, 15)} ({pref_matches} matches)"
        breakdown["total_score"] += min(req_matches * 5, 25) + min(pref_matches * 3, 15)
        
        # Location
        if self._location_matches(job.location):
            breakdown["components"]["location"] = f"+15 ({job.location})"
            breakdown["total_score"] += 15
        else:
            breakdown["components"]["location"] = f"+0 ({job.location})"
        
        # Remote
        if job.remote:
            breakdown["components"]["remote"] = "+5 (remote available)"
            breakdown["total_score"] += 5
        
        # Title exclusion
        if self._title_has_excluded_keywords(job.job_title):
            breakdown["components"]["title_exclusion"] = "-40 (contains excluded keyword)"
            breakdown["total_score"] -= 40
        
        breakdown["total_score"] = max(0, min(100, breakdown["total_score"]))
        
        return breakdown
