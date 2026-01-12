"""
Integration test for job search pipeline.
Tests extraction and parsing on real job posting URLs.
"""

import pytest
from src.extractor import ContentExtractor
from src.llm_parser import JobParser, ParsedJob
from src.filters import JobFilter
from src.storage import JobDatabase
import tempfile
import os


class TestFullPipeline:
    """Integration tests with real job URLs."""

    @pytest.fixture
    def extractor(self):
        return ContentExtractor()

    @pytest.fixture
    def parser(self):
        return JobParser()

    @pytest.fixture
    def job_filter(self):
        return JobFilter()

    @pytest.fixture
    def temp_db(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name
        db = JobDatabase(db_path)
        yield db
        db.close()
        os.unlink(db_path)

    # Real job posting URLs for testing (update these if they expire)
    REAL_JOB_URLS = [
        "https://jobs.lever.co/anthropic/e3cde481-d446-460f-b576-93cab67bd1ed",
        "https://boards.greenhouse.io/openai/jobs/5000118",
    ]

    def test_extractor_gets_content(self, extractor):
        """Test that extractor retrieves content from job pages."""
        url = self.REAL_JOB_URLS[0]
        content, method = extractor.smart_extract(url)
        
        assert content is not None, f"Failed to extract content from {url}"
        assert len(content) > 500, "Content too short"
        assert method in ["jina", "playwright"], f"Unknown method: {method}"
        print(f"\n✓ Extracted {len(content)} chars via {method}")

    def test_parser_extracts_job_details(self, extractor, parser):
        """Test that parser extracts structured job data."""
        url = self.REAL_JOB_URLS[0]
        content, _ = extractor.smart_extract(url)
        
        assert content is not None, "Extraction failed"
        
        job = parser.extract_job_details(content, url)
        
        assert job is not None, "Parsing failed"
        assert isinstance(job, ParsedJob)
        assert job.job_title, "Missing job title"
        assert job.company, "Missing company"
        assert job.source_url == url
        assert isinstance(job.yoe_required, int)
        
        print(f"\n✓ Parsed job:")
        print(f"  Title: {job.job_title}")
        print(f"  Company: {job.company}")
        print(f"  Location: {job.location}")
        print(f"  YOE Required: {job.yoe_required}")
        print(f"  Remote: {job.remote}")
        print(f"  Required Skills: {job.required_skills[:5] if job.required_skills else []}")

    def test_filter_scores_job(self, extractor, parser, job_filter):
        """Test that filter calculates relevance score."""
        url = self.REAL_JOB_URLS[0]
        content, _ = extractor.smart_extract(url)
        job = parser.extract_job_details(content, url)
        
        assert job is not None, "Parsing failed"
        
        score = job_filter.calculate_relevance_score(job)
        
        assert isinstance(score, int)
        assert 0 <= score <= 100
        
        breakdown = job_filter.explain_score(job)
        print(f"\n✓ Score: {score}/100")
        print(f"  Breakdown: {breakdown['components']}")

    def test_storage_saves_job(self, extractor, parser, job_filter, temp_db):
        """Test that storage saves and retrieves jobs."""
        url = self.REAL_JOB_URLS[0]
        content, _ = extractor.smart_extract(url)
        job = parser.extract_job_details(content, url)
        score = job_filter.calculate_relevance_score(job)
        
        # Save
        saved = temp_db.save_job(job, relevance_score=score)
        assert saved is True, "Failed to save job"
        
        # Retrieve
        jobs = temp_db.get_jobs()
        assert len(jobs) == 1
        assert jobs[0]['title'] == job.job_title
        assert jobs[0]['relevance_score'] == score
        
        print(f"\n✓ Saved and retrieved job from DB")

    def test_full_pipeline_flow(self, extractor, parser, job_filter, temp_db):
        """Test complete pipeline: extract -> parse -> score -> save."""
        results = []
        
        for url in self.REAL_JOB_URLS:
            # Extract
            content, method = extractor.smart_extract(url)
            if not content:
                print(f"⚠ Skipping {url} - extraction failed")
                continue
            
            # Parse
            job = parser.extract_job_details(content, url)
            if not job:
                print(f"⚠ Skipping {url} - parsing failed")
                continue
            
            # Score
            score = job_filter.calculate_relevance_score(job)
            
            # Save
            temp_db.save_job(job, relevance_score=score)
            
            results.append({
                'title': job.job_title,
                'company': job.company,
                'yoe': job.yoe_required,
                'score': score
            })
        
        assert len(results) > 0, "No jobs processed successfully"
        
        print(f"\n✓ Processed {len(results)} jobs:")
        for r in results:
            print(f"  [{r['score']}] {r['title']} @ {r['company']} (YOE: {r['yoe']})")


class TestYOEExtraction:
    """Focused tests for YOE extraction accuracy."""

    @pytest.fixture
    def parser(self):
        return JobParser()

    def test_yoe_parsing_from_text(self, parser):
        """Test YOE extraction from sample job text."""
        sample_content = """
        Software Engineer - Machine Learning
        
        Company: TechCorp Inc.
        Location: San Francisco, CA (Remote OK)
        
        About the role:
        We're looking for an ML Engineer to join our team.
        
        Requirements:
        - 3+ years of experience in machine learning
        - Strong Python skills
        - Experience with PyTorch or TensorFlow
        - BS/MS in Computer Science
        
        Nice to have:
        - Experience with LLMs
        - Kubernetes knowledge
        """
        
        job = parser.extract_job_details(sample_content, "https://example.com/job/123")
        
        assert job is not None
        assert job.yoe_required == 3, f"Expected YOE=3, got {job.yoe_required}"
        print(f"\n✓ Correctly extracted YOE: {job.yoe_required}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])