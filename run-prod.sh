#!/bin/bash

# Energent AI Production Environment Launcher
# This script handles production deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_colored() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    echo ""
    print_colored "$BLUE" "🚀 $1"
}

print_success() {
    print_colored "$GREEN" "✅ $1"
}

print_warning() {
    print_colored "$YELLOW" "⚠️  $1"
}

print_error() {
    print_colored "$RED" "❌ $1"
}

# Check if .env file exists
check_env_file() {
    if [ ! -f .env ]; then
        print_error ".env file not found."
        print_colored "$NC" "Please create .env file with your ANTHROPIC_API_KEY."
        print_colored "$NC" "You can copy from env.example: cp env.example .env"
        exit 1
    fi
}

# Check API key (strict for production)
check_api_key() {
    if ! grep -q "ANTHROPIC_API_KEY=sk-" .env 2>/dev/null; then
        print_error "ANTHROPIC_API_KEY not set in .env file"
        print_colored "$NC" "Production requires a valid API key. Please edit .env and add your API key."
        exit 1
    fi
    print_success "API key found in .env file"
}

# Check Docker installation
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# Main execution
main() {
    print_header "Starting Energent AI (Production Mode)"
    
    # Prerequisites check
    check_docker
    check_env_file
    check_api_key
    
    # Create data directory if it doesn't exist
    mkdir -p data
    
    # Stop any running containers
    print_colored "$YELLOW" "🔄 Stopping any running containers..."
    docker compose down 2>/dev/null || true
    
    # Start production environment
    print_colored "$YELLOW" "🔄 Starting production containers..."
    docker compose up --build -d
    
    print_success "Production environment started!"
    echo ""
    print_colored "$BLUE" "🔗 Access URLs:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend API: http://localhost:8501"
    echo "  API Docs: http://localhost:8501/docs"
    echo "  VNC Viewer: http://localhost:8080"
    echo ""
    print_colored "$BLUE" "📋 Management Commands:"
    echo "  View logs: docker compose logs -f"
    echo "  Stop: docker compose down"
    echo "  Restart: docker compose restart"
}

# Run main function
main
