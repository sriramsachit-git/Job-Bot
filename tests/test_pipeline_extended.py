"""
Extended tests for pipeline module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.pipeline import JobSearchPipeline
from src.llm_parser import ParsedJob


class TestPipelineExtended:
    """Extended test cases for JobSearchPipeline class."""
    
    @pytest.fixture
    def mock_pipeline(self):
        """Create a mock pipeline for testing."""
        with patch('src.pipeline.JobSearchPipeline.__init__', lambda x: None):
            pipeline = JobSearchPipeline()
            pipeline.searcher = Mock()
            pipeline.extractor = Mock()
            pipeline.parser = Mock()
            pipeline.db = Mock()
            pipeline.filter = Mock()
            return pipeline
    
    def test_pipeline_stores_failed_extractions(self, mock_pipeline):
        """Test that pipeline stores failed extractions."""
        # Mock search results
        mock_pipeline.searcher.search_jobs.return_value = [
            {"link": "https://example.com/job1", "title": "Job 1", "snippet": "Snippet 1"},
            {"link": "https://example.com/job2", "title": "Job 2", "snippet": "Snippet 2"}
        ]
        
        # Mock extraction results (one success, one failure)
        mock_pipeline.extractor.extract_batch.return_value = [
            {"url": "https://example.com/job1", "content": "Content 1", "method": "jina", "success": True, "error": None},
            {"url": "https://example.com/job2", "content": None, "method": "failed", "success": False, "error": "Failed"}
        ]
        mock_pipeline.extractor.get_domain.return_value = "example.com"
        
        # Mock parser
        mock_pipeline.parser.parse_batch.return_value = [
            ParsedJob(
                job_title="Job 1",
                company="Company 1",
                source_url="https://example.com/job1",
                source_domain="example.com"
            )
        ]
        
        # Mock filter
        mock_pipeline.filter.filter_jobs.return_value = [
            (ParsedJob(
                job_title="Job 1",
                company="Company 1",
                source_url="https://example.com/job1",
                source_domain="example.com"
            ), 50)
        ]
        
        # Mock database
        mock_pipeline.db.save_batch.return_value = (1, 0)
        mock_pipeline.db.get_new_jobs_since.return_value = []
        mock_pipeline.db.export_csv = Mock()
        
        # Run pipeline
        summary = mock_pipeline.run(
            keywords=["software engineer"],
            num_results=2,
            min_score=30
        )
        
        # Verify failed extraction was saved
        assert mock_pipeline.db.save_unextracted_job.called
        call_args = mock_pipeline.db.save_unextracted_job.call_args
        assert call_args[1]["url"] == "https://example.com/job2"
        assert call_args[1]["methods_attempted"] == ["failed"]
