# Debugging Guide

This repo now has:
- **E2E browser tests** (Playwright) in `tests/e2e/`
- **Backend/API integration tests** (pytest) in `tests/integration/`

Use this guide when something fails.

## Quick “is frontend talking to backend?” checks

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/dashboard/stats
curl "http://localhost:8000/api/jobs?limit=5"
```

If these work but the UI doesn’t, check the browser DevTools **Network** tab and confirm requests go to `/api/...` (Vite proxy).

## Run tests

### Backend integration tests
```bash
cd backend
source venv/bin/activate
pytest ../tests/integration/ -v
```

### Browser E2E tests
```bash
cd frontend
npm run test:e2e
```

### One-command runner
```bash
./run_tests.sh
```

## Fix applied (backend bug)

### Async SQLAlchemy delete
`DELETE /api/jobs/{id}` and `DELETE /api/resumes/{id}` were updated to use an explicit SQLAlchemy `delete(...)` statement to avoid async-session delete issues.

## Likely next bug to investigate (if searches act “weird”)

### Background task using request-scoped DB session
In `backend/app/services/search_service.py`, `asyncio.create_task(...)` starts the pipeline in the background and passes the request’s `db` session into it.

If the request finishes quickly, that session may be closed while the background task still runs.

Symptom patterns:
- search starts, then status never updates / fails intermittently
- errors about closed session/connection

Fix direction:
- have the background pipeline create **its own** `AsyncSessionLocal()` session(s), instead of reusing the request-scoped one.

## Where to look when debugging

### Backend logs
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --log-level debug
```

### Frontend logs
In browser DevTools:
- **Console** tab
- **Network** tab (failed `/api/*` requests)

### DB inspection
```bash
sqlite3 backend/data/jobs.db
.tables
SELECT id,title,company,relevance_score FROM jobs ORDER BY id DESC LIMIT 10;
```

# Debugging Guide

This guide helps debug issues found during testing and code review.

## Bugs Fixed

### 1. SQLAlchemy Async Delete Bug ✅ FIXED

**Location**: `backend/app/api/routes/jobs.py` and `backend/app/api/routes/resumes.py`

**Issue**: Using `await db.delete(job)` which is not a valid method in SQLAlchemy 2.0 async.

**Fix**: Changed to use explicit delete statement:
```python
from sqlalchemy import delete
await db.execute(delete(Job).where(Job.id == job_id))
await db.commit()
```

**Impact**: Delete operations were failing silently or causing errors.

### 2. Database Session in Background Task ⚠️ POTENTIAL ISSUE

**Location**: `backend/app/services/search_service.py:57`

**Issue**: Database session `db` is passed to `asyncio.create_task()` which runs in background. The session might be closed before the task completes.

**Recommendation**: The `run_search` method should create its own database session instead of using the passed one. Check `backend/app/core/pipeline.py` to ensure it handles database sessions correctly.

**Status**: Needs verification - check if `AsyncSearchPipeline.run_search()` creates its own session.

## Common Issues and Solutions

### Backend Issues

#### Database Connection Errors
```python
# Error: "Database is locked" or connection errors
# Solution: Ensure using NullPool and proper async session handling
```

#### CORS Errors
```python
# Error: CORS policy blocking requests
# Solution: Check cors_origins in app/config.py includes frontend URL
```

#### Async/Await Issues
```python
# Error: "coroutine was never awaited"
# Solution: Ensure all async functions use await, check pytest.ini has asyncio_mode = auto
```

### Frontend Issues

#### API Connection Errors
```bash
# Error: "Network Error" or "Failed to fetch"
# Solution: 
# 1. Check backend is running on port 8000
# 2. Check vite.config.ts proxy configuration
# 3. Check CORS settings in backend
```

#### React Query Errors
```typescript
# Error: "Query failed" or infinite loading
# Solution:
# 1. Check API endpoint URLs match backend routes
# 2. Check response format matches TypeScript types
# 3. Check error handling in components
```

### Test Issues

#### Playwright Tests Failing
```bash
# Error: "Browser not found" or "Connection refused"
# Solution:
cd frontend
npx playwright install --with-deps
```

#### Pytest Async Errors
```bash
# Error: "RuntimeWarning: coroutine was never awaited"
# Solution: Ensure pytest.ini has asyncio_mode = auto
```

## Debugging Steps

### 1. Check Backend Logs
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --log-level debug
```

### 2. Check Frontend Console
- Open browser DevTools (F12)
- Check Console tab for errors
- Check Network tab for failed API calls

### 3. Test API Endpoints Directly
```bash
# Health check
curl http://localhost:8000/health

# Dashboard stats
curl http://localhost:8000/api/dashboard/stats

# Jobs list
curl http://localhost:8000/api/jobs?limit=10
```

### 4. Run Tests in Debug Mode
```bash
# E2E tests
cd frontend
npx playwright test --debug

# Integration tests
cd backend
pytest ../tests/integration/ -v -s
```

### 5. Check Database
```bash
# View test database
sqlite3 backend/data/test_api.db
.tables
SELECT * FROM jobs LIMIT 5;
```

## Testing Checklist

Before running tests, ensure:

- [ ] Backend dependencies installed (`pip install -r requirements.txt`)
- [ ] Frontend dependencies installed (`npm install`)
- [ ] Playwright browsers installed (`npx playwright install`)
- [ ] Backend server can start (`uvicorn app.main:app`)
- [ ] Frontend server can start (`npm run dev`)
- [ ] Database directory exists (`backend/data/`)
- [ ] Environment variables set (if needed for actual API calls)

## Known Limitations

1. **Search Pipeline**: Actual job searches require API keys (Google, OpenAI). Tests mock these or skip if keys not available.

2. **Resume Generation**: Requires LaTeX installation for PDF generation. Tests may skip if not available.

3. **WebSocket Tests**: WebSocket tests require both servers running. May need manual setup.

## Reporting Issues

When reporting bugs, include:

1. **Error Message**: Full error traceback
2. **Steps to Reproduce**: Exact commands or actions
3. **Environment**: Python version, Node version, OS
4. **Logs**: Backend logs and browser console logs
5. **Test Output**: Output from `./run_tests.sh`

## Quick Fixes

### Reset Test Database
```bash
rm backend/data/test_api.db
```

### Clear Frontend Cache
```bash
cd frontend
rm -rf node_modules/.vite
npm run dev
```

### Reinstall Playwright
```bash
cd frontend
npx playwright install --force
```
