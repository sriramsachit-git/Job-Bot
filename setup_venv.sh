#!/bin/bash
# Setup script for fresh virtual environment

set -e

echo "🔧 Setting up fresh virtual environment..."

# Remove old venv if exists
if [ -d ".venv" ]; then
    echo "Removing old .venv..."
    rm -rf .venv
fi

if [ -d "venv" ]; then
    echo "Removing old venv..."
    rm -rf venv
fi

# Create new venv
echo "Creating new virtual environment..."
python3 -m venv .venv

# Activate venv
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip, setuptools, wheel..."
pip install --upgrade pip setuptools wheel

# Install root requirements
echo "Installing root requirements..."
pip install -r requirements.txt

# Install backend requirements
echo "Installing backend requirements..."
pip install -r backend/requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium

echo ""
echo "✅ Virtual environment setup complete!"
echo ""
echo "To activate the venv, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To verify installation:"
echo "  python -c 'from src.config import config; print(\"Config OK\")'"
echo "  python -c 'from app.config import settings; print(\"Backend config OK\")'"
