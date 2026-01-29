#!/bin/bash

# Comprehensive Test Runner
# Runs all tests: E2E, Integration, and Unit tests

set -e

echo "🧪 Running Comprehensive Test Suite"
echo "=================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend is running
check_backend() {
    echo -e "${YELLOW}Checking backend server...${NC}"
    if curl -s http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✓ Backend is running${NC}"
        return 0
    else
        echo -e "${RED}✗ Backend is not running${NC}"
        echo "Starting backend server..."
        cd backend
        python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
        BACKEND_PID=$!
        cd ..
        sleep 5
        return 1
    fi
}

# Check if frontend is running
check_frontend() {
    echo -e "${YELLOW}Checking frontend server...${NC}"
    if curl -s http://localhost:3000 > /dev/null; then
        echo -e "${GREEN}✓ Frontend is running${NC}"
        return 0
    else
        echo -e "${RED}✗ Frontend is not running${NC}"
        echo "Starting frontend server..."
        cd frontend
        npm run dev &
        FRONTEND_PID=$!
        cd ..
        sleep 5
        return 1
    fi
}

# Cleanup function
cleanup() {
    if [ ! -z "$BACKEND_PID" ]; then
        echo "Stopping backend server..."
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        echo "Stopping frontend server..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi
}

trap cleanup EXIT

# Parse arguments
RUN_E2E=true
RUN_INTEGRATION=true
RUN_UNIT=true
INSTALL_DEPS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --e2e-only)
            RUN_INTEGRATION=false
            RUN_UNIT=false
            ;;
        --integration-only)
            RUN_E2E=false
            RUN_UNIT=false
            ;;
        --unit-only)
            RUN_E2E=false
            RUN_INTEGRATION=false
            ;;
        --install-deps)
            INSTALL_DEPS=true
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
    shift
done

# Install dependencies if requested
if [ "$INSTALL_DEPS" = true ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    
    # Backend
    if [ -d "backend" ]; then
        cd backend
        if [ ! -d "venv" ]; then
            python -m venv venv
        fi
        source venv/bin/activate
        pip install -r requirements.txt
        pip install pytest pytest-asyncio httpx
        cd ..
    fi
    
    # Frontend
    if [ -d "frontend" ]; then
        cd frontend
        npm install
        npx playwright install --with-deps
        cd ..
    fi
fi

# Run Backend Integration Tests
if [ "$RUN_INTEGRATION" = true ]; then
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Running Backend Integration Tests${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    cd backend
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Set test database
    export DATABASE_URL="sqlite+aiosqlite:///./data/test_api.db"
    
    pytest ../tests/integration/ -v --tb=short
    BACKEND_TEST_EXIT=$?
    cd ..
    
    if [ $BACKEND_TEST_EXIT -ne 0 ]; then
        echo -e "${RED}✗ Backend integration tests failed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Backend integration tests passed${NC}"
fi

# Run E2E Tests (requires both servers running)
if [ "$RUN_E2E" = true ]; then
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Running E2E Tests${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Check/start servers
    check_backend || true
    check_frontend || true
    
    # Wait for servers to be ready
    echo "Waiting for servers to be ready..."
    sleep 3
    
    # Run Playwright tests
    cd frontend
    npx playwright test
    E2E_TEST_EXIT=$?
    cd ..
    
    if [ $E2E_TEST_EXIT -ne 0 ]; then
        echo -e "${RED}✗ E2E tests failed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ E2E tests passed${NC}"
fi

# Run Unit Tests
if [ "$RUN_UNIT" = true ]; then
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Running Unit Tests${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Backend unit tests
    if [ -d "tests" ] && [ -f "tests/test_*.py" ]; then
        cd backend
        if [ -d "venv" ]; then
            source venv/bin/activate
        fi
        pytest ../tests/test_*.py -v --tb=short || true
        cd ..
    fi
    
    # Frontend unit tests
    if [ -d "frontend" ]; then
        cd frontend
        npm test -- --run || true
        cd ..
    fi
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}All tests completed!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
