#!/bin/bash

# Energent AI Development Environment Launcher
# This script handles all development setup and startup

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

# Check if .env file exists and create if needed
check_and_create_env() {
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from template..."
        if [ -f env.example ]; then
            cp env.example .env
            print_success ".env file created from template"
            print_warning "Please edit .env and add your ANTHROPIC_API_KEY before proceeding."
            echo ""
            read -p "Would you like to continue without API key for now? (y/N): " -n 1 -r
            echo ""
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_colored "$NC" "Please edit .env file and run this script again."
                exit 1
            fi
        else
            print_error "env.example file not found. Cannot create .env file."
            exit 1
        fi
    fi
}

# Check API key
check_api_key() {
    if ! grep -q "ANTHROPIC_API_KEY=sk-" .env 2>/dev/null; then
        print_warning "ANTHROPIC_API_KEY not properly set in .env file"
        print_colored "$NC" "Please edit .env and add your API key for full functionality."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
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
    print_header "Starting Energent AI (Development Mode)"
    
    # Prerequisites check
    check_docker
    check_and_create_env
    check_api_key
    
    # Create data directory if it doesn't exist
    mkdir -p data
    
    # Stop any running containers
    print_colored "$YELLOW" "🔄 Stopping any running containers..."
    docker compose down 2>/dev/null || true
    
    # Start development environment
    print_colored "$YELLOW" "🔄 Starting development containers..."
    docker compose -f docker-compose.dev.yml up --build
    
    print_success "Development environment started!"
    echo ""
    print_colored "$BLUE" "🔗 Access URLs:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend API: http://localhost:8501"
    echo "  API Docs: http://localhost:8501/docs"
    echo "  VNC Viewer: http://localhost:8080"
}

# Run main function
main
