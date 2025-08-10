#!/bin/bash

# Test script to build each service individually

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Test MLflow build
test_mlflow_build() {
    print_header "🧪 Testing MLflow Server Build (Isolated)"
    
    print_info "Building MLflow server from mlflow directory..."
    cd mlflow
    
    if docker build -t test-mlflow-isolated .; then
        print_status "MLflow server built successfully"
        cd ..
        return 0
    else
        print_error "MLflow server build failed"
        cd ..
        return 1
    fi
}

# Test main API build
test_api_build() {
    print_header "🧪 Testing Main API Build"
    
    print_info "Building main API from root directory..."
    
    if docker build -t test-api-isolated .; then
        print_status "Main API built successfully"
        return 0
    else
        print_error "Main API build failed"
        return 1
    fi
}

# Test both services
test_both_services() {
    print_header "🧪 Testing Both Services Together"
    
    print_info "Starting MLflow server..."
    docker run -d --name test-mlflow-service -p 5001:5001 test-mlflow-isolated
    
    print_info "Starting API server..."
    docker run -d --name test-api-service -p 8000:8000 \
        -e MLFLOW_TRACKING_URI=http://localhost:5001 \
        test-api-isolated
    
    # Wait for services to start
    sleep 30
    
    # Test MLflow health
    if curl -f http://localhost:5001/health; then
        print_status "MLflow health check passed"
    else
        print_error "MLflow health check failed"
        docker logs test-mlflow-service
    fi
    
    # Test API health
    if curl -f http://localhost:8000/health; then
        print_status "API health check passed"
    else
        print_error "API health check failed"
        docker logs test-api-service
    fi
    
    # Cleanup
    docker stop test-mlflow-service test-api-service
    docker rm test-mlflow-service test-api-service
}

# Cleanup function
cleanup() {
    print_info "Cleaning up test images and containers..."
    docker stop test-mlflow-service test-api-service 2>/dev/null || true
    docker rm test-mlflow-service test-api-service 2>/dev/null || true
    docker rmi test-mlflow-isolated test-api-isolated 2>/dev/null || true
    print_status "Cleanup completed"
}

# Main function
main() {
    print_header "🚀 Testing Individual Service Builds"
    echo "====================================="
    
    # Test builds individually
    if test_mlflow_build && test_api_build; then
        print_status "Both services built successfully!"
        
        # Test them running together
        test_both_services
        
        print_header "🎉 All tests passed!"
    else
        print_error "Some builds failed"
        exit 1
    fi
    
    cleanup
}

# Handle script interruption
trap cleanup EXIT

# Run main function
main "$@"