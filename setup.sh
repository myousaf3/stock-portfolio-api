#!/bin/bash

# Portfolio API Setup Script
# This script helps initialize the project

set -e

echo "🚀 Portfolio API Setup"
echo "======================"
echo ""

# Check if .env.example exists
if [ ! -f .env.example ]; then
    echo "❌ .env.example not found!"
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    
    # Generate secure secret key
    if command -v openssl &> /dev/null; then
        SECRET_KEY=$(openssl rand -hex 32)
        # Update .env with generated key
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/your-secret-key-change-this-in-production/$SECRET_KEY/" .env
        else
            sed -i "s/your-secret-key-change-this-in-production/$SECRET_KEY/" .env
        fi
        echo "✅ Generated secure SECRET_KEY"
    else
        echo "⚠️  Could not generate SECRET_KEY (openssl not found)"
        echo "   Please update SECRET_KEY in .env manually"
    fi
else
    echo "✅ .env file already exists"
    
    # Validate .env
    if grep -q "your-secret-key-change-this-in-production" .env; then
        echo "⚠️  WARNING: Using default SECRET_KEY. Generate a secure one!"
        echo "   Run: openssl rand -hex 32"
    fi
fi

echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose found"
echo ""

# Build containers
echo "🏗️  Building Docker containers..."
docker compose build

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "  docker compose up"
echo ""
echo "Or use make commands:"
echo "  make up        - Start services"
echo "  make logs      - View logs"
echo "  make test      - Run tests"
echo ""
echo "API will be available at: http://localhost:8000"
echo "Documentation: http://localhost:8000/docs"
echo ""
echo "Demo credentials:"
echo "  Email: demo@example.com"
echo "  Password: demo123"
