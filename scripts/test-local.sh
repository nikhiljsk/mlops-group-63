#!/bin/bash

# Local testing script for CI/CD pipeline validation
# This script mimics what the GitHub Actions workflow does

set -e  # Exit on any error

echo "🚀 Starting local CI/CD pipeline test..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Python is available
if ! command -v python &> /dev/null; then
    print_error "Python is not installed or not in PATH"
    exit 1
fi

print_status "Python version: $(python --version)"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt
pip install flake8 black isort

# Create dummy artifacts for testing
echo "🔧 Creating test artifacts..."
mkdir -p artifacts
python -c "
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import numpy as np

# Create dummy model and scaler for testing
model = LogisticRegression(random_state=42)
scaler = StandardScaler()

# Fit with dummy data
X_dummy = np.random.RandomState(42).rand(100, 4)
y_dummy = np.random.RandomState(42).choice(['setosa', 'versicolor', 'virginica'], 100)

X_scaled = scaler.fit_transform(X_dummy)
model.fit(X_scaled, y_dummy)

joblib.dump(model, 'artifacts/best_model.pkl')
joblib.dump(scaler, 'artifacts/scaler.pkl')
print('✅ Test artifacts created')
"

# Run linting
echo "🔍 Running code linting..."
echo "  - Checking for syntax errors..."
flake8 api/ src/ --count --select=E9,F63,F7,F82 --show-source --statistics || {
    print_error "Syntax errors found!"
    exit 1
}

echo "  - Running full linting..."
flake8 api/ src/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

print_status "Linting completed"

# Check code formatting
echo "🎨 Checking code formatting..."
black --check --diff api/ src/ || {
    print_warning "Code formatting issues found. Run 'make format' to fix."
}

isort --check-only --diff api/ src/ || {
    print_warning "Import sorting issues found. Run 'make format' to fix."
}

print_status "Code formatting check completed"

# Run unit tests
echo "🧪 Running unit tests..."
export PYTHONPATH=.
pytest tests/ -v --cov=api --cov=src --cov-report=term-missing --cov-report=xml || {
    print_error "Unit tests failed!"
    exit 1
}

print_status "Unit tests completed"

# Test Docker build
echo "🐳 Testing Docker build..."
docker build -t iris-classifier-api:test . || {
    print_error "Docker build failed!"
    exit 1
}

print_status "Docker build completed"

# Test Docker container
echo "🔧 Testing Docker container..."
echo "  - Starting container..."
docker run -d --name test-container -p 8001:8000 iris-classifier-api:test

# Wait for container to be ready
echo "  - Waiting for container to be ready..."
sleep 30

# Test health endpoint
echo "  - Testing health endpoint..."
curl -f http://localhost:8001/health || {
    print_error "Health endpoint test failed!"
    docker logs test-container
    docker stop test-container
    docker rm test-container
    exit 1
}

# Test prediction endpoint
echo "  - Testing prediction endpoint..."
curl -f -X POST "http://localhost:8001/predict" \
  -H "Content-Type: application/json" \
  -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}' || {
    print_error "Prediction endpoint test failed!"
    docker logs test-container
    docker stop test-container
    docker rm test-container
    exit 1
}

# Clean up container
echo "  - Cleaning up test container..."
docker stop test-container
docker rm test-container

print_status "Docker container tests completed"

# Run security scan (if trivy is available)
if command -v trivy &> /dev/null; then
    echo "🔒 Running security scan..."
    trivy image iris-classifier-api:test || {
        print_warning "Security scan found issues (non-blocking)"
    }
    print_status "Security scan completed"
else
    print_warning "Trivy not installed, skipping security scan"
fi

echo ""
print_status "🎉 All local CI/CD pipeline tests passed!"
echo ""
echo "Your code is ready for:"
echo "  - ✅ Linting and code quality checks"
echo "  - ✅ Unit testing with coverage"
echo "  - ✅ Docker containerization"
echo "  - ✅ API functionality testing"
echo ""
echo "Next steps:"
echo "  1. Commit your changes"
echo "  2. Push to GitHub to trigger the full CI/CD pipeline"
echo "  3. Monitor the GitHub Actions workflow"
echo ""