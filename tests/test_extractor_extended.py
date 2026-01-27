"""
Extended tests for extractor module including BeautifulSoup.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.extractor import ContentExtractor


class TestContentExtractorExtended:
    """Extended test cases for ContentExtractor class."""
    
    def test_extract_with_beautifulsoup_success(self):
        """Test BeautifulSoup extraction with valid HTML."""
        extractor = ContentExtractor()
        
        html_content = """
        <html>
        <body>
            <main>
                <div class="job-description">
                    <h1>Software Engineer - Machine Learning</h1>
                    <p>We are looking for a software engineer with 5+ years of experience in machine learning and artificial intelligence.</p>
                    <p>Requirements: Python, Django, PostgreSQL, TensorFlow, PyTorch, Kubernetes, Docker, AWS, GCP</p>
                    <p>Responsibilities:</p>
                    <ul>
                        <li>Design and implement machine learning models for production systems</li>
                        <li>Collaborate with cross-functional teams to deploy ML solutions</li>
                        <li>Optimize model performance and scalability</li>
                        <li>Build data pipelines for training and inference</li>
                        <li>Monitor and maintain ML systems in production</li>
                        <li>Research and implement state-of-the-art ML techniques</li>
                        <li>Work with large-scale distributed systems</li>
                        <li>Participate in code reviews and technical discussions</li>
                    </ul>
                    <p>Nice to have: Experience with LLMs, RAG systems, vector databases, MLOps tools</p>
                    <p>Location: San Francisco, CA (Remote OK)</p>
                    <p>Compensation: Competitive salary and equity package</p>
                </div>
            </main>
        </body>
        </html>
        """
        
        with patch('src.extractor.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.content = html_content.encode()
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            content = extractor.extract_with_beautifulsoup("https://example.com/job")
            assert content is not None
            assert "Software Engineer" in content
            assert "Python" in content
    
    def test_extract_with_beautifulsoup_insufficient_content(self):
        """Test BeautifulSoup extraction with insufficient content."""
        extractor = ContentExtractor()
        
        html_content = "<html><body><p>Short</p></body></html>"
        
        with patch('src.extractor.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.content = html_content.encode()
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            content = extractor.extract_with_beautifulsoup("https://example.com/job")
            assert content is None
    
    def test_extract_with_beautifulsoup_request_error(self):
        """Test BeautifulSoup extraction with request error."""
        extractor = ContentExtractor()
        
        with patch('src.extractor.requests.get') as mock_get:
            mock_get.side_effect = Exception("Connection error")
            
            content = extractor.extract_with_beautifulsoup("https://example.com/job")
            assert content is None
    
    def test_smart_extract_fallback_to_beautifulsoup(self):
        """Test that smart_extract falls back to BeautifulSoup."""
        extractor = ContentExtractor()
        
        html_content = """
        <html>
        <body>
            <main class="job-content">
                <h1>Senior Machine Learning Engineer</h1>
                <p>This is a detailed job description with enough content to pass the minimum length requirement of 500 characters.</p>
                <p>We are seeking an experienced ML Engineer to join our team and work on cutting-edge AI projects.</p>
                <p>Requirements include:</p>
                <ul>
                    <li>5+ years of experience in machine learning and deep learning</li>
                    <li>Strong proficiency in Python, PyTorch, and TensorFlow</li>
                    <li>Experience with distributed training and model deployment</li>
                    <li>Knowledge of cloud platforms like AWS, GCP, or Azure</li>
                    <li>Understanding of MLOps practices and tools</li>
                    <li>Experience with large language models and transformer architectures</li>
                    <li>Strong problem-solving and communication skills</li>
                </ul>
                <p>You will work on exciting projects involving natural language processing, computer vision, and recommendation systems.</p>
                <p>We offer competitive compensation, comprehensive benefits, and a collaborative work environment.</p>
            </main>
        </body>
        </html>
        """
        
        with patch.object(extractor, 'extract_with_jina', return_value=None), \
             patch.object(extractor, 'extract_with_playwright', return_value=None), \
             patch('src.extractor.requests.get') as mock_get:
            
            mock_response = Mock()
            mock_response.content = html_content.encode()
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            content, method = extractor.smart_extract("https://example.com/job")
            assert content is not None
            assert method == "beautifulsoup"
    
    def test_extract_batch_with_failures(self):
        """Test batch extraction with some failures."""
        extractor = ContentExtractor()
        
        urls = [
            "https://example.com/job1",
            "https://example.com/job2",
            "https://example.com/job3"
        ]
        
        with patch.object(extractor, 'smart_extract') as mock_extract:
            mock_extract.side_effect = [
                ("Content 1", "jina"),
                (None, "failed"),
                ("Content 3", "beautifulsoup")
            ]
            
            results = extractor.extract_batch(urls, delay=0)
            
            assert len(results) == 3
            assert results[0]["success"] is True
            assert results[1]["success"] is False
            assert results[2]["success"] is True
            assert results[2]["method"] == "beautifulsoup"
