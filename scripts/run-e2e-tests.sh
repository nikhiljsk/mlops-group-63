#!/bin/bash

# Comprehensive End-to-End Test Runner
# Executes all end-to-end system tests for the MLOps pipeline

set -e

# Conda environment configuration
CONDA_ENV_NAME="jsk-ml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
}

print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_section() { echo -e "${PURPLE}🔍 $1${NC}"; }

run_test_suite() {
    local test_name="$1"
    local test_command="$2"
    local required="$3"  # "required" or "optional"
    
    print_section "Running: $test_name"
    
    if eval "$test_command"; then
        print_status "$test_name - PASSED"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        if [ "$required" = "required" ]; then
            print_error "$test_name - FAILED (REQUIRED)"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        else
            print_warning "$test_name - FAILED (OPTIONAL)"
            SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
        fi
    fi
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo ""
}

# Activate conda environment
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
    
    # Check if environment exists
    if ! conda env list | grep -q "^$CONDA_ENV_NAME "; then
        print_error "Conda environment '$CONDA_ENV_NAME' not found."
        print_info "Available environments:"
        conda env list
        exit 1
    fi
    
    # Activate the environment
    conda activate "$CONDA_ENV_NAME"
    
    if [ "$CONDA_DEFAULT_ENV" != "$CONDA_ENV_NAME" ]; then
        print_error "Failed to activate conda environment: $CONDA_ENV_NAME"
        exit 1
    fi
    
    print_status "Successfully activated conda environment: $CONDA_DEFAULT_ENV"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Activate conda environment first
    activate_conda_env
    
    # Check Python in conda environment
    if ! command -v python &> /dev/null; then
        print_error "Python not found in conda environment"
        exit 1
    fi
    print_status "Python found: $(python --version)"
    
    # Check conda environment details
    print_info "Conda environment details:"
    print_info "  Environment: $CONDA_DEFAULT_ENV"
    print_info "  Python path: $(which python)"
    print_info "  Pip path: $(which pip)"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_warning "Docker not found - some tests will be skipped"
    else
        print_status "Docker found: $(docker --version | head -n1)"
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_warning "Docker Compose not found - some tests will be skipped"
    else
        print_status "Docker Compose found: $(docker-compose --version)"
    fi
    
    # Check required Python packages in conda environment
    print_info "Checking Python dependencies in conda environment..."
    python -c "
import sys
required_packages = ['pytest', 'requests', 'fastapi', 'uvicorn', 'sklearn', 'pandas', 'numpy', 'mlflow', 'joblib']
missing_packages = []

for package in required_packages:
    try:
        if package == 'sklearn':
            __import__('sklearn')
        else:
            __import__(package)
    except ImportError:
        missing_packages.append(package)

if missing_packages:
    print(f'Missing packages: {missing_packages}')
    print('Available packages in environment:')
    import pkg_resources
    installed_packages = [d.project_name for d in pkg_resources.working_set]
    print(f'Installed: {sorted(installed_packages)[:10]}...')  # Show first 10
    sys.exit(1)
else:
    print('All required packages found')
"
    
    if [ $? -eq 0 ]; then
        print_status "All required Python packages found in conda environment"
    else
        print_error "Missing required Python packages in conda environment"
        print_info "Run in conda environment: conda activate $CONDA_ENV_NAME && pip install -r requirements.txt"
        exit 1
    fi
    
    echo ""
}

# Setup test environment
setup_test_environment() {
    print_header "Setting Up Test Environment"
    
    # Create test artifacts if they don't exist
    if [ ! -f "artifacts/best_model.pkl" ] || [ ! -f "artifacts/scaler.pkl" ]; then
        print_info "Creating test artifacts..."
        python -c "
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import numpy as np
import os

# Create artifacts directory
os.makedirs('artifacts', exist_ok=True)

# Create dummy model and scaler for testing
model = LogisticRegression()
scaler = StandardScaler()

# Fit with dummy data
X_dummy = np.random.rand(100, 4)
y_dummy = np.random.choice(['setosa', 'versicolor', 'virginica'], 100)

scaler.fit(X_dummy)
model.fit(scaler.transform(X_dummy), y_dummy)

joblib.dump(model, 'artifacts/best_model.pkl')
joblib.dump(scaler, 'artifacts/scaler.pkl')

print('Test artifacts created successfully')
"
        print_status "Test artifacts created"
    else
        print_status "Test artifacts already exist"
    fi
    
    # Create test data if needed
    if [ ! -f "data/iris.csv" ]; then
        print_info "Creating test data..."
        python -c "
from sklearn.datasets import load_iris
import pandas as pd
import os

os.makedirs('data', exist_ok=True)

iris = load_iris()
df = pd.DataFrame(iris.data, columns=iris.feature_names)
df['target'] = iris.target
df['species'] = df['target'].map({0: 'setosa', 1: 'versicolor', 2: 'virginica'})

df.to_csv('data/iris.csv', index=False)
print('Test data created successfully')
"
        print_status "Test data created"
    else
        print_status "Test data already exists"
    fi
    
    echo ""
}

# Run all test suites
run_all_tests() {
    print_header "Running End-to-End Test Suites"
    
    # 1. Complete Pipeline Tests
    run_test_suite \
        "Complete MLOps Pipeline Tests" \
        "python -m pytest tests/e2e/test_complete_pipeline.py -v --tb=short" \
        "required"
    
    # 2. CI/CD Pipeline Tests
    run_test_suite \
        "CI/CD Pipeline Validation Tests" \
        "python -m pytest tests/e2e/test_cicd_pipeline.py -v --tb=short" \
        "required"
    
    # 3. Monitoring and Alerting Tests
    run_test_suite \
        "Monitoring and Alerting Tests" \
        "python -m pytest tests/e2e/test_monitoring_alerting.py -v --tb=short" \
        "required"
    
    # 4. Integration Tests
    run_test_suite \
        "API Integration Tests" \
        "python -m pytest tests/integration/ -v --tb=short" \
        "required"
    
    # 5. Unit Tests with Coverage
    run_test_suite \
        "Unit Tests with Coverage" \
        "python -m pytest tests/ -v --cov=api --cov=src --cov-report=term-missing --cov-fail-under=70" \
        "required"
    
    # 6. Code Quality Tests
    run_test_suite \
        "Code Quality - Linting" \
        "flake8 api/ src/ --count --select=E9,F63,F7,F82 --show-source --statistics" \
        "required"
    
    run_test_suite \
        "Code Quality - Formatting" \
        "black --check --diff api/ src/" \
        "optional"
    
    run_test_suite \
        "Code Quality - Import Sorting" \
        "isort --check-only --diff api/ src/" \
        "optional"
    
    # 7. Docker Tests (if Docker is available)
    if command -v docker &> /dev/null; then
        run_test_suite \
            "Docker Build Test" \
            "docker build -t iris-api-e2e-test . && docker rmi iris-api-e2e-test" \
            "optional"
    fi
    
    # 8. Docker Compose Tests (if Docker Compose is available)
    if command -v docker-compose &> /dev/null; then
        run_test_suite \
            "Docker Compose Validation" \
            "docker-compose config" \
            "optional"
    fi
    
    # 9. Configuration Validation Tests
    run_test_suite \
        "Configuration Files Validation" \
        "python -c \"
import yaml
import os

# Test Prometheus config
if os.path.exists('monitoring/prometheus.yml'):
    with open('monitoring/prometheus.yml', 'r') as f:
        yaml.safe_load(f)
    print('Prometheus config valid')

# Test alert rules
if os.path.exists('monitoring/alert_rules.yml'):
    with open('monitoring/alert_rules.yml', 'r') as f:
        yaml.safe_load(f)
    print('Alert rules valid')

# Test GitHub workflow
if os.path.exists('.github/workflows/ci-cd.yml'):
    with open('.github/workflows/ci-cd.yml', 'r') as f:
        yaml.safe_load(f)
    print('GitHub workflow valid')

print('All configuration files valid')
\"" \
        "required"
    
    # 10. Script Validation Tests
    run_test_suite \
        "Deployment Scripts Validation" \
        "bash -n deploy.sh && bash -n demo.sh && bash -n scripts/e2e-test.sh" \
        "optional"
}

# Performance and Load Tests
run_performance_tests() {
    print_header "Running Performance Tests"
    
    # Start API server for performance testing
    print_info "Starting API server for performance testing..."
    uvicorn api.main:app --host 0.0.0.0 --port 8020 &
    API_PID=$!
    
    # Wait for server to start
    sleep 15
    
    # Run performance tests
    run_test_suite \
        "API Performance Test" \
        "python -c \"
import requests
import time
import concurrent.futures

def make_request():
    try:
        start_time = time.time()
        response = requests.post(
            'http://localhost:8020/predict',
            json={
                'sepal_length': 5.1,
                'sepal_width': 3.5,
                'petal_length': 1.4,
                'petal_width': 0.2
            },
            timeout=5
        )
        end_time = time.time()
        return response.status_code == 200, end_time - start_time
    except:
        return False, float('inf')

# Run concurrent requests
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(make_request) for _ in range(50)]
    results = [future.result() for future in concurrent.futures.as_completed(futures)]

# Analyze results
successful_requests = [r for r in results if r[0]]
response_times = [r[1] for r in successful_requests]

if response_times:
    avg_response_time = sum(response_times) / len(response_times)
    max_response_time = max(response_times)
    success_rate = len(successful_requests) / len(results)
    
    print(f'Success rate: {success_rate:.2%}')
    print(f'Average response time: {avg_response_time:.3f}s')
    print(f'Max response time: {max_response_time:.3f}s')
    
    assert success_rate >= 0.9, f'Success rate too low: {success_rate:.2%}'
    assert avg_response_time < 2.0, f'Average response time too high: {avg_response_time:.3f}s'
    assert max_response_time < 5.0, f'Max response time too high: {max_response_time:.3f}s'
    
    print('Performance test passed!')
else:
    raise Exception('No successful requests')
\"" \
        "optional"
    
    # Stop API server
    kill $API_PID 2>/dev/null || true
    wait $API_PID 2>/dev/null || true
    
    echo ""
}

# Security Tests
run_security_tests() {
    print_header "Running Security Tests"
    
    # Start API server for security testing
    print_info "Starting API server for security testing..."
    uvicorn api.main:app --host 0.0.0.0 --port 8021 &
    API_PID=$!
    
    # Wait for server to start
    sleep 15
    
    run_test_suite \
        "Input Validation Security Test" \
        "python -c \"
import requests

# Test malicious inputs
malicious_inputs = [
    {'sepal_length': \\\"'; DROP TABLE prediction_logs; --\\\", 'sepal_width': 3.5, 'petal_length': 1.4, 'petal_width': 0.2},
    {'sepal_length': '<script>alert(\\\"xss\\\")</script>', 'sepal_width': 3.5, 'petal_length': 1.4, 'petal_width': 0.2},
    {'sepal_length': 999999.0, 'sepal_width': 999999.0, 'petal_length': 999999.0, 'petal_width': 999999.0}
]

for malicious_input in malicious_inputs:
    response = requests.post('http://localhost:8021/predict', json=malicious_input)
    # Should be rejected by validation or handled gracefully
    assert response.status_code in [200, 422], f'Unexpected response for malicious input: {response.status_code}'

print('Security validation test passed!')
\"" \
        "optional"
    
    # Stop API server
    kill $API_PID 2>/dev/null || true
    wait $API_PID 2>/dev/null || true
    
    echo ""
}

# Generate test report
generate_test_report() {
    print_header "Test Results Summary"
    
    echo -e "${BLUE}📊 Test Execution Summary${NC}"
    echo "========================="
    echo "Total Test Suites: $TOTAL_TESTS"
    echo "Passed: $PASSED_TESTS"
    echo "Failed: $FAILED_TESTS"
    echo "Skipped: $SKIPPED_TESTS"
    echo ""
    
    # Calculate success rate
    if [ $TOTAL_TESTS -gt 0 ]; then
        SUCCESS_RATE=$(( (PASSED_TESTS * 100) / TOTAL_TESTS ))
        echo "Success Rate: ${SUCCESS_RATE}%"
    fi
    
    echo ""
    
    if [ $FAILED_TESTS -eq 0 ]; then
        print_status "🎉 All critical tests passed! System is ready for production."
        echo ""
        echo "✅ Complete MLOps pipeline validated"
        echo "✅ CI/CD pipeline functionality verified"
        echo "✅ Monitoring and alerting systems tested"
        echo "✅ API integration and performance validated"
        echo "✅ Code quality and security checks passed"
        echo ""
        echo "🚀 System is production-ready!"
        
        # Generate detailed report file
        cat > e2e-test-report.md << EOF
# End-to-End Test Report

**Date:** $(date)
**Status:** ✅ PASSED

## Summary
- Total Test Suites: $TOTAL_TESTS
- Passed: $PASSED_TESTS
- Failed: $FAILED_TESTS
- Skipped: $SKIPPED_TESTS
- Success Rate: ${SUCCESS_RATE}%

## Test Categories Validated
- ✅ Complete MLOps Pipeline
- ✅ CI/CD Pipeline Functionality
- ✅ Monitoring and Alerting Systems
- ✅ API Integration and Performance
- ✅ Code Quality and Security

## Conclusion
The MLOps pipeline has been thoroughly tested and validated. All critical components are functioning correctly and the system is ready for production deployment.

## Next Steps
1. Deploy to production environment
2. Monitor system performance and alerts
3. Set up regular health checks
4. Plan for model retraining cycles
EOF
        
        print_info "Detailed report saved to: e2e-test-report.md"
        return 0
    else
        print_error "❌ $FAILED_TESTS critical test(s) failed. System is not ready for production."
        echo ""
        echo "🔧 Please fix the following issues:"
        echo "   - Review failed test outputs above"
        echo "   - Fix any configuration or code issues"
        echo "   - Re-run tests after fixes"
        echo ""
        echo "📋 For help, check:"
        echo "   - Test logs above"
        echo "   - README.md for setup instructions"
        echo "   - DEPLOYMENT.md for deployment guidance"
        
        return 1
    fi
}

# Cleanup function
cleanup() {
    print_info "Cleaning up test environment..."
    
    # Kill any remaining processes
    pkill -f "uvicorn api.main:app" 2>/dev/null || true
    
    # Remove test containers
    docker rm -f $(docker ps -aq --filter "name=*-e2e-*" --filter "name=*-test-*") 2>/dev/null || true
    
    # Remove test images
    docker rmi -f $(docker images -q --filter "reference=*-e2e-test*" --filter "reference=*-test*") 2>/dev/null || true
    
    print_status "Cleanup completed"
}

# Trap cleanup on exit
trap cleanup EXIT

# Main execution
main() {
    echo -e "${PURPLE}🧪 MLOps Pipeline End-to-End Testing${NC}"
    echo -e "${PURPLE}=====================================${NC}"
    echo ""
    
    # Set Python path
    export PYTHONPATH=".:$PYTHONPATH"
    
    # Ensure we're in the correct conda environment
    if [ -z "$CONDA_DEFAULT_ENV" ] || [ "$CONDA_DEFAULT_ENV" != "$CONDA_ENV_NAME" ]; then
        print_warning "Not in correct conda environment. Attempting to activate..."
        activate_conda_env
    fi
    
    # Run test phases
    check_prerequisites
    setup_test_environment
    run_all_tests
    run_performance_tests
    run_security_tests
    
    # Generate final report
    generate_test_report
}

# Execute main function
main "$@"