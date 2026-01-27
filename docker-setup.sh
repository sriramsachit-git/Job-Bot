#!/bin/bash
# Docker setup script for job search pipeline

set -e

echo "🐳 Setting up Docker environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install docker-compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "⚠️  Please edit .env and add your API keys!"
    else
        cat > .env << EOF
# API Keys (required)
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_CSE_ID=your_cse_id_here
OPENAI_API_KEY=your_openai_key_here

# Database
DATABASE_PATH=data/jobs.db
SQLALCHEMY_DATABASE_URL=sqlite+aiosqlite:///./data/jobs.db

# Backend
HOST=0.0.0.0
PORT=8000
DEBUG=false
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Cloud Storage (optional)
CLOUD_STORAGE_PROVIDER=local
EOF
        echo "⚠️  Created .env file. Please edit it and add your API keys!"
    fi
fi

# Create data directories
echo "Creating data directories..."
mkdir -p data resumes backend/data backend/resumes

echo ""
echo "✅ Docker setup complete!"
echo ""
echo "To start the services:"
echo "  docker-compose up -d"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop services:"
echo "  docker-compose down"
echo ""
echo "To rebuild:"
echo "  docker-compose build --no-cache"
echo ""
echo "⚠️  Don't forget to add your API keys to .env file!"
