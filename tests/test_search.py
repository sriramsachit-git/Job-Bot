"""
Tests for search module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.search import GoogleJobSearch


class TestGoogleJobSearch:
    """Test cases for GoogleJobSearch class."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        with patch('src.search.config') as mock_config:
            mock_config.api_key = "test_api_key"
            mock_config.cx_id = "test_cse_id"
            yield mock_config
    
    def test_init_missing_api_key(self):
        """Test initialization fails without API key."""
        with patch('src.search.config') as mock_config:
            mock_config.api_key = ""
            mock_config.cx_id = "test_cse_id"
            with pytest.raises(ValueError, match="Google API key and CSE ID are required"):
                GoogleJobSearch()
    
    def test_build_query_single_keyword(self, mock_config):
        """Test building query with single keyword."""
        searcher = GoogleJobSearch()
        query = searcher.build_query(["AI engineer"])
        assert "AI engineer" in query
        assert "site:" in query
    
    def test_build_query_multiple_keywords(self, mock_config):
        """Test building query with multiple keywords."""
        searcher = GoogleJobSearch()
        query = searcher.build_query(["AI engineer", "ML engineer"])
        assert "AI engineer" in query
        assert "ML engineer" in query
        assert "OR" in query
    
    def test_build_query_with_sites(self, mock_config):
        """Test building query with custom sites."""
        searcher = GoogleJobSearch()
        query = searcher.build_query(["engineer"], sites=["greenhouse.io"])
        assert "site:greenhouse.io" in query
    
    def test_build_query_no_keywords(self, mock_config):
        """Test building query fails without keywords."""
        searcher = GoogleJobSearch()
        with pytest.raises(ValueError, match="At least one keyword is required"):
            searcher.build_query([])
