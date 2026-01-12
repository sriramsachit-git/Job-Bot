# 🔍 Job Search Pipeline

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Automated job search, extraction, and filtering pipeline for AI/ML engineering positions.**

This pipeline automates the tedious process of searching job boards, extracting job details, and filtering relevant positions based on your profile. It supports 30+ ATS platforms including Greenhouse, Lever, Workday, and more.

---

## 🎯 Features

- **🔍 Smart Search** - Google Custom Search API with Boolean query support
- **📄 Multi-Source Extraction** - Handles JS-rendered sites (Greenhouse, Lever) and static pages
- **🤖 AI-Powered Parsing** - GPT-4o-mini extracts structured job data with high accuracy
- **🎯 Relevance Scoring** - Scores jobs based on YOE, skills, location, and preferences
- **💾 Persistent Storage** - SQLite database with deduplication
- **📊 CSV Export** - Export results for spreadsheet analysis
- **⚡ Rate Limiting** - Built-in retry logic and respectful rate limiting

---

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Customization](#-customization)
- [API Keys Setup](#-api-keys-setup)
- [Supported Job Sites](#-supported-job-sites)
- [Architecture](#-architecture)
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

5. **Set up configuration**
   ```bash
   cp .env.example .env
   ```

6. **Add your API keys to `.env`** (see [API Keys Setup](#-api-keys-setup))

---

## ⚙️ Configuration

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
| `extractor.py` | Web content extraction (Jina + Playwright) |
| `llm_parser.py` | GPT-4o-mini job parsing |
| `filters.py` | Relevance scoring and filtering |
| `storage.py` | SQLite database operations |
| `pipeline.py` | Main orchestrator |

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

## 🙏 Acknowledgments

- [Jina AI](https://jina.ai/) for the Reader API
- [OpenAI](https://openai.com/) for GPT-4o-mini
- [Playwright](https://playwright.dev/) for browser automation
- [Rich](https://rich.readthedocs.io/) for beautiful CLI output

---

## 📞 Support

- Create an [Issue](https://github.com/yourusername/job_search_pipeline/issues) for bug reports
- Start a [Discussion](https://github.com/yourusername/job_search_pipeline/discussions) for questions

---

**Happy Job Hunting! 🎯**
