#!/bin/bash

# Simple script to run the MLOps pipeline locally

echo "🚀 Starting MLOps Pipeline for Iris Classification"

# Step 1: Train models
echo "📊 Training models..."
python src/train.py

# Step 2: Start API
echo "🌐 Starting API server..."
echo "API will be available at: http://localhost:8000"
echo "API docs at: http://localhost:8000/docs"
echo "Health check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"

uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload