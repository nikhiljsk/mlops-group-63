#!/bin/bash

# MLOps Demo Runner Script
# This script demonstrates the complete MLOps pipeline

set -e

echo "🚀 Starting MLOps Iris Classification Demo"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required commands exist
check_requirements() {
    print_status "Checking requirements..."
    
    commands=("python3" "docker" "docker-compose")
    for cmd in "${commands[@]}"; do
        if ! command -v $cmd &> /dev/null; then
            print_error "$cmd is not installed"
            exit 1
        fi
    done
    
    print_success "All requirements satisfied"
}

# Setup Python environment
setup_environment() {
    print_status "Setting up Python environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    fi
    
    source venv/bin/activate
    pip install -r requirements.txt
    print_success "Dependencies installed"
}

# Train models
train_models() {
    print_status "Training ML models..."
    
    source venv/bin/activate
    python src/train.py
    
    if [ -f "artifacts/best_model.pkl" ]; then
        print_success "Models trained successfully"
    else
        print_error "Model training failed"
        exit 1
    fi
}

# MLflow server removed - using local training only

# Start Prometheus
start_prometheus() {
    print_status "Starting Prometheus monitoring..."
    
    docker-compose up -d prometheus
    
    # Wait for Prometheus to start
    sleep 10
    
    if curl -s http://localhost:9090 > /dev/null; then
        print_success "Prometheus started at http://localhost:9090"
    else
        print_warning "Prometheus may not be ready yet"
    fi
}

# Start API server
start_api() {
    print_status "Starting FastAPI server..."
    
    source venv/bin/activate
    uvicorn api.main:app --host 0.0.0.0 --port 8000 &
    API_PID=$!
    
    # Wait for API to start
    sleep 10
    
    if curl -s http://localhost:8000/health > /dev/null; then
        print_success "API server started at http://localhost:8000"
    else
        print_error "API server failed to start"
        exit 1
    fi
}

# Start web frontend
start_frontend() {
    print_status "Starting web frontend..."
    
    # Simple Python HTTP server for the frontend (use port 3001 to avoid Grafana conflict)
    cd frontend
    python3 -m http.server 3001 &
    FRONTEND_PID=$!
    cd ..
    
    sleep 3
    print_success "Frontend started at http://localhost:3001"
}

# Run tests
run_tests() {
    print_status "Running pipeline tests..."
    
    source venv/bin/activate
    python test_pipeline.py
    
    print_success "Pipeline tests completed"
}

# Make sample predictions
demo_predictions() {
    print_status "Making sample predictions..."
    
    # Test single prediction
    curl -X POST "http://localhost:8000/predict" \
         -H "Content-Type: application/json" \
         -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}' \
         | python3 -m json.tool
    
    echo ""
    
    # Test batch prediction
    curl -X POST "http://localhost:8000/predict/batch" \
         -H "Content-Type: application/json" \
         -d '{
           "samples": [
             {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2},
             {"sepal_length": 6.2, "sepal_width": 2.9, "petal_length": 4.3, "petal_width": 1.3},
             {"sepal_length": 6.5, "sepal_width": 3.0, "petal_length": 5.2, "petal_width": 2.0}
           ]
         }' \
         | python3 -m json.tool
    
    print_success "Sample predictions completed"
}

# Show metrics
show_metrics() {
    print_status "Fetching current metrics..."
    
    echo "=== API Health ==="
    curl -s http://localhost:8000/health | python3 -m json.tool
    
    echo ""
    echo "=== Model Info ==="
    curl -s http://localhost:8000/model/info | python3 -m json.tool
    
    echo ""
    echo "=== Prometheus Metrics (sample) ==="
    curl -s http://localhost:8000/metrics | head -20
    
    print_success "Metrics displayed"
}

# Cleanup function
cleanup() {
    print_status "Cleaning up processes..."
    
    # Kill background processes
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Stop Docker containers
    docker-compose down 2>/dev/null || true
    
    print_success "Cleanup completed"
}

# Trap cleanup on script exit
trap cleanup EXIT

# Main execution
main() {
    case "${1:-full}" in
        "setup")
            check_requirements
            setup_environment
            ;;
        "train")
            setup_environment
            train_models
            ;;
        "start")
            start_mlflow
            start_prometheus
            start_api
            start_frontend
            ;;
        "test")
            run_tests
            demo_predictions
            show_metrics
            ;;
        "full")
            check_requirements
            setup_environment
            train_models
            start_prometheus
            start_api
            start_frontend
            
            print_success "🎉 MLOps Pipeline is now running!"
            echo ""
            echo "📊 Access Points:"
            echo "  • Web Demo:    http://localhost:3001"
            echo "  • API Docs:    http://localhost:8000/docs"
            echo "  • Prometheus:  http://localhost:9090"
            echo "  • Grafana:     http://localhost:3000"
            echo ""
            echo "🧪 Run tests with: ./run_demo.sh test"
            echo "🛑 Press Ctrl+C to stop all services"
            
            # Keep script running
            while true; do
                sleep 30
                if ! curl -s http://localhost:8000/health > /dev/null; then
                    print_error "API server is down!"
                    break
                fi
            done
            ;;
        "stop")
            cleanup
            ;;
        *)
            echo "Usage: $0 {setup|train|start|test|full|stop}"
            echo ""
            echo "Commands:"
            echo "  setup  - Install dependencies and setup environment"
            echo "  train  - Train ML models"
            echo "  start  - Start all services"
            echo "  test   - Run tests and demo predictions"
            echo "  full   - Complete demo (default)"
            echo "  stop   - Stop all services"
            exit 1
            ;;
    esac
}

main "$@"