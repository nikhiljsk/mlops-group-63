#!/bin/bash

# Simple script to run the MLOps pipeline locally

echo "🚀 Starting MLOps Pipeline for Iris Classification"

# Step 1: Train models
echo "📊 Training models..."
python src/train.py

# Step 2: Start Prometheus
echo "📈 Starting Prometheus monitoring..."
docker-compose up -d prometheus
echo "Prometheus UI available at: http://localhost:9090"

# Step 3: Start API
echo "🌐 Starting API server..."
echo "API will be available at: http://localhost:8000"
echo "API docs at: http://localhost:8000/docs"
echo "Health check: http://localhost:8000/health"
echo "Metrics endpoint: http://localhost:8000/metrics"
echo "Prometheus UI: http://localhost:9090"
echo ""
echo "Press Ctrl+C to stop the server"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    docker-compose down
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload