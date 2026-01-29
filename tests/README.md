# Test Suite Documentation

This directory contains comprehensive tests for the Job Search Pipeline application, including E2E browser tests, API integration tests, and frontend-backend connectivity tests.

## Test Structure

```
tests/
├── e2e/                    # End-to-end browser tests (Playwright)
│   ├── dashboard.spec.ts   # Dashboard page tests
│   ├── search-flow.spec.ts # Search workflow tests
│   ├── api-connectivity.spec.ts # API connectivity tests
│   └── fixtures.ts         # Test fixtures
├── integration/            # Backend API integration tests
│   ├── test_backend_api.py      # Backend API endpoint tests
│   └── test_frontend_backend.py # Frontend-backend integration tests
└── README.md               # This file
```

## Test Types

### 1. E2E Tests (Playwright)

Browser-based tests that test the complete user flow:
- **Dashboard Tests**: Load dashboard, display stats, navigate to search
- **Search Flow Tests**: Complete search workflow from UI to backend
- **API Connectivity Tests**: Verify frontend can communicate with backend

**Run E2E tests:**
```bash
# Install Playwright browsers (first time only)
cd frontend
npm install
npx playwright install --with-deps

# Run tests
npm run test:e2e

# Run with UI
npm run test:e2e:ui

# Debug mode
npm run test:e2e:debug
```

### 2. Integration Tests (Pytest)

Backend API tests that verify endpoints work correctly:
- **Backend API Tests**: Test all API endpoints, error handling, validation
- **Frontend-Backend Tests**: Test API response formats match frontend expectations

**Run integration tests:**
```bash
cd backend
source venv/bin/activate
pip install pytest pytest-asyncio httpx
pytest ../tests/integration/ -v
```

### 3. Comprehensive Test Runner

Run all tests with a single command:

```bash
# Run all tests
./run_tests.sh

# Run only E2E tests
./run_tests.sh --e2e-only

# Run only integration tests
./run_tests.sh --integration-only

# Install dependencies first
./run_tests.sh --install-deps
```

## Prerequisites

### Backend
- Python 3.10+
- Virtual environment with dependencies installed
- Test database will be created automatically at `backend/data/test_api.db`

### Frontend
- Node.js 18+
- Playwright browsers installed (`npx playwright install`)

## Test Configuration

### Playwright Configuration
- Config file: `playwright.config.ts`
- Tests run against `http://localhost:3000` (frontend)
- Backend expected at `http://localhost:8000`
- Automatically starts servers if not running

### Pytest Configuration
- Config file: `pytest.ini`
- Uses async test mode
- Test database: `sqlite+aiosqlite:///./data/test_api.db`

## What Tests Cover

### Dashboard Page
- ✅ Loads dashboard and displays stats
- ✅ Navigates to new search page
- ✅ Displays jobs table
- ✅ Handles API errors gracefully
- ✅ Filters jobs by status

### Search Flow
- ✅ Completes new search workflow
- ✅ Displays search progress
- ✅ Handles search errors

### API Connectivity
- ✅ Backend health check
- ✅ Dashboard stats endpoint
- ✅ Jobs list endpoint
- ✅ CORS configuration
- ✅ Filtering and pagination
- ✅ Error handling

### Backend API
- ✅ Health endpoint
- ✅ Dashboard endpoints
- ✅ Jobs CRUD operations
- ✅ Search endpoints
- ✅ Error handling and validation
- ✅ Pagination

### Frontend-Backend Integration
- ✅ API response format validation
- ✅ CORS headers
- ✅ Error response format
- ✅ Complete search flow
- ✅ Job CRUD flow

## Debugging Tests

### Playwright Debug Mode
```bash
cd frontend
npx playwright test --debug
```

### View Test Results
```bash
# HTML report
npx playwright show-report

# Screenshots and videos saved to test-results/
```

### Backend Test Debugging
```bash
cd backend
source venv/bin/activate
pytest ../tests/integration/ -v -s  # -s shows print statements
pytest ../tests/integration/test_backend_api.py::TestJobsAPI::test_get_jobs -v
```

## Common Issues

### Backend not running
- Tests will automatically start backend if not running
- Or manually: `cd backend && uvicorn app.main:app --reload`

### Frontend not running
- Tests will automatically start frontend if not running
- Or manually: `cd frontend && npm run dev`

### Database errors
- Test database is created automatically
- Delete `backend/data/test_api.db` to reset

### Playwright browsers not installed
```bash
cd frontend
npx playwright install --with-deps
```

## Continuous Integration

Tests are designed to run in CI environments:
- Set `CI=true` environment variable
- Tests will retry failed tests
- Servers are started automatically
- Test databases are isolated

## Adding New Tests

### Adding E2E Test
1. Create new file in `tests/e2e/`
2. Import from `@playwright/test`
3. Use `test.describe()` and `test()` functions
4. Run with `npm run test:e2e`

### Adding Integration Test
1. Create new file in `tests/integration/`
2. Use pytest async fixtures
3. Import from `app.main` and test endpoints
4. Run with `pytest tests/integration/`

## Test Coverage Goals

- ✅ Dashboard page: 100% of user flows
- ✅ Search flow: 100% of steps
- ✅ API endpoints: 100% coverage
- ✅ Error handling: All error paths tested
- ✅ Frontend-backend: All API calls verified
