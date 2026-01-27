"""
Extended tests for pipeline module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.pipeline import JobSearchPipeline
from src.llm_parser import ParsedJob
from src.usage_tracker import UsageTracker


class TestPipelineExtended:
    """Extended test cases for JobSearchPipeline class."""
    
    @pytest.fixture
    def mock_pipeline(self):
        """Create a mock pipeline for testing."""
        # Create pipeline instance properly
        pipeline = JobSearchPipeline.__new__(JobSearchPipeline)  # Create without calling __init__
        pipeline.searcher = Mock()
        pipeline.extractor = Mock()
        pipeline.parser = Mock()
        pipeline.db = Mock()
        pipeline.filter = Mock()
        pipeline.pre_filter = None  # Disable pre-filtering for test
        pipeline.usage_tracker = None
        return pipeline
    
    def test_pipeline_stores_failed_extractions(self, mock_pipeline):
        """Test that pipeline stores failed extractions."""
        # Mock search results (these become filtered_results after early filtering)
        search_results = [
            {"link": "https://example.com/job1", "title": "Job 1", "snippet": "Snippet 1", "displayLink": "example.com"},
            {"link": "https://example.com/job2", "title": "Job 2", "snippet": "Snippet 2", "displayLink": "example.com"}
        ]
        mock_pipeline.searcher.search_jobs.return_value = search_results
        
        # Mock early filtering to pass all results
        mock_pipeline.filter.should_skip_early = Mock(return_value=False)
        
        # Mock extraction results (one success, one failure)
        extraction_results = [
            {"url": "https://example.com/job1", "content": "Content 1", "method": "jina", "success": True, "error": None},
            {"url": "https://example.com/job2", "content": None, "method": "failed", "success": False, "error": "Failed"}
        ]
        mock_pipeline.extractor.extract_batch.return_value = extraction_results
        mock_pipeline.extractor.get_domain.return_value = "example.com"
        
        # Mock parser (only for successful extraction)
        # parse_batch returns (jobs, token_usage) tuple
        mock_pipeline.parser.parse_batch.return_value = (
            [
                ParsedJob(
                    job_title="Job 1",
                    company="Company 1",
                    source_url="https://example.com/job1",
                    source_domain="example.com"
                )
            ],
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
        )
        
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
        
        # Mock UsageTracker creation
        with patch('src.pipeline.UsageTracker') as mock_tracker_class:
            mock_tracker = Mock()
            mock_tracker.set_google_usage = Mock()
            mock_tracker.log_extraction = Mock()
            mock_tracker.log_openai_request = Mock()
            mock_tracker_class.return_value = mock_tracker
            
            # Mock console to avoid print statements
            with patch('src.pipeline.console') as mock_console:
                mock_console.print = Mock()
                
                # Run pipeline
                summary = mock_pipeline.run(
                    keywords=["software engineer"],
                    num_results=2,
                    min_score=30
                )
        
        # Verify failed extraction was saved
        assert mock_pipeline.db.save_unextracted_job.called, "save_unextracted_job should have been called"
        call_args = mock_pipeline.db.save_unextracted_job.call_args
        assert call_args[1]["url"] == "https://example.com/job2"
        assert call_args[1]["methods_attempted"] == ["failed"]
