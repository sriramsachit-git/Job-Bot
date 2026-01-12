# Quick Start Guide

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Playwright browsers (if using Playwright extraction):**
   ```bash
   playwright install chromium
   ```

3. **Install LaTeX for PDF generation (optional but recommended):**
   ```bash
   # macOS
   brew install --cask mactex
   
   # Ubuntu/Debian/Jetson Nano
   sudo apt-get install texlive-latex-base texlive-latex-extra
   ```

4. **Verify PDF setup:**
   ```bash
   python check_pdf_setup.py
   ```

5. **Set up environment variables:**
   Create a `.env` file with:
   ```
   GOOGLE_API_KEY=your_google_api_key
   GOOGLE_CSE_ID=your_cse_id
   OPENAI_API_KEY=your_openai_api_key
   ```

## Running the Pipeline

### Basic Usage

```bash
# Run daily search (default)
python main.py

# Custom search
python main.py --keywords "AI engineer" "ML engineer" --num-results 50

# View statistics
python main.py --stats
```

### Generate Resumes

```bash
# Interactive mode (selects top 10 jobs)
python generate_resumes.py

# Auto-select projects
python generate_resumes.py --auto

# Specific job
python generate_resumes.py --job-id 42
```

## Running the Web Frontend

### On Jetson Nano

```bash
# Start web server (accessible from network)
python web_app.py --host 0.0.0.0 --port 5000
```

### Access from PC

1. Find Jetson Nano IP: `hostname -I` (on Jetson)
2. Open browser: `http://<jetson-ip>:5000`

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_extractor_extended.py

# Run with coverage
pytest --cov=src tests/
```

## Features Added

### 1. BeautifulSoup Extraction
- Third extraction method added as fallback
- Lightweight HTML parsing for simple pages
- Automatically used when Jina and Playwright fail

### 2. Unextracted Jobs Table
- Failed extractions stored in separate table
- Tracks retry count and methods attempted
- Can be retried later

### 3. Web Frontend
- Flask-based web interface
- View jobs, resumes, and statistics
- Access from any device on network
- Perfect for Jetson Nano + PC setup

### 4. PDF Resume Generation
- LaTeX to PDF compilation
- Automatic cleanup of auxiliary files
- Download via web interface

### 5. Extended Test Suite
- Comprehensive test coverage
- Tests for all new features
- Mock-based testing for external dependencies

## Project Structure

```
job_search_pipeline/
├── main.py                 # Main CLI entry point
├── web_app.py             # Flask web server
├── generate_resumes.py    # Resume generation CLI
├── check_pdf_setup.py     # PDF setup verification
├── src/
│   ├── pipeline.py        # Main pipeline orchestrator
│   ├── extractor.py       # Content extraction (Jina/Playwright/BeautifulSoup)
│   ├── storage.py         # Database operations
│   ├── llm_parser.py      # AI job parsing
│   ├── filters.py         # Relevance filtering
│   └── resume_generator.py # Resume generation
├── tests/                 # Test suite
├── templates/             # Web frontend templates
└── data/                  # Data storage
    ├── jobs.db           # SQLite database
    └── resumes/          # Generated resumes
```

## Next Steps

1. Run a test search: `python main.py --keywords "software engineer"`
2. Check the web interface: `python web_app.py`
3. Generate a resume: `python generate_resumes.py --top 1`
4. View results in the web dashboard
