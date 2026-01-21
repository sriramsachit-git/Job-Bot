#!/bin/bash
# ============================================================
# Linux/Mac Cron Setup for Daily Job Search Pipeline
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH=$(which python3 || which python)
DAILY_RUNNER="$SCRIPT_DIR/daily_runner.py"
LOG_FILE="$SCRIPT_DIR/logs/daily_runner.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo ""
echo "========================================"
echo "Daily Job Search Pipeline - Cron Setup"
echo "========================================"
echo ""

# Check if Python is available
if [ -z "$PYTHON_PATH" ]; then
    echo -e "${RED}ERROR: Python is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python found: $PYTHON_PATH${NC}"
echo -e "${GREEN}✓ Script path: $DAILY_RUNNER${NC}"
echo ""

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Generate cron entry
CRON_ENTRY="0 9 * * * cd $SCRIPT_DIR && $PYTHON_PATH $DAILY_RUNNER --run-once >> $LOG_FILE 2>&1"

echo -e "${CYAN}Generated cron entry:${NC}"
echo ""
echo -e "${YELLOW}$CRON_ENTRY${NC}"
echo ""

# Ask user if they want to install the cron job
read -p "Do you want to install this cron job? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "daily_runner.py"; then
        echo -e "${YELLOW}Existing job search cron job found. Removing...${NC}"
        crontab -l 2>/dev/null | grep -v "daily_runner.py" | crontab -
    fi
    
    # Add new cron job
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    
    echo ""
    echo -e "${GREEN}========================================"
    echo "SUCCESS! Cron job installed."
    echo "========================================"
    echo -e "${NC}"
    echo "Schedule: Daily at 9:00 AM"
    echo "Log file: $LOG_FILE"
    echo ""
    echo "To verify installation:"
    echo "  crontab -l"
    echo ""
    echo "To remove the cron job:"
    echo "  crontab -l | grep -v 'daily_runner.py' | crontab -"
    echo ""
else
    echo ""
    echo "Cron job not installed. To install manually:"
    echo ""
    echo "1. Run: crontab -e"
    echo "2. Add this line:"
    echo "   $CRON_ENTRY"
    echo ""
fi

# Option to run now
echo ""
read -p "Do you want to run the pipeline now? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${CYAN}Starting pipeline...${NC}"
    echo ""
    cd "$SCRIPT_DIR"
    $PYTHON_PATH "$DAILY_RUNNER"
fi
