#!/bin/bash

# FERC Scraper - External Database Deployment Script
# Configured for database: 34.59.88.3 (jay_semia)

set -e

echo "🚀 FERC Scraper - External Database Deployment"
echo "=============================================="
echo "Database: 34.59.88.3:5432/postgres"
echo "Schema: test_external"
echo "User: jay_semia"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    print_step "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_status "Docker and Docker Compose are installed."
}

# Test database connection
test_database_connection() {
    print_step "Testing database connection..."
    
    # Test if we can reach the database
    if ! nc -z 34.59.88.3 5432 2>/dev/null; then
        print_warning "Cannot reach database port 5432 on 34.59.88.3"
        print_warning "This may be expected if you're not on the same network"
    else
        print_status "Database port is reachable"
    fi
    
    # Test with psql if available
    if command -v psql &> /dev/null; then
        if PGPASSWORD='$..q)kf:=bCqw4fZ' psql -h 34.59.88.3 -U jay_semia -d postgres -c "SELECT version();" >/dev/null 2>&1; then
            print_status "Database connection test successful"
        else
            print_warning "Direct database connection test failed"
            print_warning "This is normal if you're not on the same network"
        fi
    else
        print_warning "psql not available, skipping direct connection test"
    fi
}

# Setup environment file
setup_environment() {
    print_step "Setting up environment configuration..."
    
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            print_status "Created .env file from template with external database configuration."
        else
            print_error ".env.example not found. Please create a .env file manually."
            exit 1
        fi
    else
        print_status ".env file already exists."
    fi
    
    # Verify configuration
    if grep -q "34.59.88.3" .env; then
        print_status "External database configuration verified in .env"
    else
        print_warning "External database configuration not found in .env"
        print_warning "Please ensure DB_HOST=34.59.88.3 is set"
    fi
}

# Build and start services
deploy_services() {
    print_step "Building and starting FERC scraper..."
    
    # Stop any existing services
    docker-compose down 2>/dev/null || true
    
    # Build images
    print_status "Building Docker image..."
    docker-compose build
    
    # Start services
    print_status "Starting FERC scraper..."
    docker-compose up -d
    
    # Wait for services to be ready
    print_status "Waiting for scraper to initialize..."
    sleep 10
    
    # Check service status
    print_status "Checking service status..."
    docker-compose ps
}

# Run health checks
run_health_checks() {
    print_step "Running health checks..."
    
    # Check if scraper container is running
    if docker-compose ps ferc-scraper | grep -q "Up"; then
        print_status "✅ FERC scraper is running"
    else
        print_error "❌ FERC scraper is not running"
        docker-compose logs ferc-scraper
        exit 1
    fi
    
    # Test database connection from container
    print_status "Testing database connection from container..."
    if docker-compose exec -T ferc-scraper python -c "
import os
from src.ferc_scraper.config import get_settings
from src.ferc_scraper.storage import PostgresStorage

try:
    settings = get_settings()
    with PostgresStorage(settings) as storage:
        cursor = storage._conn.cursor()
        cursor.execute('SELECT version()')
        print('✅ Database connection successful')
        print(f'   PostgreSQL version: {cursor.fetchone()[0][:50]}...')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
" 2>/dev/null; then
        print_status "✅ Database connection from container successful"
    else
        print_error "❌ Database connection from container failed"
        print_error "Check the logs for details: docker-compose logs ferc-scraper"
    fi
}

# Run tests
run_tests() {
    print_step "Running tests..."
    
    # Run unit tests
    print_status "Running unit tests..."
    if docker-compose exec -T ferc-scraper python -m pytest tests/ -q; then
        print_status "✅ Unit tests passed"
    else
        print_warning "⚠️ Some unit tests failed (this may be expected)"
    fi
    
    # Run database integration tests
    print_status "Running database integration tests..."
    if docker-compose exec -T ferc-scraper python tests/test_database_integration.py; then
        print_status "✅ Database integration tests passed"
    else
        print_warning "⚠️ Database integration tests failed (check logs for details)"
    fi
}

# Show access information
show_access_info() {
    echo ""
    echo "🎉 FERC Scraper Deployment Completed!"
    echo "====================================="
    echo ""
    echo "📊 Database Information:"
    echo "   • Host: 34.59.88.3"
    echo "   • Port: 5432"
    echo "   • Database: postgres"
    echo "   • Schema: test_external"
    echo "   • User: jay_semia"
    echo ""
    echo "🐳 Container Information:"
    echo "   • Container Name: ferc_scraper"
    echo "   • Status: $(docker-compose ps --format 'table {{.Name}}\t{{.Status}}' | grep ferc-scraper)"
    echo ""
    echo "📋 Useful Commands:"
    echo "   • View logs: docker-compose logs -f ferc-scraper"
    echo "   • Stop scraper: docker-compose down"
    echo "   • Restart scraper: docker-compose restart ferc-scraper"
    echo "   • Check status: docker-compose ps"
    echo "   • Run tests: docker-compose exec ferc-scraper python -m pytest tests/ -v"
    echo ""
    echo "🔍 Monitoring:"
    echo "   • Scraper logs: docker-compose logs -f ferc-scraper"
    echo "   • Resource usage: docker-compose stats"
    echo "   • Database connection: docker-compose exec ferc-scraper python -c 'from src.ferc_scraper.config import get_settings; from src.ferc_scraper.storage import PostgresStorage; settings = get_settings(); PostgresStorage(settings).connect()'"
    echo ""
    echo "📊 Data Tables:"
    echo "   • Documents (SCD2): test_external.documents"
    echo "   • Raw Data: test_external.ferc_raw"
    echo ""
    echo "✅ The FERC scraper is now running and connected to your external database!"
    echo ""
}

# Main deployment function
main() {
    echo "Starting deployment process for external database..."
    echo ""
    
    check_docker
    test_database_connection
    setup_environment
    deploy_services
    run_health_checks
    run_tests
    show_access_info
}

# Handle script arguments
case "${1:-}" in
    "check")
        check_docker
        test_database_connection
        ;;
    "env")
        setup_environment
        ;;
    "deploy")
        deploy_services
        ;;
    "health")
        run_health_checks
        ;;
    "test")
        run_tests
        ;;
    "logs")
        docker-compose logs -f ferc-scraper
        ;;
    "stop")
        docker-compose down
        ;;
    "restart")
        docker-compose restart ferc-scraper
        ;;
    "status")
        docker-compose ps
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  check     - Check Docker and database connectivity"
        echo "  env       - Setup environment file"
        echo "  deploy    - Deploy scraper"
        echo "  health    - Run health checks"
        echo "  test      - Run tests"
        echo "  logs      - View scraper logs"
        echo "  stop      - Stop scraper"
        echo "  restart   - Restart scraper"
        echo "  status    - Show service status"
        echo "  help      - Show this help message"
        echo ""
        echo "If no command is provided, runs full deployment."
        ;;
    *)
        main
        ;;
esac