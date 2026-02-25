#!/bin/bash
# Quick start script for Docker setup

set -e

echo "🚀 Starting AI Translation Pipeline with Docker..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker Desktop or Docker daemon."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Error: docker-compose is not installed."
    echo "   Install it from: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if Ollama is running
echo "🔍 Checking Ollama connection..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is running"
else
    echo "⚠️  Warning: Ollama is not running on localhost:11434"
    echo "   Please start Ollama: ollama serve"
    echo "   And pull the model: ollama pull mistral:7b"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads outputs

# Build and start containers
echo "🔨 Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "✅ Services started!"
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🌐 Access the application:"
echo "   - Web UI: http://localhost:8501"
echo "   - API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "📝 View logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose down"
echo ""

