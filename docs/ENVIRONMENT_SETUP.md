# Environment Setup Guide

This guide explains how to set up a fresh virtual environment or Docker environment for the job search pipeline.

## ✅ Fresh Virtual Environment Created

A new virtual environment has been created at `.venv/` with all dependencies installed.

### What Was Done

1. ✅ Removed old corrupted `.venv` directory
2. ✅ Created fresh Python 3.13.11 virtual environment
3. ✅ Upgraded pip, setuptools, and wheel
4. ✅ Installed all root requirements (`requirements.txt`)
5. ✅ Installed all backend requirements (`backend/requirements.txt`)
6. ⚠️ Playwright browsers need network access to install (see below)

### Current Status

- **Python Version**: 3.13.11
- **Virtual Environment**: `.venv/`
- **Root Dependencies**: ✅ Installed
- **Backend Dependencies**: ✅ Installed
- **Playwright Browsers**: ⚠️ Need network access

---

## 🚀 Quick Start

### Activate Virtual Environment

```bash
source .venv/bin/activate
```

### Verify Installation

```bash
# Test CLI config
python -c "from src.config import config; print('✅ CLI config OK')"

# Test backend config (from backend directory)
cd backend
python -c "from app.config import settings; print('✅ Backend config OK')"
cd ..
```

### Install Playwright Browsers

**Note**: This requires network access. If you're in a sandboxed environment, you'll need to run this manually:

```bash
source .venv/bin/activate
playwright install chromium
```

---

## 🐳 Docker Setup (Alternative)

If you prefer Docker, use the provided setup script:

```bash
./docker-setup.sh
```

This will:
1. Check Docker installation
2. Create `.env` file if needed
3. Create necessary directories
4. Set up docker-compose

### Start Docker Services

```bash
docker-compose up -d
```

### View Logs

```bash
docker-compose logs -f
```

### Stop Services

```bash
docker-compose down
```

---

## 📝 Setup Scripts

Two setup scripts have been created:

### 1. `setup_venv.sh` - Virtual Environment Setup

Automates the entire venv setup process:

```bash
chmod +x setup_venv.sh
./setup_venv.sh
```

This script:
- Removes old venv
- Creates new venv
- Installs all dependencies
- Installs Playwright browsers

### 2. `docker-setup.sh` - Docker Setup

Sets up Docker environment:

```bash
chmod +x docker-setup.sh
./docker-setup.sh
```

---

## ⚠️ Known Issues & Solutions

### Issue 1: NumPy Version Conflict

**Problem**: Backend requirements specified `numpy==1.26.4` which doesn't build on Python 3.13.

**Solution**: ✅ Fixed - Updated to `numpy>=2.0.0` which is compatible with Python 3.13.

### Issue 2: Playwright Browser Installation

**Problem**: Playwright browsers require network access to download.

**Solution**: 
- Run `playwright install chromium` manually when you have network access
- Or use Docker which includes browsers in the image

### Issue 3: Backend Config Import

**Problem**: Importing `app.config` requires being in the backend directory or adding it to path.

**Solution**: 
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from app.config import settings
```

---

## 🔧 Manual Setup (If Scripts Don't Work)

### Step 1: Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2: Upgrade pip

```bash
pip install --upgrade pip setuptools wheel
```

### Step 3: Install Dependencies

```bash
# Root dependencies
pip install -r requirements.txt

# Backend dependencies
pip install -r backend/requirements.txt
```

### Step 4: Install Playwright Browsers

```bash
playwright install chromium
```

---

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] Virtual environment activates: `source .venv/bin/activate`
- [ ] Python version: `python --version` (should show 3.13.11)
- [ ] CLI config imports: `python -c "from src.config import config; print('OK')"`
- [ ] Backend config imports: `cd backend && python -c "from app.config import settings; print('OK')"`
- [ ] Playwright installed: `playwright --version`
- [ ] Playwright browsers: `playwright install chromium` (if network available)
- [ ] Run tests: `pytest tests/ -v` (some may fail without Playwright browsers)

---

## 🐳 Docker Alternative

If virtual environment setup is problematic, Docker provides an isolated environment:

### Prerequisites

- Docker installed
- docker-compose installed

### Setup

```bash
./docker-setup.sh
```

### Start Services

```bash
docker-compose up -d
```

### Access Services

- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000

---

## 📦 What's Installed

### Root Requirements (`requirements.txt`)
- Core: requests, pandas, numpy, python-dotenv, rich, click, PyYAML
- Web scraping: beautifulsoup4, playwright, lxml
- AI/ML: openai
- Google API: google-api-python-client, google-auth
- Async: aiohttp, httpx
- Testing: pytest, pytest-asyncio
- Utilities: tenacity, tqdm
- Flask: Flask, Jinja2, Werkzeug

### Backend Requirements (`backend/requirements.txt`)
- FastAPI: fastapi, uvicorn, starlette
- Database: sqlalchemy, aiosqlite, alembic
- Validation: pydantic, pydantic-settings, email-validator
- Cloud Storage: boto3, google-cloud-storage
- Web scraping: beautifulsoup4, playwright, lxml
- Data: numpy, pandas

---

## 🆘 Troubleshooting

### "ModuleNotFoundError: No module named 'app'"

**Solution**: Make sure you're in the backend directory or add it to Python path:
```python
import sys
sys.path.insert(0, 'backend')
```

### "Playwright browser not found"

**Solution**: Install browsers:
```bash
playwright install chromium
```

### "NumPy build failed"

**Solution**: Already fixed - use numpy>=2.0.0 for Python 3.13

### "Docker compose not found"

**Solution**: Install docker-compose or use `docker compose` (newer Docker versions)

---

## 📚 Next Steps

1. **Configure API Keys**: Edit `.env` file with your API keys
2. **Run Tests**: `pytest tests/ -v`
3. **Start CLI**: `python main.py --help`
4. **Start Backend**: `cd backend && uvicorn app.main:app --reload`
5. **Start Frontend**: `cd frontend && npm install && npm start`

---

## 📖 Related Documentation

- [CONFIGURATION.md](CONFIGURATION.md) - Configuration management
- [STRUCTURE.md](STRUCTURE.md) - Project structure
- [FRAMEWORK_DECISION.md](FRAMEWORK_DECISION.md) - Web framework strategy
- [README.md](../README.md) - Main documentation
