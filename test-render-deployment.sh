#!/bin/bash

# Test script for Render deployment
# This script helps test the Docker builds locally before deploying to Render

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

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Function to test MLflow server build
test_mlflow_build() {
    print_header "🧪 Testing MLflow Server Build"
    
    print_info "Building MLflow server image..."
    if docker build -t test-mlflow-server ./mlflow; then
        print_status "MLflow server image built successfully"
    else
        print_error "MLflow server build failed"
        return 1
    fi
    
    print_info "Testing MLflow server container..."
    # Start container in background
    docker run -d --name test-mlflow \
        -p 5001:5001 \
        -e MLFLOW_BACKEND_STORE_URI=sqlite:///mlflow/backend/mlflow.db \
        -e MLFLOW_DEFAULT_ARTIFACT_ROOT=/mlflow/artifacts \
        test-mlflow-server
    
    # Wait for container to start
    sleep 30
    
    # Test health endpoint
    if curl -f http://localhost:5001/health; then
        print_status "MLflow server health check passed"
    else
        print_error "MLflow server health check failed"
        docker logs test-mlflow
        docker stop test-mlflow
        docker rm test-mlflow
        return 1
    fi
    
    # Cleanup
    docker stop test-mlflow
    docker rm test-mlflow
    print_status "MLflow server test completed successfully"
}

# Function to test main API build
test_api_build() {
    print_header "🧪 Testing Main API Build"
    
    print_info "Building main API image..."
    if docker build -t test-iris-api .; then
        print_status "Main API image built successfully"
    else
        print_error "Main API build failed"
        return 1
    fi
    
    print_info "Testing main API container..."
    # Start container in background
    docker run -d --name test-iris-api \
        -p 8000:8000 \
        -e DEBUG=false \
        -e LOG_LEVEL=INFO \
        -e USE_MLFLOW_REGISTRY=false \
        test-iris-api
    
    # Wait for container to start
    sleep 20
    
    # Test health endpoint
    if curl -f http://localhost:8000/health; then
        print_status "Main API health check passed"
    else
        print_error "Main API health check failed"
        docker logs test-iris-api
        docker stop test-iris-api
        docker rm test-iris-api
        return 1
    fi
    
    # Test prediction endpoint
    print_info "Testing prediction endpoint..."
    if curl -f -X POST "http://localhost:8000/predict" \
       -H "Content-Type: application/json" \
       -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'; then
        print_status "Prediction endpoint test passed"
    else
        print_error "Prediction endpoint test failed"
        docker logs test-iris-api
        docker stop test-iris-api
        docker rm test-iris-api
        return 1
    fi
    
    # Cleanup
    docker stop test-iris-api
    docker rm test-iris-api
    print_status "Main API test completed successfully"
}

# Function to cleanup test images
cleanup() {
    print_info "Cleaning up test images..."
    docker rmi test-mlflow-server test-iris-api 2>/dev/null || true
    print_status "Cleanup completed"
}

# Main function
main() {
    print_header "🚀 Testing Render Deployment Locally"
    echo "======================================"
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        exit 1
    fi
    
    # Run tests
    if test_mlflow_build && test_api_build; then
        print_header "🎉 All tests passed!"
        print_info "Your deployment should work on Render."
        print_info "You can now push your changes to trigger deployment."
    else
        print_error "Some tests failed. Please fix the issues before deploying."
        exit 1
    fi
    
    # Cleanup
    cleanup
}

# Handle script interruption
trap cleanup EXIT

# Run main function
main "$@"