#!/bin/bash

# Conda Environment Validation Script
# Validates that the jsk-ml conda environment has all required packages

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

echo -e "${BLUE}🔍 Conda Environment Validation${NC}"
echo "================================="
echo ""

# Check if conda is available
if ! command -v conda &> /dev/null; then
    print_error "Conda not found. Please install conda first."
    exit 1
fi

print_status "Conda found: $(conda --version)"

# Check if environment exists
if ! conda env list | grep -q "^$CONDA_ENV_NAME "; then
    print_error "Conda environment '$CONDA_ENV_NAME' not found."
    print_info "Available environments:"
    conda env list
    print_info ""
    print_info "To create the environment, run:"
    print_info "conda create -n $CONDA_ENV_NAME python=3.11"
    print_info "conda activate $CONDA_ENV_NAME"
    print_info "pip install -r requirements.txt"
    exit 1
fi

print_status "Conda environment '$CONDA_ENV_NAME' found"

# Activate environment
print_info "Activating conda environment..."

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

conda activate "$CONDA_ENV_NAME"

if [ "$CONDA_DEFAULT_ENV" != "$CONDA_ENV_NAME" ]; then
    print_error "Failed to activate conda environment: $CONDA_ENV_NAME"
    exit 1
fi

print_status "Successfully activated conda environment: $CONDA_DEFAULT_ENV"

# Check Python version
python_version=$(python --version 2>&1)
print_info "Python version: $python_version"

# Check required packages
print_info "Checking required packages..."

required_packages=(
    "fastapi"
    "uvicorn"
    "pydantic"
    "scikit-learn"
    "pandas"
    "numpy"
    "joblib"
    "mlflow"
    "pytest"
    "requests"
    "prometheus-client"
    "sqlite3"  # Built-in, but we'll check
)

missing_packages=()
installed_packages=()

for package in "${required_packages[@]}"; do
    if python -c "import $package" 2>/dev/null; then
        installed_packages+=("$package")
    else
        # Special case for sklearn
        if [ "$package" = "scikit-learn" ]; then
            if python -c "import sklearn" 2>/dev/null; then
                installed_packages+=("$package")
            else
                missing_packages+=("$package")
            fi
        else
            missing_packages+=("$package")
        fi
    fi
done

# Report results
echo ""
print_info "Package Status:"
for package in "${installed_packages[@]}"; do
    print_status "$package"
done

if [ ${#missing_packages[@]} -gt 0 ]; then
    echo ""
    print_warning "Missing packages:"
    for package in "${missing_packages[@]}"; do
        print_error "$package"
    done
    
    echo ""
    print_info "To install missing packages, run:"
    print_info "conda activate $CONDA_ENV_NAME"
    print_info "pip install ${missing_packages[*]}"
    exit 1
fi

# Check package versions
echo ""
print_info "Package versions:"
python -c "
import sys
packages_to_check = ['fastapi', 'uvicorn', 'sklearn', 'pandas', 'numpy', 'mlflow', 'pytest']

for package in packages_to_check:
    try:
        if package == 'sklearn':
            import sklearn
            print(f'  scikit-learn: {sklearn.__version__}')
        else:
            module = __import__(package)
            if hasattr(module, '__version__'):
                print(f'  {package}: {module.__version__}')
            else:
                print(f'  {package}: installed (version unknown)')
    except ImportError:
        print(f'  {package}: not installed')
"

# Test basic functionality
echo ""
print_info "Testing basic functionality..."

# Test FastAPI import
python -c "
from fastapi import FastAPI
app = FastAPI()
print('✅ FastAPI import successful')
"

# Test scikit-learn
python -c "
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import numpy as np

# Create dummy model
model = LogisticRegression()
scaler = StandardScaler()
X = np.random.rand(10, 4)
y = np.random.choice(['a', 'b', 'c'], 10)
scaler.fit(X)
model.fit(scaler.transform(X), y)
print('✅ Scikit-learn functionality test successful')
"

# Test MLflow
python -c "
import mlflow
print('✅ MLflow import successful')
"

# Test pytest
python -c "
import pytest
print('✅ Pytest import successful')
"

echo ""
print_status "🎉 Conda environment validation successful!"
print_info "Environment '$CONDA_ENV_NAME' is ready for MLOps pipeline testing."

# Show environment summary
echo ""
print_info "Environment Summary:"
print_info "  Name: $CONDA_DEFAULT_ENV"
print_info "  Python: $(which python)"
print_info "  Pip: $(which pip)"
print_info "  Location: $CONDA_PREFIX"

echo ""
print_info "To run end-to-end tests:"
print_info "  ./scripts/run-e2e-tests.sh"
print_info ""
print_info "To run individual test suites:"
print_info "  conda activate $CONDA_ENV_NAME"
print_info "  python -m pytest tests/e2e/ -v"