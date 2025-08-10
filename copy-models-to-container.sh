#!/bin/bash

# Script to copy real model files to a running container
# Usage: ./copy-models-to-container.sh <container-name>

CONTAINER_NAME=${1:-iris-api-prod}

echo "📦 Copying model artifacts to container: $CONTAINER_NAME"

# Check if container exists and is running
if ! docker ps | grep -q $CONTAINER_NAME; then
    echo "❌ Container $CONTAINER_NAME is not running"
    exit 1
fi

# Copy artifacts
echo "📁 Copying artifacts..."
docker cp ./artifacts/. $CONTAINER_NAME:/app/artifacts/

# Copy data
echo "📁 Copying data..."
docker cp ./data/. $CONTAINER_NAME:/app/data/

# Restart the container to pick up new models
echo "🔄 Restarting container to load new models..."
docker restart $CONTAINER_NAME

echo "✅ Model files copied successfully!"
echo "🔍 You can verify by checking: docker exec $CONTAINER_NAME ls -la /app/artifacts/"