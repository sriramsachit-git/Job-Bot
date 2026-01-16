"""
Web content extraction module.
Supports multiple extraction methods: Jina Reader, Playwright, and BeautifulSoup.
Automatically routes to the best method based on the target site.
"""

import logging
import time
from typing import Optional, Tuple, List, Dict, Any
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn

from src.config import JS_HEAVY_SITES, JINA_FRIENDLY_SITES, config

logger = logging.getLogger(__name__)
console = Console()


class ContentExtractor:
    """
    Multi-source web content extractor.
    
    Automatically routes extraction requests to the most appropriate method:
    - Jina Reader: Fast, works for most sites
    - Playwright: For JavaScript-heavy sites (Greenhouse, Lever, etc.)
    - BeautifulSoup: Fallback for simple HTML pages
    
    Includes fallback logic if primary method fails.
    """
    
    # CSS selectors to try when extracting job content (in order of specificity)
    JOB_SELECTORS = [
        '[data-testid="job-description"]',
        '[data-testid="posting-description"]',
        '.job-description',
        '.posting-description',
        '.job-content',
        '.content-wrapper',
        '.job-details',
        '#job-description',
        '#job-content',
        'article.job',
        'article',
        'main',
        '.main-content',
        'body'
    ]
    
    def __init__(self):
        """Initialize the content extractor."""
        self._playwright_browser = None
        logger.info("ContentExtractor initialized")
    
    @staticmethod
    def get_domain(url: str) -> str:
        """
        Extract the base domain from a URL.
        
        Handles subdomains: job-boards.greenhouse.io -> greenhouse.io
        
        Args:
            url: Full URL string
            
        Returns:
            Base domain string
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
            
            # Handle subdomains (e.g., job-boards.greenhouse.io -> greenhouse.io)
            parts = domain.split(".")
            if len(parts) > 2:
                # Keep last two parts for common TLDs
                return ".".join(parts[-2:])
            return domain
        except Exception as e:
            logger.error(f"Error parsing URL {url}: {e}")
            return ""
    
    def needs_playwright(self, url: str) -> bool:
        """
        Check if URL requires JavaScript rendering.
        
        Args:
            url: URL to check
            
        Returns:
            True if Playwright should be used
        """
        domain = self.get_domain(url)
        return any(js_site in domain for js_site in JS_HEAVY_SITES)
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5)
    )
    def extract_with_jina(self, url: str, timeout: int = 15) -> Optional[str]:
        """
        Extract content using Jina Reader API.
        
        Jina Reader converts web pages to clean markdown text.
        Fast and works for most non-JS sites.
        
        Args:
            url: URL to extract
            timeout: Request timeout in seconds
            
        Returns:
            Extracted text content or None if failed
        """
        try:
            jina_url = f"https://r.jina.ai/{url}"
            logger.debug(f"Fetching via Jina: {url}")
            
            response = requests.get(jina_url, timeout=timeout)
            response.raise_for_status()
            
            content = response.text
            
            # Validate content length
            if len(content) > 500:
                logger.debug(f"Jina extraction successful: {len(content)} chars")
                return content
            else:
                logger.warning(f"Jina returned insufficient content: {len(content)} chars")
                return None
                
        except requests.RequestException as e:
            logger.warning(f"Jina extraction failed for {url}: {e}")
            return None
    
    def extract_with_playwright(self, url: str, timeout: int = 20000) -> Optional[str]:
        """
        Extract content using Playwright browser automation.
        
        Required for JavaScript-heavy sites that render content client-side.
        Slower but more reliable for dynamic content.
        
        Args:
            url: URL to extract
            timeout: Page load timeout in milliseconds
            
        Returns:
            Extracted text content or None if failed
        """
        try:
            from playwright.sync_api import sync_playwright
            
            logger.debug(f"Fetching via Playwright: {url}")
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                page = context.new_page()
                
                try:
                    # Navigate to page
                    page.goto(url, timeout=timeout, wait_until="domcontentloaded")
                    
                    # Wait for JavaScript to load content
                    page.wait_for_timeout(3000)
                    
                    # Try each selector until we find good content
                    content = None
                    for selector in self.JOB_SELECTORS:
                        try:
                            element = page.query_selector(selector)
                            if element:
                                text = element.inner_text()
                                if len(text) > 500:
                                    content = text
                                    logger.debug(f"Found content with selector: {selector}")
                                    break
                        except Exception:
                            continue
                    
                    if content:
                        logger.debug(f"Playwright extraction successful: {len(content)} chars")
                        return content
                    else:
                        # Fallback to full body text
                        body_text = page.inner_text("body")
                        if len(body_text) > 500:
                            return body_text
                        logger.warning(f"Playwright found insufficient content")
                        return None
                        
                finally:
                    browser.close()
                    
        except ImportError:
            logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
            return None
        except Exception as e:
            logger.error(f"Playwright extraction failed for {url}: {e}")
            return None
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5)
    )
    def extract_with_beautifulsoup(self, url: str, timeout: int = 15) -> Optional[str]:
        """
        Extract content using BeautifulSoup HTML parsing.
        
        Lightweight fallback method for simple HTML pages.
        No JavaScript execution, just HTML parsing.
        
        Args:
            url: URL to extract
            timeout: Request timeout in seconds
            
        Returns:
            Extracted text content or None if failed
        """
        try:
            logger.debug(f"Fetching via BeautifulSoup: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            
            # Try each selector until we find good content
            content = None
            for selector in self.JOB_SELECTORS:
                try:
                    elements = soup.select(selector)
                    if elements:
                        # Get text from all matching elements
                        text = ' '.join([elem.get_text(separator=' ', strip=True) for elem in elements])
                        if len(text) > 500:
                            content = text
                            logger.debug(f"Found content with selector: {selector}")
                            break
                except Exception:
                    continue
            
            if content:
                logger.debug(f"BeautifulSoup extraction successful: {len(content)} chars")
                return content
            
            # Fallback: get main content or body text
            main = soup.find('main') or soup.find('article') or soup.find('body')
            if main:
                text = main.get_text(separator=' ', strip=True)
                # Clean up excessive whitespace
                text = ' '.join(text.split())
                if len(text) > 500:
                    logger.debug(f"BeautifulSoup fallback extraction successful: {len(text)} chars")
                    return text
            
            logger.warning(f"BeautifulSoup found insufficient content")
            return None
                
        except requests.RequestException as e:
            logger.warning(f"BeautifulSoup extraction failed for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"BeautifulSoup parsing error for {url}: {e}")
            return None
    
    def smart_extract(self, url: str) -> Tuple[Optional[str], str]:
        """
        Intelligently extract content using the best method for the URL.
        
        Routes to Playwright for JS-heavy sites, Jina for others.
        Falls back to alternative method if primary fails.
        
        Args:
            url: URL to extract
            
        Returns:
            Tuple of (content, method_used)
            method_used is one of: "jina", "playwright", "failed"
        """
        domain = self.get_domain(url)
        logger.info(f"Extracting from {domain}...")
        
        # Route 1: JS-heavy sites -> Playwright first
        if self.needs_playwright(url):
            content = self.extract_with_playwright(url)
            if content:
                return content, "playwright"
            
            # Fallback to Jina
            content = self.extract_with_jina(url)
            if content:
                return content, "jina"
            
            # Final fallback to BeautifulSoup
            content = self.extract_with_beautifulsoup(url)
            if content:
                return content, "beautifulsoup"
        
        # Route 2: Other sites -> Jina first
        else:
            content = self.extract_with_jina(url)
            if content:
                return content, "jina"
            
            # Fallback to Playwright
            content = self.extract_with_playwright(url)
            if content:
                return content, "playwright"
            
            # Final fallback to BeautifulSoup
            content = self.extract_with_beautifulsoup(url)
            if content:
                return content, "beautifulsoup"
        
        logger.warning(f"All extraction methods failed for {url}")
        return None, "failed"
    
    def extract_batch(
        self,
        urls: List[str],
        delay: float = 1.0,
        max_batch_size: Optional[int] = None,
        parallel: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Extract content from multiple URLs.
        
        Args:
            urls: List of URLs to extract
            delay: Delay between requests in seconds
            max_batch_size: Maximum number of URLs to process (None = all)
            parallel: Use parallel processing (experimental)
            
        Returns:
            List of dicts with: url, content, method, success, error
        """
        # Limit batch size if specified
        if max_batch_size and len(urls) > max_batch_size:
            logger.info(f"Limiting batch to {max_batch_size} URLs (from {len(urls)})")
            urls = urls[:max_batch_size]
        
        results: List[Dict[str, Any]] = []
        
        # Parallel extraction (experimental)
        if parallel and len(urls) > 1:
            return self._extract_batch_parallel(urls, delay)
        
        # Sequential extraction (default)
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Extracting content...", total=len(urls))
            
            for i, url in enumerate(urls):
                try:
                    content, method = self.smart_extract(url)
                    
                    results.append({
                        "url": url,
                        "content": content,
                        "method": method,
                        "success": content is not None,
                        "error": None
                    })
                    
                    if content:
                        progress.update(task, description=f"✓ Extracted ({method})")
                    else:
                        progress.update(task, description=f"✗ Failed")
                        
                except Exception as e:
                    logger.error(f"Error extracting {url}: {e}")
                    results.append({
                        "url": url,
                        "content": None,
                        "method": "error",
                        "success": False,
                        "error": str(e)
                    })
                
                progress.advance(task)
                
                # Rate limiting
                if i < len(urls) - 1:
                    time.sleep(delay)
        
        # Log summary
        successful = sum(1 for r in results if r["success"])
        console.print(f"[green]Extracted: {successful}/{len(urls)} URLs[/green]")
        
        return results
    
    def _extract_batch_parallel(self, urls: List[str], delay: float) -> List[Dict[str, Any]]:
        """Extract content in parallel using ThreadPoolExecutor."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results: List[Dict[str, Any]] = []
        max_workers = min(5, len(urls))  # Limit concurrent requests
        
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Extracting content (parallel)...", total=len(urls))
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_url = {
                    executor.submit(self.smart_extract, url): url 
                    for url in urls
                }
                
                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        content, method = future.result()
                        results.append({
                            "url": url,
                            "content": content,
                            "method": method,
                            "success": content is not None,
                            "error": None
                        })
                        if content:
                            progress.update(task, description=f"✓ Extracted ({method})")
                    except Exception as e:
                        logger.error(f"Error extracting {url}: {e}")
                        results.append({
                            "url": url,
                            "content": None,
                            "method": "error",
                            "success": False,
                            "error": str(e)
                        })
                    
                    progress.advance(task)
                    time.sleep(delay)  # Rate limiting
        
        # Sort results to match input order
        url_to_result = {r["url"]: r for r in results}
        results = [url_to_result[url] for url in urls if url in url_to_result]
        
        successful = sum(1 for r in results if r["success"])
        console.print(f"[green]Extracted: {successful}/{len(urls)} URLs (parallel)[/green]")
        
        return results