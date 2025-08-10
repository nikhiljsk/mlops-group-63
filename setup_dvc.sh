#!/bin/bash

# DVC Setup Script for MLOps Pipeline
# This script initializes DVC for data and model versioning

set -e

echo "🔧 Setting up DVC for MLOps pipeline..."

# Initialize DVC if not already initialized
if [ ! -d ".dvc" ]; then
    echo "📦 Initializing DVC..."
    dvc init --no-scm
    echo "✅ DVC initialized"
else
    echo "✅ DVC already initialized"
fi

# Add data to DVC tracking
if [ -f "data/iris.csv" ] && [ ! -f "data/iris.csv.dvc" ]; then
    echo "📊 Adding data to DVC tracking..."
    dvc add data/iris.csv
    echo "✅ Data added to DVC"
fi

# Add artifacts directory to DVC tracking
if [ -d "artifacts" ] && [ ! -f "artifacts.dvc" ]; then
    echo "🎯 Adding artifacts to DVC tracking..."
    dvc add artifacts/
    echo "✅ Artifacts added to DVC"
fi

# Create metrics and plots directories
mkdir -p metrics plots

# Add DVC files to git
echo "📝 Adding DVC files to git..."
git add data/iris.csv.dvc artifacts.dvc .dvcignore dvc.yaml params.yaml

echo "🎉 DVC setup complete!"
echo ""
echo "Next steps:"
echo "1. Run 'dvc repro' to execute the pipeline"
echo "2. Use 'dvc metrics show' to view metrics"
echo "3. Use 'dvc plots show' to view plots"
echo "4. Commit changes: git commit -m 'Add DVC pipeline'"