#!/bin/bash
# ============================================================
# Systemd Service Setup for Daily Job Search Pipeline
# Run this script with sudo
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="$SCRIPT_DIR/job-search.service"
TARGET_SERVICE="/etc/systemd/system/job-search.service"
LOG_DIR="/var/log/job_search"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo "========================================"
echo "Job Search Pipeline - Systemd Setup"
echo "========================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}ERROR: This script must be run as root (sudo)${NC}"
    exit 1
fi

# Get the current user (not root)
REAL_USER=${SUDO_USER:-$(whoami)}
REAL_HOME=$(eval echo ~$REAL_USER)

echo -e "${CYAN}Configuration:${NC}"
echo "  User: $REAL_USER"
echo "  Home: $REAL_HOME"
echo "  Script Dir: $SCRIPT_DIR"
echo ""

# Create log directory
echo "Creating log directory..."
mkdir -p "$LOG_DIR"
chown "$REAL_USER:$REAL_USER" "$LOG_DIR"
echo -e "${GREEN}✓ Log directory created: $LOG_DIR${NC}"

# Find Python path
PYTHON_PATH=$(which python3 || which python)

# Update service file with correct paths
echo "Updating service file..."
sed -e "s|User=pi|User=$REAL_USER|g" \
    -e "s|Group=pi|Group=$REAL_USER|g" \
    -e "s|WorkingDirectory=.*|WorkingDirectory=$SCRIPT_DIR|g" \
    -e "s|/home/pi/job_search_pipeline|$SCRIPT_DIR|g" \
    -e "s|/home/pi/.local/bin|$REAL_HOME/.local/bin|g" \
    -e "s|/usr/bin/python3|$PYTHON_PATH|g" \
    "$SERVICE_FILE" > "$TARGET_SERVICE"

echo -e "${GREEN}✓ Service file installed: $TARGET_SERVICE${NC}"

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload
echo -e "${GREEN}✓ Systemd reloaded${NC}"

# Enable the service
echo "Enabling service..."
systemctl enable job-search
echo -e "${GREEN}✓ Service enabled${NC}"

echo ""
echo -e "${GREEN}========================================"
echo "SUCCESS! Systemd service installed."
echo "========================================"
echo -e "${NC}"
echo ""
echo "Commands:"
echo "  Start:    sudo systemctl start job-search"
echo "  Stop:     sudo systemctl stop job-search"
echo "  Status:   sudo systemctl status job-search"
echo "  Logs:     sudo journalctl -u job-search -f"
echo "  Disable:  sudo systemctl disable job-search"
echo ""

# Ask to start the service
read -p "Do you want to start the service now? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting service..."
    systemctl start job-search
    sleep 2
    systemctl status job-search --no-pager
fi
