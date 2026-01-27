# 🔍 Job Search Pipeline

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Automated job search, extraction, and filtering pipeline for AI/ML engineering positions.**

This pipeline automates the tedious process of searching job boards, extracting job details, and filtering relevant positions based on your profile. It supports 30+ ATS platforms including Greenhouse, Lever, Workday, and more.

---

## 🎯 Features

- **🔍 Smart Search** - Google Custom Search API with Boolean query support, comprehensive matrix search
- **📄 Multi-Source Extraction** - Three extraction methods: Jina Reader, Playwright, and BeautifulSoup with automatic fallback
- **🤖 AI-Powered Parsing** - GPT-4o-mini extracts structured job data with high accuracy
- **💰 Pre-Parse Filtering** - Regex-based filtering saves 20-40% on LLM costs by filtering disqualifying jobs before expensive API calls
- **📊 Skill Tracking** - Tracks skill demand across job categories (Data Scientist, ML Engineer, AI Engineer, etc.)
- **🎯 Relevance Scoring** - Scores jobs based on YOE, skills, location, and preferences
- **💾 Persistent Storage** - SQLite database with deduplication and failed extraction tracking
- **📊 CSV Export** - Export results for spreadsheet analysis
- **📄 Smart Resume Generation** - AI-powered tailored resume generation with dynamic skill selection and PDF output
- **🌐 Web Frontend** - FastAPI backend with React frontend (Flask also available for simple deployments)
- **📋 Unextracted Jobs Tracking** - Never lose a job posting - failed extractions saved for retry
- **📈 Usage Tracking** - Automatic API usage and cost tracking with historical reports
- **⚡ Rate Limiting** - Built-in retry logic and respectful rate limiting

---

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Entry Points](#-entry-points)
- [Daily Automation](#-daily-automation)
- [Resume Generation](#-resume-generation)
- [Web Frontend](#-web-frontend)
- [Customization](#-customization)
- [API Keys Setup](#-api-keys-setup)
- [Supported Job Sites](#-supported-job-sites)
- [Architecture](#-architecture)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/job_search_pipeline.git
cd job_search_pipeline

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 4. Configure API keys
cp .env.example .env
# Edit .env with your API keys (see API Keys Setup section)

# 5. Run daily search
python main.py --daily

# 6. (Optional) Install LaTeX for PDF resume generation
# macOS: brew install --cask mactex
# Ubuntu/Debian: sudo apt-get install texlive-latex-base texlive-latex-extra

# 7. (Optional) Start web frontend
# Option A: FastAPI + React (recommended)
cd backend && uvicorn app.main:app --reload
cd frontend && npm install && npm start

# Option B: Flask (simple, deprecated)
python web_app.py --host 0.0.0.0 --port 5000
```

---

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- Google Cloud account (for Custom Search API)
- OpenAI API key

### Step-by-Step Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/job_search_pipeline.git
   cd job_search_pipeline
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   
   # On macOS/Linux:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browser**
   ```bash
   playwright install chromium
   ```

5. **Install LaTeX for PDF generation (optional but recommended)**
   ```bash
   # macOS
   brew install --cask mactex
   
   # Ubuntu/Debian/Jetson Nano
   sudo apt-get install texlive-latex-base texlive-latex-extra
   
   # Verify installation
   python scripts/check_pdf_setup.py
   ```

6. **Set up configuration**
   ```bash
   cp .env.example .env
   ```

7. **Add your API keys to `.env`** (see [API Keys Setup](#-api-keys-setup))

---

## ⚙️ Configuration

This project uses **two configuration systems** for different parts of the application:

- **`src/config.py`** - Used by CLI, Flask app, and core pipeline (simple Config class)
- **`backend/app/config.py`** - Used by FastAPI backend (Pydantic Settings with type validation)

Both systems read from the same `.env` file. See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for detailed documentation on when to use each system and how they differ.

### Environment Variables (`.env`)

```env
# Required API Keys
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_CSE_ID=your_custom_search_engine_id_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional Settings
LOG_LEVEL=INFO
DATABASE_PATH=data/jobs.db
```

### User Profile (`src/config.py`)

Customize your job preferences in the `USER_PROFILE` dictionary:

```python
USER_PROFILE = {
    # Maximum years of experience you're targeting
    "max_yoe": 3,
    
    # Skills you have (used for matching)
    "required_skills": [
        "python", 
        "sql", 
        "machine learning",
        "pytorch",
        "tensorflow"
    ],
    
    # Nice-to-have skills (bonus points)
    "preferred_skills": [
        "aws", 
        "kubernetes", 
        "mlops",
        "llm",
        "langchain"
    ],
    
    # Preferred locations
    "preferred_locations": [
        "San Francisco", 
        "Remote", 
        "New York",
        "Seattle"
    ],
    
    # Set True to only see remote jobs
    "remote_only": False,
    
    # Job titles to exclude (too senior)
    "exclude_title_keywords": [
        "senior", 
        "staff", 
        "principal", 
        "director", 
        "lead", 
        "manager"
    ],
}
```

---

## 📖 Usage

### Basic Commands

```bash
# Run daily automated search (recommended)
python main.py --daily

# Search with custom keywords
python main.py --keywords "AI engineer" "ML engineer"

# Search specific sites
python main.py --keywords "data scientist" --sites greenhouse.io lever.co

# Get more results
python main.py --keywords "ML engineer" --num-results 100

# Search last week instead of last day
python main.py --keywords "AI engineer" --date-restrict w1

# View database statistics
python main.py --stats

# Show help
python main.py --help
```

### Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--keywords` | `-k` | Search keywords | Daily defaults |
| `--sites` | `-s` | Job sites to search | All supported sites |
| `--num-results` | `-n` | Max results to fetch | 50 |
| `--date-restrict` | `-d` | Date filter (d1/d3/w1/w2/m1) | d1 (last day) |
| `--min-score` | `-m` | Min relevance score | 30 |
| `--daily` | | Run daily search | |
| `--comprehensive` | `-c` | Matrix search: each keyword × each site | |
| `--per-site` | `-ps` | Search each site individually with N results | |
| `--no-pre-filter` | | Disable pre-filtering (send all to LLM) | |
| `--skill-stats` | | Show skill frequency statistics | |
| `--pre-filter-stats` | | Show pre-filter statistics | |
| `--usage-report` | `-u` | Show API usage and costs (last 7 days) | |
| `--stats` | | Show database stats | |
| `--quiet` | `-q` | Reduce output | |

### Python API Usage

```python
from src.pipeline import JobSearchPipeline

# Initialize pipeline
pipeline = JobSearchPipeline()

# Run custom search
results = pipeline.run(
    keywords=["ML engineer", "AI engineer"],
    sites=["greenhouse.io", "lever.co"],
    num_results=50,
    min_score=40
)

# Get statistics
stats = pipeline.get_stats()
print(f"Total jobs: {stats['total']}")

# Query saved jobs
jobs = pipeline.db.get_jobs(filters={
    "max_yoe": 2,
    "min_score": 50,
    "remote": True
})

# Clean up
pipeline.cleanup()
```

---

## 🚪 Entry Points

This project has multiple entry points for different use cases:

### 1. CLI (Primary) - `python main.py`
Main command-line interface for job searching and pipeline operations.

```bash
python main.py --daily                    # Run daily search
python main.py --keywords "AI engineer"    # Custom search
python main.py --stats                     # View statistics
```

**Location**: `/main.py`  
**Dependencies**: `requirements.txt` (root)

### 2. FastAPI Backend (Recommended for Web)
Modern async API backend with automatic OpenAPI documentation.

```bash
cd backend
uvicorn app.main:app --reload
# Access API at http://localhost:8000
# Docs at http://localhost:8000/docs
```

**Location**: `/backend/app/main.py`  
**Dependencies**: `backend/requirements.txt`

### 3. React Frontend
Modern web UI that connects to FastAPI backend.

```bash
cd frontend
npm install
npm start
# Access UI at http://localhost:3000
```

**Location**: `/frontend/`  
**Dependencies**: `frontend/package.json`

### 4. Flask Web App (Deprecated)
Simple Flask-based web interface. Kept for backward compatibility.

```bash
python web_app.py --host 0.0.0.0 --port 5000
```

**Location**: `/web_app.py`  
**Dependencies**: `requirements.txt` (includes Flask)  
**Status**: Deprecated - use FastAPI + React instead

See [docs/FRAMEWORK_DECISION.md](docs/FRAMEWORK_DECISION.md) for framework strategy details.

---

## 📄 Resume Generation

The pipeline includes AI-powered resume generation that tailors your resume to each job posting.

### Quick Start

```bash
# Generate resumes for top 10 jobs (interactive)
python scripts/generate_resumes.py

# Auto-select top 3 projects for each job
python scripts/generate_resumes.py --auto

# Generate for specific job ID
python scripts/generate_resumes.py --job-id 42

# Generate for top 5 jobs with min score 40
python scripts/generate_resumes.py --top 5 --min-score 40

# List all generated resumes
python scripts/generate_resumes.py --list-resumes
```

### Setup

1. **Create resume configuration** (`data/resume_config.yaml`):
   ```yaml
   contact:
     name: "Your Name"
     email: "your.email@example.com"
     phone: "xxx-xxx-xxxx"
     linkedin: "linkedin.com/in/yourprofile"
     github: "github.com/yourusername"
   
   default_location: "San Diego, CA"
   approved_locations:
     - "San Diego, CA"
     - "Remote"
   
   education:
     degree: "MS in Data Science"
     school: "University Name"
     gpa: "3.8"
     graduation: "2023"
     coursework: ["Machine Learning", "Deep Learning", "Statistics"]
   
   experience:
     - title: "ML Engineer"
       company: "Company Name"
       dates: "2022 - Present"
       bullets:
         - "Built ML pipelines..."
         - "Deployed models..."
   
   skills:
     languages: ["Python", "SQL", "R"]
     ml_frameworks: ["PyTorch", "TensorFlow", "Scikit-learn"]
     cloud_devops: ["AWS", "Docker", "Kubernetes"]
     ai_tools: ["LangChain", "HuggingFace", "OpenAI"]
     domains: ["NLP", "Computer Vision", "Recommendation Systems"]
   ```

2. **Create projects file** (`data/projects.json`):
   ```json
   {
     "projects": [
       {
         "id": "project1",
         "name": "RAG System",
         "one_liner": "Built a retrieval-augmented generation system",
         "skills": ["Python", "LangChain", "OpenAI", "Vector DB"],
         "metrics": "Improved accuracy by 30%",
         "bullets": [
           "Implemented semantic search with embeddings",
           "Built prompt engineering pipeline"
         ]
       }
     ]
   }
   ```

### Features

- **AI-Powered Project Matching**: Automatically ranks your projects by relevance to each job
- **Dynamic Skill Selection**: Automatically adds relevant skills from `extended_skills` based on job requirements
- **Location Matching**: Automatically adjusts resume location based on job location
- **Tailored Summaries**: Generates job-specific professional summaries
- **PDF Output**: Compiles LaTeX to professional PDF resumes
- **Batch Processing**: Generate multiple resumes at once
- **Change Tracking**: Tracks which skills and projects were added to each resume

### Integration with Main Pipeline

Resume generation is now integrated into the main pipeline flow. After running a job search, you'll see:

1. All new jobs displayed with YOE and key details
2. Prompt to generate resumes for new jobs
3. Automatic project selection and resume generation

---

## 🌐 Web Frontend

### FastAPI + React (Recommended)

The primary web interface uses FastAPI for the backend and React for the frontend:

```bash
# Start FastAPI backend
cd backend
uvicorn app.main:app --reload
# Backend runs on http://localhost:8000
# API docs available at http://localhost:8000/docs

# Start React frontend (in another terminal)
cd frontend
npm install
npm start
# Frontend runs on http://localhost:3000
```

**Features:**
- Modern async API with automatic OpenAPI documentation
- React-based UI with better UX
- Type-safe request/response handling
- Better performance with async operations

See [docs/WEB_APP.md](docs/WEB_APP.md) for detailed setup instructions.

### Flask Web App (Deprecated)

The Flask app is kept for backward compatibility but is deprecated:

A Flask-based web dashboard to view and manage your job search pipeline from any device on your network. Perfect for running on Jetson Nano and viewing on your PC.

### Starting the Web Server

```bash
# Run on all interfaces (accessible from network)
python web_app.py --host 0.0.0.0 --port 5000

# Run on specific port
python web_app.py --host 0.0.0.0 --port 8080

# Development mode (local only)
python web_app.py --host 127.0.0.1 --port 5000
```

**Note**: Flask app is deprecated. New development should use FastAPI + React instead. See [docs/FRAMEWORK_DECISION.md](docs/FRAMEWORK_DECISION.md) for details.

### Accessing from PC

1. **Find the server IP address:**
   ```bash
   # On the server (Jetson Nano)
   hostname -I
   ```

2. **Open in browser:**
   ```
   http://<server-ip>:5000
   ```
   Example: `http://192.168.1.100:5000`

### Features

- **Dashboard**: View statistics and overview
- **Job Browser**: Filter jobs by score, YOE, company, location, remote status
- **Unextracted Jobs**: Monitor failed extractions with retry counts
- **Resume Management**: View and download generated PDF resumes
- **Mark Applied**: Track which jobs you've applied to
- **Auto-refresh**: Updates every 30 seconds

### API Endpoints

The web app provides a REST API:

**Job Management:**
- `GET /api/stats` - Database statistics
- `GET /api/jobs` - Get jobs with filters
- `GET /api/jobs/<id>` - Get specific job
- `POST /api/jobs/<id>/mark-applied` - Mark job as applied
- `GET /api/unextracted` - Get unextracted jobs

**Resume Management:**
- `GET /api/resumes` - Get generated resumes
- `GET /api/resumes/<id>/pdf` - Download resume PDF

**Search & Analysis:**
- `POST /api/search/run` - Run a job search
- `GET /api/pre-filtered` - Get pre-filtered jobs (by reason)
- `GET /api/pre-filter-stats` - Pre-filter statistics
- `GET /api/skills` - Get skill frequency data (by category)
- `GET /api/skills/<skill_name>` - Get skill distribution across categories
- `GET /api/skill-stats` - Overall skill statistics

---

## 🎨 Customization

### Adding New Job Sites

Edit `src/config.py`:

```python
# Add to JS_HEAVY_SITES if the site requires JavaScript rendering
JS_HEAVY_SITES.add("newsite.com")

# Or add to JINA_FRIENDLY_SITES if it works with simple HTTP requests
JINA_FRIENDLY_SITES.add("newsite.com")

# Add to default search sites
DEFAULT_JOB_SITES.append("newsite.com")
```

### Modifying Relevance Scoring

Edit the `calculate_relevance_score` method in `src/filters.py`:

```python
def calculate_relevance_score(self, job: ParsedJob) -> int:
    score = 0
    
    # Customize scoring weights
    if job.yoe_required <= self.max_yoe:
        score += 30  # Adjust this weight
    
    # Add custom scoring logic
    if "FAANG" in job.company:
        score += 20  # Bonus for FAANG companies
    
    return max(0, min(100, score))
```

### Adding Custom Extraction Selectors

Edit `src/extractor.py`:

```python
JOB_SELECTORS = [
    # Add custom selectors at the top (higher priority)
    '.custom-job-description',
    '[data-custom="job-content"]',
    # ... existing selectors
]
```

### Extraction Methods

The pipeline uses three extraction methods with automatic fallback:

1. **Jina Reader** (Primary for most sites)
   - Fast, works for static HTML pages
   - Converts web pages to clean markdown

2. **Playwright** (For JavaScript-heavy sites)
   - Renders JavaScript content
   - Used for Greenhouse, Lever, Workday, etc.

3. **BeautifulSoup** (Final fallback)
   - Lightweight HTML parsing
   - Used when Jina and Playwright both fail

Failed extractions are automatically saved to the `unextracted_jobs` table for later retry.

---

## 🔑 API Keys Setup

### 1. Google Custom Search API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the **Custom Search JSON API**:
   - Go to APIs & Services → Library
   - Search for "Custom Search JSON API"
   - Click Enable
4. Create credentials:
   - Go to APIs & Services → Credentials
   - Click "Create Credentials" → "API Key"
   - Copy the API key to `.env` as `GOOGLE_API_KEY`
5. Create a Custom Search Engine:
   - Go to [Programmable Search Engine](https://programmablesearchengine.google.com/)
   - Click "Add" to create a new search engine
   - Set "Search the entire web" to ON
   - Copy the Search Engine ID to `.env` as `GOOGLE_CSE_ID`

**Free Tier**: 100 queries/day free, then $5 per 1,000 queries

### 2. OpenAI API

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Go to API Keys section
4. Create a new API key
5. Copy the key to `.env` as `OPENAI_API_KEY`

**Cost**: ~$0.50 per 1,000 job postings parsed (using GPT-4o-mini)

---

## 🌐 Supported Job Sites

The pipeline supports 30+ ATS (Applicant Tracking System) platforms:

### JavaScript-Rendered (Uses Playwright)
- Greenhouse.io
- Lever.co
- Ashby HQ
- Workday (myworkdayjobs.com)
- iCIMS
- SmartRecruiters
- Jobvite
- Oracle Cloud
- ADP Workforce Now
- Rippling ATS

### Static Sites (Uses Jina Reader)
- Workable
- Wellfound (AngelList)
- BuiltIn
- Teamtailor
- Work at a Startup
- Breezy HR
- Homerun
- Dover
- Notion Sites

### Also Supports
- Company career pages
- Custom job boards
- Any publicly accessible job posting

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        PIPELINE FLOW                             │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Google     │     │   Content    │     │    LLM       │
│   Search     │ ──▶ │   Extractor  │ ──▶ │    Parser    │
│   API        │     │              │     │  (GPT-4o)    │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │
       │                    │                    │
       ▼                    ▼                    ▼
  Job URLs            Raw HTML/Text        Structured JSON
  (10-100)           (per job page)        (ParsedJob)
                           │
                           ▼
               ┌──────────────────────┐
               │   Smart Router       │
               │                      │
               │  Jina? ──▶ Fast      │
               │  Playwright? ──▶ JS  │
               └──────────────────────┘
                           │
                           ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    Job       │     │   SQLite     │     │    CSV       │
│   Filter     │ ──▶ │   Database   │ ──▶ │   Export     │
│  (Scoring)   │     │              │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
       │
       ▼
  Relevance Score
     (0-100)
```

### Module Descriptions

| Module | Description |
|--------|-------------|
| `config.py` | Configuration, API keys, user profile |
| `search.py` | Google Custom Search API wrapper |
| `extractor.py` | Web content extraction (Jina + Playwright + BeautifulSoup) |
| `resume_generator.py` | AI-powered resume generation with PDF output |
| `web_app.py` | Flask web frontend (deprecated, use FastAPI instead) |
| `backend/app/main.py` | FastAPI backend application |
| `llm_parser.py` | GPT-4o-mini job parsing |
| `filters.py` | Relevance scoring and filtering |
| `storage.py` | SQLite database operations |
| `pipeline.py` | Main orchestrator |

---

## 🧪 Testing

The project includes comprehensive test coverage:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_extractor_extended.py

# Run with coverage
pytest --cov=src tests/

# Run specific test class
pytest tests/test_storage_extended.py::TestStorageExtended
```

### Test Coverage

- **Extractor Tests**: Jina, Playwright, and BeautifulSoup extraction methods
- **Storage Tests**: Database operations, unextracted jobs tracking
- **Pipeline Tests**: End-to-end pipeline integration
- **Parser Tests**: LLM job parsing accuracy
- **Filter Tests**: Relevance scoring logic

---

## 🔧 Troubleshooting

### Common Issues

**1. "Google API key is required" error**
```bash
# Make sure .env file exists and has the correct values
cat .env

# Check if variables are loaded
python -c "from src.config import config; print(config.api_key[:10])"
```

**2. "Playwright browser not found"**
```bash
# Install Playwright browsers
playwright install chromium
```

**3. "Rate limit exceeded" from Google**
- Free tier is 100 queries/day
- Wait 24 hours or upgrade to paid tier
- Reduce `--num-results`

**4. Empty extraction results**
- Some sites have anti-bot protection
- Try reducing batch size
- Check if the site is accessible in browser

**5. Low relevance scores**
- Adjust `USER_PROFILE` skills to match your resume
- Lower `--min-score` threshold
- Check `explain_score()` for debugging:
  ```python
  from src.filters import JobFilter
  from src.llm_parser import ParsedJob
  
  filter = JobFilter()
  breakdown = filter.explain_score(job)
  print(breakdown)
  ```

**6. PDF generation fails**
```bash
# Check if pdflatex is installed
python scripts/check_pdf_setup.py

# Install LaTeX if needed (see Installation section)
```

**7. Web frontend not accessible from PC**
- Ensure `--host 0.0.0.0` is used (not `127.0.0.1`)
- Check firewall settings on server
- Verify server IP address with `hostname -I`
- Check that port is not blocked

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py --daily
```

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| Search speed | ~1 sec per 10 URLs |
| Extraction (Jina) | ~1-2 sec per page |
| Extraction (Playwright) | ~3-5 sec per page |
| Extraction (BeautifulSoup) | ~0.5-1 sec per page |
| LLM parsing | ~0.5 sec per job |
| **Total for 50 jobs** | **~3-5 minutes** |

### Cost Breakdown (per 50 jobs)

| Service | Cost |
|---------|------|
| Google Search API | Free (100/day) |
| OpenAI GPT-4o-mini | ~$0.025 |
| **Total** | **~$0.03** |

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆕 Recent Features

### Pre-Parse Filtering (Cost Saving)
- Filters disqualifying jobs BEFORE expensive LLM calls using regex
- Checks: YOE > max_yoe, non-US locations, citizenship/clearance requirements
- Saves 20-40% on LLM costs
- View stats: `python main.py --pre-filter-stats`

### Skill Frequency Tracking
- Tracks which skills appear in which job categories
- Categories: Data Scientist, ML Engineer, AI Engineer, Applied Scientist, etc.
- View stats: `python main.py --skill-stats`
- Access via web API: `/api/skills`

### Smart Resume Skills
- Dynamically adds relevant skills from `extended_skills` based on job requirements
- Only adds skills you actually have (from your extended_skills list)
- Tracks which skills were added to each resume

### Usage Tracking
- Automatic tracking of Google Search API and OpenAI API usage
- Cost calculation and historical reports
- View: `python main.py --usage-report`

## 🤖 Daily Automation

The pipeline can be set up to run automatically every day. This is perfect for keeping your job search active without manual intervention.

### Quick Start

```bash
# Run once immediately
python scripts/daily_runner.py

# Run as daemon (scheduled daily at 9 AM)
python scripts/daily_runner.py --daemon

# Custom schedule time
python scripts/daily_runner.py --daemon --schedule "08:30"
```

### Setup Options

**Option 1: Cron (Linux/Mac) - Recommended**
```bash
chmod +x setup_cron.sh
./setup_cron.sh
```

**Option 2: Systemd Service (Linux)**
```bash
sudo ./setup_systemd.sh
```

**Option 3: Windows Task Scheduler**
```cmd
# Run as Administrator
setup_windows_task.bat
```

### Features

- **Automated Daily Runs**: Runs at scheduled time (default: 9 AM)
- **Resume Generation**: Automatically generates resumes for top matches
- **Web Dashboard**: Starts web server for viewing results
- **Logging**: All runs logged to `logs/daily_runner.log`

### Configuration

The `scripts/daily_runner.py` script supports many options:

```bash
python scripts/daily_runner.py --help
```

Key options:
- `--daemon` - Run as background daemon
- `--schedule HH:MM` - Set custom schedule time
- `--no-web` - Skip web server
- `--no-resume` - Skip resume generation
- `--top-jobs N` - Generate resumes for top N jobs

See [DAILY_AUTOMATION.md](DAILY_AUTOMATION.md) for complete documentation.

## 📚 Additional Documentation

- [ARCHITECTURE_FLOW.md](ARCHITECTURE_FLOW.md) - Complete architecture and flow documentation
- [DAILY_AUTOMATION.md](DAILY_AUTOMATION.md) - Daily automation setup guide

## 🙏 Acknowledgments

- [Jina AI](https://jina.ai/) for the Reader API
- [OpenAI](https://openai.com/) for GPT-4o-mini
- [Playwright](https://playwright.dev/) for browser automation
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing
- [Flask](https://flask.palletsprojects.com/) for web framework
- [Rich](https://rich.readthedocs.io/) for beautiful CLI output

---

## 📞 Support

- Create an [Issue](https://github.com/yourusername/job_search_pipeline/issues) for bug reports
- Start a [Discussion](https://github.com/yourusername/job_search_pipeline/discussions) for questions

---

**Happy Job Hunting! 🎯**
