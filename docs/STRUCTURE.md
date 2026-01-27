# Project Structure

This document describes the intended folder structure and organization principles for the Job Search Pipeline project.

## Directory Structure

```
job_search_pipeline/
├── backend/                    # FastAPI backend application
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/         # API route handlers
│   │   │   └── deps.py         # Shared dependencies
│   │   ├── core/               # Core business logic
│   │   ├── models/             # SQLAlchemy database models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── services/           # Business logic services
│   │   ├── config.py           # Backend configuration (Pydantic)
│   │   ├── database.py         # Database connection and setup
│   │   └── main.py             # FastAPI application entry point
│   ├── Dockerfile              # Backend container definition
│   └── requirements.txt       # Backend Python dependencies
│
├── frontend/                   # React frontend application
│   ├── src/                    # React source code
│   ├── Dockerfile              # Frontend container definition
│   ├── nginx.conf              # Nginx configuration
│   └── package.json            # Node.js dependencies
│
├── src/                        # Core pipeline logic (shared)
│   ├── config.py               # CLI/Flask configuration
│   ├── pipeline.py             # Main pipeline orchestrator
│   ├── search.py               # Google Search API wrapper
│   ├── extractor.py            # Web content extraction
│   ├── llm_parser.py           # GPT job parsing
│   ├── storage.py              # SQLite database operations (sync)
│   ├── filters.py              # Relevance scoring
│   ├── pre_filters.py          # Pre-parse filtering
│   ├── resume_generator.py      # Resume generation
│   └── usage_tracker.py        # API usage tracking
│
├── scripts/                    # Utility scripts
│   ├── daily_runner.py         # Daily automation script
│   ├── generate_resumes.py     # Resume generation utility
│   ├── check_pdf_setup.py      # LaTeX/PDF setup verification
│   └── verify_setup.py          # Environment verification
│
├── tests/                      # All test files
│   ├── test_backend.py         # Backend API tests
│   ├── test_structure.py       # Structure validation tests
│   ├── test_quick.py           # Quick smoke tests
│   ├── test_extractor.py       # Extractor tests
│   ├── test_extractor_extended.py
│   ├── test_integration.py     # Integration tests
│   ├── test_parser.py           # LLM parser tests
│   ├── test_pipeline_extended.py
│   ├── test_search.py          # Search tests
│   ├── test_storage.py         # Storage tests
│   └── test_storage_extended.py
│
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md         # System architecture
│   ├── WEB_APP.md              # Web app documentation
│   ├── SETUP_WEB_APP.md        # Web app setup guide
│   ├── DAILY_AUTOMATION.md     # Automation guide
│   ├── AUTOMATION_INTEGRATION.md
│   ├── SEARCH_FEATURES.md      # Search features documentation
│   ├── SWAGGER_WORKFLOW.md     # API workflow documentation
│   ├── FRAMEWORK_DECISION.md   # Web framework strategy
│   ├── STRUCTURE.md            # This file
│   └── archive/                # Archived/debug files
│       ├── PROMPT_DEBUG_NO_JOBS.md
│       ├── COMPLETION_SUMMARY.md
│       ├── TEST_RESULTS.md
│       ├── EXECUTION_CHECK.md
│       ├── FEATURE_EXECUTION_VERIFICATION.md
│       └── FEATURES_IMPLEMENTATION_SUMMARY.md
│
├── templates/                  # Flask templates (deprecated)
│   └── index.html
│
├── data/                       # Database and data files (gitignored)
│   ├── jobs.db                 # SQLite database
│   ├── resume_config.yaml      # Resume configuration
│   └── projects.json           # Project data
│
├── logs/                       # Log files (gitignored)
│
├── main.py                     # CLI entry point (primary)
├── web_app.py                  # Flask app (deprecated)
├── requirements.txt            # Root requirements (CLI/core)
├── docker-compose.yml          # Docker orchestration
├── README.md                   # Main README
├── .gitignore                  # Git ignore rules
└── .env.example                # Environment variables template
```

## Organization Principles

### 1. Separation of Concerns

- **`src/`**: Core pipeline logic, shared between CLI and web apps
- **`backend/`**: FastAPI-specific code (async, modern)
- **`frontend/`**: React UI code
- **`scripts/`**: Utility scripts for automation and setup
- **`tests/`**: All test files in one location

### 2. Configuration Management

- **`src/config.py`**: Used by CLI and Flask (simple Config class)
- **`backend/app/config.py`**: Used by FastAPI (Pydantic Settings)
- Both read from `.env` file
- See [CONFIGURATION.md](CONFIGURATION.md) for detailed documentation

### 3. Database Strategy

- **SQLite (sync)**: `src/storage.py` - Used by CLI and Flask
- **SQLAlchemy (async)**: `backend/app/database.py` - Used by FastAPI
- The async pipeline can copy data from SQLite to async DB

### 4. Entry Points

1. **CLI**: `python main.py` - Primary entry point for job searching
2. **FastAPI**: `uvicorn backend.app.main:app` - Web API
3. **React**: `cd frontend && npm start` - Web UI
4. **Flask** (deprecated): `python web_app.py` - Simple web interface

### 5. Dependencies

- **`requirements.txt`**: Core dependencies for CLI/scripts
- **`backend/requirements.txt`**: FastAPI backend dependencies
- **`frontend/package.json`**: React frontend dependencies

## Import Paths

### CLI/Flask Code
```python
from src.config import config
from src.pipeline import JobSearchPipeline
from src.storage import JobDatabase
```

### FastAPI Backend Code
```python
from app.config import settings
from app.database import init_db
from app.models.job import Job
```

### Shared Core Logic
Both can import from `src/`:
```python
from src.search import GoogleJobSearch
from src.extractor import ContentExtractor
```

## Testing Structure

All tests are in `/tests/`:
- Unit tests for individual modules
- Integration tests for full pipeline
- Backend API tests
- Extended test suites for complex scenarios

## Documentation Structure

- **`README.md`**: Main documentation, quick start, features
- **`docs/ARCHITECTURE.md`**: System architecture and design
- **`docs/WEB_APP.md`**: Web application documentation
- **`docs/FRAMEWORK_DECISION.md`**: Framework strategy
- **`docs/STRUCTURE.md`**: This file - project organization
- **`docs/archive/`**: Old debug/temporary files

## Future Improvements

1. Consider consolidating config files if possible
2. Document why two pipeline implementations exist (sync vs async)
3. Standardize import paths across the codebase
4. Add type hints consistently
5. Create proper package structure if needed
