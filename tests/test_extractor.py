"""
Tests for extractor module.
"""

import pytest
from unittest.mock import Mock, patch
from src.extractor import ContentExtractor


class TestContentExtractor:
    """Test cases for ContentExtractor class."""
    
    def test_get_domain_simple(self):
        """Test domain extraction from simple URL."""
        extractor = ContentExtractor()
        domain = extractor.get_domain("https://greenhouse.io/jobs/123")
        assert domain == "greenhouse.io"
    
    def test_get_domain_subdomain(self):
        """Test domain extraction from URL with subdomain."""
        extractor = ContentExtractor()
        domain = extractor.get_domain("https://jobs.greenhouse.io/123")
        assert domain == "greenhouse.io"
    
    def test_get_domain_www(self):
        """Test domain extraction removes www."""
        extractor = ContentExtractor()
        domain = extractor.get_domain("https://www.greenhouse.io/jobs")
        assert domain == "greenhouse.io"
    
    def test_needs_playwright_greenhouse(self):
        """Test Playwright detection for Greenhouse."""
        extractor = ContentExtractor()
        assert extractor.needs_playwright("https://greenhouse.io/jobs/123")
    
    def test_needs_playwright_regular_site(self):
        """Test Playwright detection for regular site."""
        extractor = ContentExtractor()
        assert not extractor.needs_playwright("https://example.com/jobs")
