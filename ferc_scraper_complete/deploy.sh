#!/bin/bash

# FERC Scraper Deployment Script
# This script automates the deployment of the FERC scraper

set -e

echo "🚀 FERC Scraper Deployment Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if Docker is installed
check_docker() {
    print_status "Checking Docker installation..."
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

# Setup environment file
setup_environment() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            print_status "Created .env file from template."
            print_warning "Please edit .env file with your database credentials before continuing."
        else
            print_error ".env.example not found. Please create a .env file manually."
            exit 1
        fi
    else
        print_status ".env file already exists."
    fi
}

# Build and start services
deploy_services() {
    print_status "Building and starting services..."
    
    # Stop any existing services
    docker-compose down 2>/dev/null || true
    
    # Build images
    print_status "Building Docker images..."
    docker-compose build
    
    # Start services
    print_status "Starting services..."
    docker-compose up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 30
    
    # Check service status
    print_status "Checking service status..."
    docker-compose ps
}

# Run health checks
run_health_checks() {
    print_status "Running health checks..."
    
    # Check if PostgreSQL is ready
    if docker-compose exec -T postgres pg_isready -U ferc_user -d ferc_data >/dev/null 2>&1; then
        print_status "✅ PostgreSQL is ready"
    else
        print_warning "⚠️ PostgreSQL is not ready yet. This is normal during initial startup."
    fi
    
    # Check if scraper container is running
    if docker-compose ps ferc-scraper | grep -q "Up"; then
        print_status "✅ FERC scraper is running"
    else
        print_error "❌ FERC scraper is not running"
        docker-compose logs ferc-scraper
        exit 1
    fi
}

# Show access information
show_access_info() {
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo "====================================="
    echo ""
    echo "📊 Access Information:"
    echo "   • pgAdmin: http://localhost:8080"
    echo "     - Email: admin@ferc.local"
    echo "     - Password: admin"
    echo ""
    echo "   • PostgreSQL: localhost:5432"
    echo "     - Database: ferc_data"
    echo "     - User: ferc_user"
    echo "     - Password: (as configured in .env)"
    echo ""
    echo "📋 Useful Commands:"
    echo "   • View logs: docker-compose logs -f ferc-scraper"
    echo "   • Stop services: docker-compose down"
    echo "   • Restart scraper: docker-compose restart ferc-scraper"
    echo "   • Check status: docker-compose ps"
    echo ""
    echo "🔍 Monitoring:"
    echo "   • Scraper logs: docker-compose logs -f ferc-scraper"
    echo "   • Database logs: docker-compose logs -f postgres"
    echo "   • Resource usage: docker-compose stats"
    echo ""
}

# Main deployment function
main() {
    echo "Starting deployment process..."
    echo ""
    
    check_docker
    setup_environment
    deploy_services
    run_health_checks
    show_access_info
}

# Handle script arguments
case "${1:-}" in
    "check")
        check_docker
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
        echo "  check     - Check Docker installation"
        echo "  env       - Setup environment file"
        echo "  deploy    - Deploy services"
        echo "  health    - Run health checks"
        echo "  logs      - View scraper logs"
        echo "  stop      - Stop all services"
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