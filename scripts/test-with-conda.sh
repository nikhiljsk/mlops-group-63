#!/bin/bash

# Test execution script for conda environment
# Ensures all tests run in the correct jsk-ml conda environment

set -e

CONDA_ENV_NAME="jsk-ml"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

# Function to activate conda environment
activate_conda_env() {
    print_info "Activating conda environment: $CONDA_ENV_NAME"
    
    # Initialize conda for bash
    if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
        source "$HOME/miniconda3/etc/profile.d/conda.sh"
    elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
        source "$HOME/anaconda3/etc/profile.d/conda.sh"
    elif [ -f "/opt/conda/etc/profile.d/conda.sh" ]; then
        source "/opt/conda/etc/profile.d/conda.sh"
    else
        # Try to find conda in common locations
        for conda_path in "$HOME/miniconda3/bin/conda" "$HOME/anaconda3/bin/conda" "/opt/conda/bin/conda"; do
            if [ -f "$conda_path" ]; then
                eval "$($conda_path shell.bash hook)"
                break
            fi
        done
    fi
    
    # Check if conda is available
    if ! command -v conda &> /dev/null; then
        print_error "Conda not found. Please ensure conda is installed and in PATH."
        exit 1
    fi
    
    # Activate the environment
    conda activate "$CONDA_ENV_NAME" || {
        print_error "Failed to activate conda environment: $CONDA_ENV_NAME"
        print_info "Available environments:"
        conda env list
        exit 1
    }
    
    print_status "Successfully activated conda environment: $CONDA_DEFAULT_ENV"
}

# Parse command line arguments
TEST_TYPE="all"
VERBOSE=""
COVERAGE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            TEST_TYPE="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE="-v"
            shift
            ;;
        -c|--coverage)
            COVERAGE="--cov=api --cov=src --cov-report=term-missing"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -t, --type TYPE     Test type: unit, integration, e2e, all (default: all)"
            echo "  -v, --verbose       Verbose output"
            echo "  -c, --coverage      Run with coverage"
            echo "  -h, --help          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                          # Run all tests"
            echo "  $0 -t unit -v -c           # Run unit tests with verbose output and coverage"
            echo "  $0 -t e2e                  # Run only end-to-end tests"
            echo "  $0 -t integration          # Run only integration tests"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}🧪 MLOps Pipeline Testing with Conda${NC}"
echo "====================================="
echo ""

# Ensure we're in the correct conda environment
if [ -z "$CONDA_DEFAULT_ENV" ] || [ "$CONDA_DEFAULT_ENV" != "$CONDA_ENV_NAME" ]; then
    activate_conda_env
fi

# Verify environment
print_info "Environment: $CONDA_DEFAULT_ENV"
print_info "Python: $(which python)"
print_info "Python version: $(python --version)"
print_info "Test type: $TEST_TYPE"

# Set Python path
export PYTHONPATH=".:$PYTHONPATH"

# Create artifacts if they don't exist
if [ ! -f "artifacts/best_model.pkl" ] || [ ! -f "artifacts/scaler.pkl" ]; then
    print_info "Creating test artifacts..."
    python -c "
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import numpy as np
import os

os.makedirs('artifacts', exist_ok=True)

model = LogisticRegression()
scaler = StandardScaler()
X_dummy = np.random.rand(100, 4)
y_dummy = np.random.choice(['setosa', 'versicolor', 'virginica'], 100)
scaler.fit(X_dummy)
model.fit(scaler.transform(X_dummy), y_dummy)
joblib.dump(model, 'artifacts/best_model.pkl')
joblib.dump(scaler, 'artifacts/scaler.pkl')
print('Test artifacts created')
"
    print_status "Test artifacts created"
fi

# Run tests based on type
case $TEST_TYPE in
    "unit")
        print_info "Running unit tests..."
        python -m pytest tests/ -m "unit or not (integration or e2e)" $VERBOSE $COVERAGE
        ;;
    "integration")
        print_info "Running integration tests..."
        python -m pytest tests/integration/ $VERBOSE $COVERAGE
        ;;
    "e2e")
        print_info "Running end-to-end tests..."
        python -m pytest tests/e2e/ $VERBOSE $COVERAGE
        ;;
    "all")
        print_info "Running all tests..."
        
        # Run unit tests first
        print_info "1. Running unit tests..."
        python -m pytest tests/ -m "unit or not (integration or e2e)" $VERBOSE $COVERAGE
        
        # Run integration tests
        print_info "2. Running integration tests..."
        python -m pytest tests/integration/ $VERBOSE
        
        # Run end-to-end tests
        print_info "3. Running end-to-end tests..."
        python -m pytest tests/e2e/ $VERBOSE
        ;;
    *)
        print_error "Unknown test type: $TEST_TYPE"
        print_info "Valid types: unit, integration, e2e, all"
        exit 1
        ;;
esac

if [ $? -eq 0 ]; then
    print_status "🎉 All tests passed!"
else
    print_error "❌ Some tests failed!"
    exit 1
fi