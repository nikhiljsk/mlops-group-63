#!/bin/bash

# Simple test script for MLflow build

echo "🧪 Testing MLflow build..."

# Build the MLflow image
echo "Building MLflow image..."
if docker build -t test-mlflow-simple ./mlflow --no-cache; then
    echo "✅ MLflow build successful!"
    
    # Test running the container
    echo "Testing container startup..."
    docker run -d --name test-mlflow-container -p 5001:5001 test-mlflow-simple
    
    # Wait a bit for startup
    sleep 20
    
    # Test health endpoint
    echo "Testing health endpoint..."
    if curl -f http://localhost:5001/health; then
        echo "✅ Health check passed!"
    else
        echo "❌ Health check failed"
        docker logs test-mlflow-container
    fi
    
    # Cleanup
    docker stop test-mlflow-container
    docker rm test-mlflow-container
    docker rmi test-mlflow-simple
    
else
    echo "❌ MLflow build failed!"
    exit 1
fi