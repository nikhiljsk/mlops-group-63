#!/bin/bash

# Debug script to test Docker build issues

echo "🔍 Debugging Docker build context..."

echo "📁 Current directory contents:"
ls -la

echo "📁 Data directory contents:"
ls -la data/

echo "📁 Artifacts directory contents:"
ls -la artifacts/

echo "🐳 Testing Docker build with verbose output..."
docker build --no-cache --progress=plain -t debug-iris-api . 2>&1 | tee docker-build-debug.log

echo "📝 Build log saved to docker-build-debug.log"