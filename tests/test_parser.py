"""
Tests for LLM parser module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.llm_parser import JobParser, ParsedJob


class TestJobParser:
    """Test cases for JobParser class."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        with patch('src.llm_parser.config') as mock_config:
            mock_config.openai_api_key = "test_openai_key"
            yield mock_config
    
    def test_init_missing_api_key(self):
        """Test initialization fails without API key."""
        with patch('src.llm_parser.config') as mock_config:
            mock_config.openai_api_key = ""
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                JobParser()
    
    def test_extract_job_details_short_content(self, mock_config):
        """Test extraction fails with too short content."""
        parser = JobParser()
        result = parser.extract_job_details("short", "https://example.com/job")
        assert result is None
    
    def test_parsed_job_model(self):
        """Test ParsedJob model validation."""
        job = ParsedJob(
            job_title="Software Engineer",
            company="Test Company",
            source_url="https://example.com/job",
            source_domain="example.com"
        )
        assert job.job_title == "Software Engineer"
        assert job.company == "Test Company"
        assert job.yoe_required == 0  # Default value
