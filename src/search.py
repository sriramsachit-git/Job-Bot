"""
Google Custom Search API wrapper for job searching.
Uses the official Google API Python client library.
"""

import logging
from typing import List, Dict, Optional, Any
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.config import config, DEFAULT_JOB_SITES

logger = logging.getLogger(__name__)
console = Console()


class GoogleJobSearch:
    """
    Google Custom Search API wrapper for job searching.
    
    Uses the official googleapiclient library for API calls.
    Supports Boolean queries, date filtering, and pagination.
    """
    
    def __init__(self, api_key: Optional[str] = None, cse_id: Optional[str] = None):
        """
        Initialize the Google Job Search client.
        
        Args:
            api_key: Google API key. Defaults to config.api_key
            cse_id: Custom Search Engine ID. Defaults to config.cx_id
        """
        self.api_key = api_key or config.api_key
        self.cse_id = cse_id or config.cx_id
        
        if not self.api_key or not self.cse_id:
            raise ValueError("Google API key and CSE ID are required")
        
        # Build the Custom Search API service
        self.service = build("customsearch", "v1", developerKey=self.api_key)
        logger.info("GoogleJobSearch initialized successfully")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((HttpError, ConnectionError)),
        before_sleep=lambda retry_state: logger.warning(
            f"Retrying search (attempt {retry_state.attempt_number})..."
        )
    )
    def _execute_search(self, **kwargs) -> Dict[str, Any]:
        """
        Execute a single search request with retry logic.
        
        Args:
            **kwargs: Arguments to pass to the CSE list() method
            
        Returns:
            API response dictionary
        """
        try:
            result = self.service.cse().list(cx=self.cse_id, **kwargs).execute()
            return result
        except HttpError as e:
            logger.error(f"Google API error: {e}")
            raise
    
    def search(
        self,
        query: str,
        date_restrict: str = "d1",
        num_results: int = 50
    ) -> List[Dict[str, str]]:
        """
        Search Google Custom Search API with pagination.
        
        Args:
            query: Search query string (supports Boolean operators)
            date_restrict: Date filter - "d1" (day), "w1" (week), "m1" (month)
            num_results: Maximum number of results to return (max 100)
            
        Returns:
            List of search results with title, link, snippet, displayLink
        """
        all_results: List[Dict[str, str]] = []
        num_results = min(num_results, 100)  # Google API hard limit
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task(f"Searching: {query[:50]}...", total=None)
            
            # Paginate through results (10 per page)
            for start_index in range(1, num_results + 1, 10):
                try:
                    response = self._execute_search(
                        q=query,
                        dateRestrict=date_restrict,
                        start=start_index,
                        num=min(10, num_results - len(all_results))
                    )
                    
                    items = response.get("items", [])
                    if not items:
                        logger.info(f"No more results at index {start_index}")
                        break
                    
                    for item in items:
                        all_results.append({
                            "title": item.get("title", ""),
                            "link": item.get("link", ""),
                            "snippet": item.get("snippet", ""),
                            "displayLink": item.get("displayLink", "")
                        })
                    
                    progress.update(task, description=f"Found {len(all_results)} results...")
                    
                    # Check if we have enough results
                    if len(all_results) >= num_results:
                        break
                        
                except HttpError as e:
                    if "rateLimitExceeded" in str(e):
                        logger.error("Rate limit exceeded. Please wait and try again.")
                        break
                    raise
        
        logger.info(f"Search completed: {len(all_results)} results found")
        return all_results
    
    def build_query(
        self,
        keywords: List[str],
        sites: Optional[List[str]] = None
    ) -> str:
        """
        Build a Boolean search query for job searching.
        
        Args:
            keywords: List of job title keywords to search for
            sites: List of job board domains to search. Defaults to DEFAULT_JOB_SITES
            
        Returns:
            Formatted Boolean query string
            
        Example:
            keywords=["AI engineer", "ML engineer"]
            sites=["greenhouse.io", "lever.co"]
            Returns: "(AI engineer OR ML engineer) (site:greenhouse.io OR site:lever.co)"
        """
        if not keywords:
            raise ValueError("At least one keyword is required")
        
        sites = sites or DEFAULT_JOB_SITES
        
        # Build keywords part: (kw1 OR kw2 OR kw3)
        keywords_query = " OR ".join([f'"{kw}"' if " " in kw else kw for kw in keywords])
        keywords_part = f"({keywords_query})"
        
        # Build sites part: (site:s1 OR site:s2)
        if sites:
            sites_query = " OR ".join([f"site:{site}" for site in sites])
            sites_part = f"({sites_query})"
            query = f"{keywords_part} {sites_part}"
        else:
            query = keywords_part
        
        logger.debug(f"Built query: {query}")
        return query
    
    def search_jobs(
        self,
        keywords: List[str],
        sites: Optional[List[str]] = None,
        date_restrict: str = "d1",
        num_results: int = 50
    ) -> List[Dict[str, str]]:
        """
        Convenience method to search for jobs with keywords and sites.
        
        Args:
            keywords: List of job title keywords
            sites: List of job board domains (optional)
            date_restrict: Date filter - "d1", "w1", "m1"
            num_results: Maximum results to return
            
        Returns:
            List of search results
        """
        query = self.build_query(keywords, sites)
        console.print(f"[cyan]Query: {query}[/cyan]")
        return self.search(query, date_restrict, num_results)
    
    def get_search_stats(self, query: str) -> Dict[str, Any]:
        """
        Get search statistics without fetching all results.
        
        Args:
            query: Search query string
            
        Returns:
            Dictionary with totalResults and searchTime
        """
        response = self._execute_search(q=query, num=1)
        return {
            "totalResults": response.get("searchInformation", {}).get("totalResults", 0),
            "searchTime": response.get("searchInformation", {}).get("searchTime", 0)
        }
