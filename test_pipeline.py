#!/usr/bin/env python3
"""Simple test script to verify the MLOps pipeline works end-to-end."""

import requests
import time
import subprocess
import sys
import os


def test_training():
    """Test model training"""
    print("🧪 Testing model training...")
    result = subprocess.run([sys.executable, "src/train.py"], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Training failed: {result.stderr}")
        return False
    
    # Check if model files were created
    if not os.path.exists("artifacts/best_model.pkl"):
        print("❌ Model file not created")
        return False
    
    if not os.path.exists("artifacts/scaler.pkl"):
        print("❌ Scaler file not created")
        return False
    
    print("✅ Training completed successfully")
    return True


def test_api():
    """Test API endpoints"""
    print("🧪 Testing API endpoints...")
    
    # Start API server in background
    api_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "api.main:app", 
        "--host", "0.0.0.0", "--port", "8000"
    ])
    
    # Wait for server to start
    time.sleep(10)
    
    try:
        base_url = "http://localhost:8000"
        
        # Test health endpoint
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code != 200:
            print(f"❌ Health check failed: {response.status_code}")
            return False
        print("✅ Health check passed")
        
        # Test prediction endpoint
        prediction_data = {
            "sepal_length": 5.1,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2
        }
        response = requests.post(f"{base_url}/predict", json=prediction_data, timeout=10)
        if response.status_code != 200:
            print(f"❌ Prediction failed: {response.status_code}")
            return False
        
        result = response.json()
        if "prediction" not in result:
            print("❌ Prediction response missing 'prediction' field")
            return False
        
        print(f"✅ Prediction successful: {result['prediction']}")
        
        # Test metrics endpoint
        response = requests.get(f"{base_url}/metrics", timeout=10)
        if response.status_code != 200:
            print(f"❌ Metrics endpoint failed: {response.status_code}")
            return False
        print("✅ Metrics endpoint working")
        
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False
    
    finally:
        # Stop API server
        api_process.terminate()
        api_process.wait()


def main():
    """Run all tests"""
    print("🚀 Starting MLOps Pipeline Tests")
    print("=" * 50)
    
    # Test training
    if not test_training():
        print("❌ Training tests failed")
        sys.exit(1)
    
    # Test API
    if not test_api():
        print("❌ API tests failed")
        sys.exit(1)
    
    print("=" * 50)
    print("🎉 All tests passed! MLOps pipeline is working correctly.")


if __name__ == "__main__":
    main()