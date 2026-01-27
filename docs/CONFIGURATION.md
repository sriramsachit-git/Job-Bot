# Configuration Management

This document explains the dual configuration system used in this project and when to use each configuration module.

## Overview

The project uses **two separate configuration systems** for different parts of the application:

1. **`src/config.py`** - Used by CLI, Flask app, and core pipeline logic
2. **`backend/app/config.py`** - Used by FastAPI backend

Both systems read from the same `.env` file but serve different purposes and have different capabilities.

---

## Configuration Systems Comparison

### `src/config.py` (CLI/Core Pipeline)

**Purpose**: Configuration for command-line interface, Flask web app, and core pipeline operations.

**Technology**: Simple Python class with `os.getenv()` and `python-dotenv`

**Used By**:
- `main.py` (CLI entry point)
- `web_app.py` (Flask app)
- `src/pipeline.py` (Main pipeline orchestrator)
- `src/search.py` (Google Search API)
- `src/resume_generator.py` (Resume generation)
- All other `src/` modules

**Key Features**:
- Simple, lightweight configuration
- Class-based singleton pattern (`config = Config()`)
- Manual validation with `config.validate()`
- Includes business logic constants (site lists, user profile)

**Configuration Values**:

```python
# API Keys
api_key: str              # GOOGLE_API_KEY
cx_id: str                # GOOGLE_CSE_ID
openai_api_key: str       # OPENAI_API_KEY

# Paths
database_path: str        # DATABASE_PATH (default: "data/jobs.db")
log_level: str            # LOG_LEVEL (default: "INFO")

# Rate Limiting
request_delay: float      # Default: 1.0
max_retries: int          # Default: 3
```

**Additional Constants**:
- `JS_HEAVY_SITES` - Sites requiring Playwright
- `JINA_FRIENDLY_SITES` - Sites that work well with Jina Reader
- `DEFAULT_JOB_SITES` - Default job board sites
- `USER_PROFILE` - User preferences for job filtering

**Usage Example**:
```python
from src.config import config, USER_PROFILE, DEFAULT_JOB_SITES

# Validate configuration
config.validate()

# Access values
api_key = config.api_key
db_path = config.database_path

# Use constants
sites = DEFAULT_JOB_SITES
profile = USER_PROFILE
```

---

### `backend/app/config.py` (FastAPI Backend)

**Purpose**: Configuration for FastAPI backend, async database, and web API features.

**Technology**: Pydantic Settings (BaseSettings) with automatic validation

**Used By**:
- `backend/app/main.py` (FastAPI app)
- `backend/app/database.py` (Async database)
- `backend/app/services/*` (Backend services)
- `backend/app/api/routes/*` (API routes)

**Key Features**:
- Type-safe configuration with Pydantic
- Automatic validation and type coercion
- Path objects (not just strings)
- Web-specific settings (CORS, server config)
- Cloud storage configuration
- Automatic directory creation

**Configuration Values**:

```python
# API Keys (optional for testing)
google_api_key: str       # GOOGLE_API_KEY
google_cse_id: str        # GOOGLE_CSE_ID
openai_api_key: str       # OPENAI_API_KEY

# Database
database_url: str         # SQLALCHEMY_DATABASE_URL (default: "sqlite+aiosqlite:///./data/jobs.db")

# Paths (Path objects)
data_dir: Path            # Default: Path("./data")
resumes_dir: Path         # Default: Path("./data/resumes")

# Cloud Storage
cloud_storage_provider: str  # CLOUD_STORAGE_PROVIDER (default: "local")
aws_access_key_id: str       # AWS_ACCESS_KEY_ID
aws_secret_access_key: str    # AWS_SECRET_ACCESS_KEY
s3_bucket: str                # S3_BUCKET
s3_region: str                # S3_REGION (default: "us-east-1")

# CORS
cors_origins: List[str]    # CORS_ORIGINS (default: ["http://localhost:3000", "http://localhost:5173"])

# Server
host: str                 # HOST (default: "0.0.0.0")
port: int                 # PORT (default: 8000)
debug: bool               # DEBUG (default: False)
```

**Usage Example**:
```python
from app.config import settings

# Access values (type-safe, validated)
api_key = settings.google_api_key
db_url = settings.database_url

# Path objects work directly
resume_path = settings.resumes_dir / "resume.pdf"

# Automatic validation
# If invalid type provided, Pydantic raises ValidationError
```

---

## Environment Variable Mapping

Both config systems read from the same `.env` file. Here's how environment variables map to each system:

| Environment Variable | `src/config.py` | `backend/app/config.py` | Notes |
|---------------------|-----------------|------------------------|-------|
| `GOOGLE_API_KEY` | `config.api_key` | `settings.google_api_key` | Same value, different names |
| `GOOGLE_CSE_ID` | `config.cx_id` | `settings.google_cse_id` | Same value, different names |
| `OPENAI_API_KEY` | `config.openai_api_key` | `settings.openai_api_key` | Same value, same name |
| `DATABASE_PATH` | `config.database_path` | - | CLI uses file path string |
| `SQLALCHEMY_DATABASE_URL` | - | `settings.database_url` | Backend uses SQLAlchemy URL |
| `LOG_LEVEL` | `config.log_level` | - | CLI only |
| `HOST` | - | `settings.host` | Backend only |
| `PORT` | - | `settings.port` | Backend only |
| `DEBUG` | - | `settings.debug` | Backend only |
| `CORS_ORIGINS` | - | `settings.cors_origins` | Backend only |
| `CLOUD_STORAGE_PROVIDER` | - | `settings.cloud_storage_provider` | Backend only |
| `AWS_ACCESS_KEY_ID` | - | `settings.aws_access_key_id` | Backend only |
| `AWS_SECRET_ACCESS_KEY` | - | `settings.aws_secret_access_key` | Backend only |
| `S3_BUCKET` | - | `settings.s3_bucket` | Backend only |
| `S3_REGION` | - | `settings.s3_region` | Backend only |

---

## When to Use Which Config

### Use `src/config.py` When:

✅ Writing CLI scripts (`main.py`, scripts in `scripts/`)  
✅ Working with Flask app (`web_app.py`)  
✅ Developing core pipeline logic (`src/pipeline.py`, `src/search.py`, etc.)  
✅ Need business logic constants (`USER_PROFILE`, `DEFAULT_JOB_SITES`)  
✅ Simple configuration needs (no type validation required)  
✅ Working with synchronous code

### Use `backend/app/config.py` When:

✅ Writing FastAPI backend code  
✅ Working with async database operations  
✅ Need type-safe configuration with validation  
✅ Need web-specific settings (CORS, server config)  
✅ Working with cloud storage  
✅ Need Path objects instead of strings  
✅ Working with async code

---

## Key Differences

### 1. **Validation**

**`src/config.py`**:
```python
# Manual validation
config.validate()  # Raises ValueError if missing
```

**`backend/app/config.py`**:
```python
# Automatic validation on instantiation
settings = Settings()  # Raises ValidationError if invalid
```

### 2. **Type Safety**

**`src/config.py`**:
```python
# String values, no type coercion
api_key: str = os.getenv("GOOGLE_API_KEY", "")
# Returns empty string if not set
```

**`backend/app/config.py`**:
```python
# Pydantic handles type conversion
port: int = 8000
# Automatically converts string "8000" to int 8000
# Raises ValidationError if cannot convert
```

### 3. **Path Handling**

**`src/config.py`**:
```python
# String paths
database_path: str = "data/jobs.db"
# Must manually convert to Path if needed
```

**`backend/app/config.py`**:
```python
# Path objects
resumes_dir: Path = Path("./data/resumes")
# Can use directly: settings.resumes_dir / "file.pdf"
```

### 4. **Business Logic**

**`src/config.py`**:
- Includes `USER_PROFILE` (user preferences)
- Includes `DEFAULT_JOB_SITES` (site lists)
- Includes `JS_HEAVY_SITES`, `JINA_FRIENDLY_SITES`

**`backend/app/config.py`**:
- Focused on infrastructure/config only
- No business logic constants

---

## Shared Values

Both systems need the same API keys. Make sure your `.env` file includes:

```env
# Required for both systems
GOOGLE_API_KEY=your_key_here
GOOGLE_CSE_ID=your_cse_id_here
OPENAI_API_KEY=your_openai_key_here

# CLI/Flask specific
DATABASE_PATH=data/jobs.db
LOG_LEVEL=INFO

# Backend specific
SQLALCHEMY_DATABASE_URL=sqlite+aiosqlite:///./data/jobs.db
HOST=0.0.0.0
PORT=8000
DEBUG=False
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## Why Two Config Systems?

### Historical Reasons

1. **Different Development Phases**: 
   - `src/config.py` was created first for CLI/Flask
   - `backend/app/config.py` was added later for FastAPI

2. **Different Requirements**:
   - CLI needs simple config with business logic constants
   - Backend needs type-safe config with web/cloud features

3. **Different Technologies**:
   - CLI uses simple Python classes
   - Backend uses Pydantic (modern, type-safe)

### Current Rationale

**Separation is intentional and beneficial**:

✅ **Different Concerns**: CLI config includes business logic (USER_PROFILE), backend config is infrastructure-only  
✅ **Different Validation**: CLI uses simple validation, backend uses Pydantic's powerful validation  
✅ **Different Types**: CLI uses strings, backend uses Path objects and typed values  
✅ **Independence**: Each system can evolve independently

---

## Future Considerations

### Option 1: Keep Separate (Recommended)

**Pros**:
- Clear separation of concerns
- Each system optimized for its use case
- No breaking changes needed

**Cons**:
- Some duplication (API keys)
- Need to maintain two systems

### Option 2: Create Shared Base

Create a shared config module that both import from:

```python
# shared_config.py
class BaseConfig:
    google_api_key: str
    google_cse_id: str
    openai_api_key: str

# src/config.py
from shared_config import BaseConfig
class Config(BaseConfig):
    # CLI-specific additions

# backend/app/config.py
from shared_config import BaseConfig
class Settings(BaseSettings, BaseConfig):
    # Backend-specific additions
```

**Pros**:
- Single source of truth for shared values
- Reduces duplication

**Cons**:
- More complex architecture
- Requires refactoring
- May not be worth the effort

### Option 3: Migrate CLI to Pydantic

Convert `src/config.py` to use Pydantic Settings:

**Pros**:
- Consistent configuration approach
- Better type safety everywhere

**Cons**:
- Breaking change for CLI
- Adds Pydantic dependency to CLI
- May be overkill for simple CLI needs

---

## Best Practices

1. **Don't Mix Config Systems**
   ```python
   # ❌ Bad: Mixing configs
   from src.config import config
   from app.config import settings
   # Use one or the other, not both
   ```

2. **Use Appropriate Config for Context**
   ```python
   # ✅ Good: CLI code uses src/config
   from src.config import config
   
   # ✅ Good: Backend code uses app/config
   from app.config import settings
   ```

3. **Keep .env File Synchronized**
   - Both systems read from same `.env`
   - Ensure API keys are set for both
   - Document which variables are for which system

4. **Validate Early**
   ```python
   # CLI: Validate at startup
   config.validate()
   
   # Backend: Validation happens automatically
   # But you can add custom validation if needed
   ```

---

## Troubleshooting

### "Missing required configuration" Error

**CLI (`src/config.py`)**:
```python
# Check .env file has:
GOOGLE_API_KEY=...
GOOGLE_CSE_ID=...
OPENAI_API_KEY=...
```

**Backend (`backend/app/config.py`)**:
```python
# Pydantic will raise ValidationError
# Check that required fields are set in .env
# Or that defaults are acceptable
```

### Type Mismatch Errors

**Backend only** (Pydantic validates types):
```python
# If PORT="abc" in .env, Pydantic will raise ValidationError
# Fix: Set PORT=8000 (integer, not string)
```

**CLI** (no type validation):
```python
# CLI accepts strings, you must handle type conversion manually
```

### Path Issues

**CLI**:
```python
# Use string paths
db = JobDatabase(config.database_path)  # String
```

**Backend**:
```python
# Use Path objects
resume_path = settings.resumes_dir / "file.pdf"  # Path object
```

---

## Summary

- **Two config systems exist by design** - each optimized for its use case
- **`src/config.py`** - Simple, CLI/Flask focused, includes business logic
- **`backend/app/config.py`** - Type-safe, backend focused, infrastructure only
- **Both read from `.env`** - Keep API keys synchronized
- **Use the appropriate config** - Don't mix systems
- **Separation is intentional** - No immediate need to consolidate

For questions or issues, see the main [README.md](../README.md) or [STRUCTURE.md](STRUCTURE.md).
