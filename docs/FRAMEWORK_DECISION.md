# Web Framework Strategy

## Current State

This project currently has **two web frameworks**:

1. **Flask** (`web_app.py`) - Simple synchronous web app for viewing jobs/resumes
2. **FastAPI** (`backend/app/main.py`) - Modern async API with React frontend

## Decision: FastAPI as Primary Framework

**FastAPI is the primary and recommended web framework** for this project.

### Rationale

1. **Modern & Async**: FastAPI supports async/await, which is better for I/O-bound operations like database queries and API calls
2. **Better for Production**: Built-in OpenAPI/Swagger docs, automatic validation, better performance
3. **Type Safety**: Uses Pydantic for request/response validation
4. **Frontend Integration**: The React frontend (`frontend/`) is designed to work with the FastAPI backend
5. **Future-Proof**: Better suited for scaling and modern development practices

### Flask Status: **Deprecated but Kept for Compatibility**

The Flask app (`web_app.py`) is **deprecated** but kept for:
- Backward compatibility
- Simple deployments that don't need the full React frontend
- Quick local testing without frontend build

**Recommendation**: New development should use FastAPI. Flask app will be maintained minimally.

## Entry Points

### Primary Entry Points

1. **CLI**: `python main.py` - Main command-line interface for job searching
2. **FastAPI Backend**: `python -m backend.app.main` or `uvicorn backend.app.main:app` - Web API
3. **React Frontend**: `cd frontend && npm start` - Modern web UI

### Deprecated Entry Points

- **Flask Web App**: `python web_app.py` - Simple web interface (deprecated, use FastAPI + React instead)

## Migration Path

If you're currently using `web_app.py`:

1. **Start FastAPI backend**:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Start React frontend**:
   ```bash
   cd frontend
   npm install
   npm start
   ```

3. **Access**: http://localhost:3000 (or port configured in frontend)

The FastAPI backend provides all the same functionality as Flask, plus:
- Better API documentation (Swagger UI at `/docs`)
- Type-safe request/response handling
- Async operations for better performance
- Modern React frontend

## Configuration

- **CLI/Flask**: Uses `src/config.py` (simple Config class)
- **FastAPI**: Uses `backend/app/config.py` (Pydantic Settings)

Both read from `.env` file, but FastAPI uses Pydantic for better validation.
