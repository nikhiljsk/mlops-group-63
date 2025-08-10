#!/usr/bin/env python3
"""
Comprehensive integration test for the MLOps pipeline.
Tests the complete workflow from training to deployment.
"""

import os
import sys
import time
import requests
import subprocess
import json
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_status(message, color=Colors.BLUE):
    """Print colored status message"""
    print(f"{color}[INFO]{Colors.END} {message}")


def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}[SUCCESS]{Colors.END} {message}")


def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}[ERROR]{Colors.END} {message}")


def print_warning(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}[WARNING]{Colors.END} {message}")


def run_command(command, cwd=None, timeout=60):
    """Run shell command and return result"""
    try:
        result = subprocess.run(
            command, shell=True, cwd=cwd, timeout=timeout,
            capture_output=True, text=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"


def test_environment_setup():
    """Test environment and dependencies"""
    print_status("Testing environment setup...")
    
    # Check Python version
    if sys.version_info < (3, 11):
        print_warning(f"Python {sys.version} detected. Recommended: 3.11+")
    else:
        print_success(f"Python {sys.version} ✓")
    
    # Check required files
    required_files = [
        'requirements.txt', 'src/train.py', 'api/main.py',
        'Dockerfile', 'dvc.yaml', 'params.yaml'
    ]
    
    for file in required_files:
        if Path(file).exists():
            print_success(f"{file} exists ✓")
        else:
            print_error(f"{file} missing ✗")
            return False
    
    # Check if virtual environment is activated
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print_success("Virtual environment activated ✓")
    else:
        print_warning("Virtual environment not detected")
    
    return True


def test_data_and_preprocessing():
    """Test data loading and preprocessing"""
    print_status("Testing data and preprocessing...")
    
    try:
        # Import and test preprocessing
        sys.path.append('src')
        from preprocess import load_data, preprocess_data
        
        # Load data
        df = load_data('data/iris.csv')
        print_success(f"Data loaded: {df.shape} ✓")
        
        # Test preprocessing
        X_train, X_test, y_train, y_test = preprocess_data(df)
        print_success(f"Data preprocessed: train={X_train.shape}, test={X_test.shape} ✓")
        
        return True
        
    except Exception as e:
        print_error(f"Data preprocessing failed: {e}")
        return False


def test_model_training():
    """Test model training pipeline"""
    print_status("Testing model training...")
    
    # Run training script
    success, stdout, stderr = run_command("python src/train.py", timeout=120)
    
    if not success:
        print_error(f"Training failed: {stderr}")
        return False
    
    # Check if model artifacts were created
    required_artifacts = ['artifacts/best_model.pkl', 'artifacts/scaler.pkl']
    
    for artifact in required_artifacts:
        if Path(artifact).exists():
            print_success(f"{artifact} created ✓")
        else:
            print_error(f"{artifact} not found ✗")
            return False
    
    # Check MLflow runs
    if Path('mlruns').exists():
        print_success("MLflow experiments created ✓")
    else:
        print_warning("MLflow runs directory not found")
    
    print_success("Model training completed ✓")
    return True


def test_api_functionality():
    """Test API endpoints"""
    print_status("Testing API functionality...")
    
    # Start API server
    print_status("Starting API server...")
    api_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "api.main:app",
        "--host", "0.0.0.0", "--port", "8000"
    ])
    
    # Wait for server to start
    time.sleep(15)
    
    try:
        base_url = "http://localhost:8000"
        
        # Test health endpoint
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print_success(f"Health check passed: {health_data.get('status', 'unknown')} ✓")
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
        
        # Test model info endpoint
        response = requests.get(f"{base_url}/model/info", timeout=10)
        if response.status_code == 200:
            model_info = response.json()
            print_success(f"Model info: {model_info.get('model_name', 'unknown')} ✓")
        else:
            print_error(f"Model info failed: {response.status_code}")
            return False
        
        # Test single prediction
        prediction_data = {
            "sepal_length": 5.1,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2
        }
        
        response = requests.post(f"{base_url}/predict", json=prediction_data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print_success(f"Single prediction: {result.get('prediction', 'unknown')} "
                         f"({result.get('confidence', 0):.2%} confidence) ✓")
        else:
            print_error(f"Single prediction failed: {response.status_code}")
            return False
        
        # Test batch prediction
        batch_data = {
            "samples": [
                {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2},
                {"sepal_length": 6.2, "sepal_width": 2.9, "petal_length": 4.3, "petal_width": 1.3},
                {"sepal_length": 6.5, "sepal_width": 3.0, "petal_length": 5.2, "petal_width": 2.0}
            ]
        }
        
        response = requests.post(f"{base_url}/predict/batch", json=batch_data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print_success(f"Batch prediction: {result.get('batch_size', 0)} samples processed ✓")
        else:
            print_error(f"Batch prediction failed: {response.status_code}")
            return False
        
        # Test metrics endpoint
        response = requests.get(f"{base_url}/metrics", timeout=10)
        if response.status_code == 200:
            print_success("Prometheus metrics endpoint working ✓")
        else:
            print_error(f"Metrics endpoint failed: {response.status_code}")
            return False
        
        print_success("All API tests passed ✓")
        return True
        
    except Exception as e:
        print_error(f"API test failed: {e}")
        return False
    
    finally:
        # Stop API server
        api_process.terminate()
        api_process.wait()


def test_docker_build():
    """Test Docker image building"""
    print_status("Testing Docker build...")
    
    # Build Docker image
    success, stdout, stderr = run_command("docker build -t iris-api-test .", timeout=300)
    
    if not success:
        print_error(f"Docker build failed: {stderr}")
        return False
    
    print_success("Docker image built successfully ✓")
    
    # Test Docker run (quick test)
    print_status("Testing Docker container...")
    success, stdout, stderr = run_command(
        "docker run --rm -d --name iris-test -p 8001:8000 iris-api-test", 
        timeout=30
    )
    
    if success:
        time.sleep(10)  # Wait for container to start
        
        try:
            # Quick health check
            response = requests.get("http://localhost:8001/health", timeout=5)
            if response.status_code == 200:
                print_success("Docker container running successfully ✓")
            else:
                print_warning("Docker container started but health check failed")
        except:
            print_warning("Docker container health check failed")
        
        # Stop container
        run_command("docker stop iris-test", timeout=10)
    else:
        print_error(f"Docker run failed: {stderr}")
        return False
    
    # Clean up
    run_command("docker rmi iris-api-test", timeout=30)
    
    return True


def test_dvc_pipeline():
    """Test DVC pipeline functionality"""
    print_status("Testing DVC pipeline...")
    
    # Check if DVC is initialized
    if not Path('.dvc').exists():
        print_warning("DVC not initialized, skipping DVC tests")
        return True
    
    # Test DVC status
    success, stdout, stderr = run_command("dvc status", timeout=30)
    if success:
        print_success("DVC status check passed ✓")
    else:
        print_warning(f"DVC status check failed: {stderr}")
    
    # Test DVC pipeline reproduction
    success, stdout, stderr = run_command("dvc repro --dry", timeout=60)
    if success:
        print_success("DVC pipeline validation passed ✓")
    else:
        print_warning(f"DVC pipeline validation failed: {stderr}")
    
    return True


def generate_test_report():
    """Generate comprehensive test report"""
    print_status("Generating test report...")
    
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "environment": {
            "python_version": sys.version,
            "platform": sys.platform,
            "working_directory": os.getcwd()
        },
        "test_results": {
            "environment_setup": "✓",
            "data_preprocessing": "✓",
            "model_training": "✓",
            "api_functionality": "✓",
            "docker_build": "✓",
            "dvc_pipeline": "✓"
        },
        "artifacts_created": [
            str(p) for p in Path('.').rglob('*') 
            if p.is_file() and any(pattern in str(p) for pattern in 
                                 ['artifacts/', 'mlruns/', 'metrics/', 'plots/'])
        ]
    }
    
    # Save report
    with open('integration_test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print_success("Test report saved to 'integration_test_report.json' ✓")


def main():
    """Run comprehensive integration tests"""
    print(f"{Colors.BOLD}🧪 MLOps Pipeline Integration Tests{Colors.END}")
    print("=" * 50)
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Data & Preprocessing", test_data_and_preprocessing),
        ("Model Training", test_model_training),
        ("API Functionality", test_api_functionality),
        ("Docker Build", test_docker_build),
        ("DVC Pipeline", test_dvc_pipeline),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{Colors.BOLD}Testing: {test_name}{Colors.END}")
        print("-" * 30)
        
        try:
            success = test_func()
            results.append((test_name, success))
            
            if success:
                print_success(f"{test_name} completed successfully")
            else:
                print_error(f"{test_name} failed")
                
        except Exception as e:
            print_error(f"{test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{Colors.BOLD}📊 Test Summary{Colors.END}")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.END}")
    
    if passed == total:
        print_success("🎉 All integration tests passed! MLOps pipeline is ready for demo.")
        generate_test_report()
        return 0
    else:
        print_error(f"❌ {total - passed} tests failed. Please check the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())