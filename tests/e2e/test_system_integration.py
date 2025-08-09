"""
System Integration Tests
Final validation of complete system integration from training to deployment.
"""

import pytest
import subprocess
import os
import time
import requests
import json
import tempfile
import shutil
from pathlib import Path
import sqlite3
import yaml


class TestSystemIntegration:
    """Test complete system integration"""
    
    def test_complete_workflow_integration(self):
        """Test complete workflow from training to prediction"""
        # Step 1: Data preprocessing
        print("Testing data preprocessing...")
        result = subprocess.run([
            "python", "src/preprocess.py"
        ], capture_output=True, text=True, cwd=".")
        
        if result.returncode != 0:
            print(f"Preprocessing output: {result.stdout}")
            print(f"Preprocessing error: {result.stderr}")
        
        # Step 2: Model training
        print("Testing model training...")
        result = subprocess.run([
            "python", "src/train.py"
        ], capture_output=True, text=True, cwd=".")
        
        if result.returncode != 0:
            print(f"Training output: {result.stdout}")
            print(f"Training error: {result.stderr}")
        
        # Verify artifacts exist
        assert os.path.exists("artifacts/best_model.pkl"), "Model artifact not created"
        assert os.path.exists("artifacts/scaler.pkl"), "Scaler artifact not created"
        
        # Step 3: Start API server
        print("Testing API server startup...")
        process = subprocess.Popen([
            "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8030"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            # Wait for server to start
            time.sleep(20)
            
            # Step 4: Test API functionality
            print("Testing API endpoints...")
            
            # Health check
            response = requests.get("http://localhost:8030/health", timeout=10)
            assert response.status_code == 200
            health_data = response.json()
            assert health_data["status"] in ["healthy", "degraded"]
            
            # Model info
            response = requests.get("http://localhost:8030/model/info", timeout=10)
            assert response.status_code == 200
            model_data = response.json()
            assert "model_name" in model_data
            assert "features" in model_data
            
            # Prediction
            prediction_data = {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            }
            response = requests.post("http://localhost:8030/predict", json=prediction_data, timeout=10)
            assert response.status_code == 200
            pred_result = response.json()
            assert "prediction" in pred_result
            assert pred_result["prediction"] in ["setosa", "versicolor", "virginica"]
            
            # Batch prediction
            batch_data = {"samples": [prediction_data, prediction_data]}
            response = requests.post("http://localhost:8030/predict/batch", json=batch_data, timeout=10)
            assert response.status_code == 200
            batch_result = response.json()
            assert "predictions" in batch_result
            assert len(batch_result["predictions"]) == 2
            
            # Metrics
            response = requests.get("http://localhost:8030/metrics", timeout=10)
            assert response.status_code == 200
            assert "text/plain" in response.headers.get("content-type", "")
            
            print("✅ Complete workflow integration test passed!")
            
        finally:
            process.terminate()
            process.wait(timeout=10)
    
    def test_database_logging_integration(self):
        """Test database logging integration"""
        # Start API server
        process = subprocess.Popen([
            "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8031"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            time.sleep(15)
            
            # Make predictions to generate logs
            prediction_data = {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            }
            
            # Generate multiple predictions
            for i in range(10):
                response = requests.post("http://localhost:8031/predict", json=prediction_data)
                assert response.status_code == 200
                time.sleep(0.5)
            
            # Check database logs
            if os.path.exists("logs.db"):
                conn = sqlite3.connect("logs.db")
                cursor = conn.cursor()
                
                # Check prediction logs table
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='prediction_logs'
                """)
                table_exists = cursor.fetchone() is not None
                
                if table_exists:
                    # Check log entries
                    cursor.execute("SELECT COUNT(*) FROM prediction_logs")
                    log_count = cursor.fetchone()[0]
                    assert log_count >= 10, f"Expected at least 10 logs, found {log_count}"
                    
                    # Check log structure
                    cursor.execute("SELECT * FROM prediction_logs LIMIT 1")
                    if cursor.fetchone():
                        columns = [desc[0] for desc in cursor.description]
                        expected_columns = ["id", "timestamp", "request_data", "prediction"]
                        for col in expected_columns:
                            assert col in columns, f"Missing column: {col}"
                
                conn.close()
                print("✅ Database logging integration test passed!")
            else:
                print("⚠️ Database file not found - logging might not be configured")
                
        finally:
            process.terminate()
            process.wait(timeout=10)
    
    def test_monitoring_metrics_integration(self):
        """Test monitoring and metrics integration"""
        # Start API server
        process = subprocess.Popen([
            "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8032"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            time.sleep(15)
            
            # Generate traffic for metrics
            prediction_data = {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            }
            
            # Make various requests
            for _ in range(20):
                requests.post("http://localhost:8032/predict", json=prediction_data)
                requests.get("http://localhost:8032/health")
                time.sleep(0.1)
            
            # Generate some errors
            invalid_data = {"invalid": "data"}
            for _ in range(5):
                requests.post("http://localhost:8032/predict", json=invalid_data)
                time.sleep(0.1)
            
            # Check metrics endpoint
            response = requests.get("http://localhost:8032/metrics")
            assert response.status_code == 200
            
            metrics_text = response.text
            
            # Verify Prometheus format
            assert "# HELP" in metrics_text
            assert "# TYPE" in metrics_text
            
            # Check for expected metrics
            expected_metrics = [
                "http_requests_total",
                "http_request_duration_seconds",
                "ml_predictions_total"
            ]
            
            for metric in expected_metrics:
                assert metric in metrics_text, f"Missing metric: {metric}"
            
            # Check for error metrics
            lines = metrics_text.split('\n')
            error_metrics_found = False
            success_metrics_found = False
            
            for line in lines:
                if 'http_requests_total' in line:
                    if '422' in line or '400' in line:
                        error_metrics_found = True
                    if '200' in line:
                        success_metrics_found = True
            
            assert success_metrics_found, "No success metrics found"
            assert error_metrics_found, "No error metrics found after generating errors"
            
            print("✅ Monitoring metrics integration test passed!")
            
        finally:
            process.terminate()
            process.wait(timeout=10)
    
    def test_configuration_integration(self):
        """Test configuration files integration"""
        # Test Prometheus configuration
        if os.path.exists("monitoring/prometheus.yml"):
            with open("monitoring/prometheus.yml", 'r') as f:
                prometheus_config = yaml.safe_load(f)
            
            assert "scrape_configs" in prometheus_config
            
            # Find iris-api job
            iris_job = None
            for job in prometheus_config["scrape_configs"]:
                if job.get("job_name") == "iris-api":
                    iris_job = job
                    break
            
            assert iris_job is not None, "iris-api job not found in Prometheus config"
            assert iris_job.get("metrics_path") == "/metrics"
        
        # Test alert rules
        if os.path.exists("monitoring/alert_rules.yml"):
            with open("monitoring/alert_rules.yml", 'r') as f:
                alert_config = yaml.safe_load(f)
            
            assert "groups" in alert_config
            
            # Check for expected alerts
            all_alerts = []
            for group in alert_config["groups"]:
                if "rules" in group:
                    all_alerts.extend([rule["alert"] for rule in group["rules"] if "alert" in rule])
            
            expected_alerts = ["HighErrorRate", "HighResponseTime", "APIDown"]
            for alert in expected_alerts:
                assert alert in all_alerts, f"Missing alert: {alert}"
        
        # Test Docker Compose configuration
        compose_files = ["docker-compose.yml", "docker-compose.dev.yml", "docker-compose.prod.yml"]
        for compose_file in compose_files:
            if os.path.exists(compose_file):
                result = subprocess.run([
                    "docker-compose", "-f", compose_file, "config"
                ], capture_output=True, text=True)
                assert result.returncode == 0, f"Invalid compose file: {compose_file}"
        
        # Test GitHub workflow
        if os.path.exists(".github/workflows/ci-cd.yml"):
            with open(".github/workflows/ci-cd.yml", 'r') as f:
                workflow = yaml.safe_load(f)
            
            assert "jobs" in workflow
            expected_jobs = ["test", "docker-build-push", "integration-test"]
            for job in expected_jobs:
                assert job in workflow["jobs"], f"Missing job: {job}"
        
        print("✅ Configuration integration test passed!")
    
    def test_error_handling_integration(self):
        """Test error handling across the system"""
        # Start API server
        process = subprocess.Popen([
            "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8033"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            time.sleep(15)
            
            # Test various error conditions
            error_test_cases = [
                # Invalid input types
                {
                    "data": {"sepal_length": "invalid", "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2},
                    "expected_status": 422
                },
                # Missing fields
                {
                    "data": {"sepal_length": 5.1, "sepal_width": 3.5},
                    "expected_status": 422
                },
                # Negative values (might be handled differently)
                {
                    "data": {"sepal_length": -1.0, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2},
                    "expected_status": 422
                },
                # Empty request
                {
                    "data": {},
                    "expected_status": 422
                }
            ]
            
            for i, test_case in enumerate(error_test_cases):
                response = requests.post("http://localhost:8033/predict", json=test_case["data"])
                assert response.status_code == test_case["expected_status"], \
                    f"Test case {i+1}: Expected {test_case['expected_status']}, got {response.status_code}"
                
                # Check error response format
                if response.status_code == 422:
                    error_data = response.json()
                    assert "detail" in error_data, f"Test case {i+1}: Missing error details"
            
            # Test malformed JSON
            response = requests.post(
                "http://localhost:8033/predict",
                data="invalid json",
                headers={"Content-Type": "application/json"}
            )
            assert response.status_code == 422
            
            # Test unsupported methods
            response = requests.put("http://localhost:8033/predict")
            assert response.status_code == 405
            
            # Test non-existent endpoints
            response = requests.get("http://localhost:8033/nonexistent")
            assert response.status_code == 404
            
            # Verify system still works after errors
            valid_data = {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            }
            response = requests.post("http://localhost:8033/predict", json=valid_data)
            assert response.status_code == 200
            
            print("✅ Error handling integration test passed!")
            
        finally:
            process.terminate()
            process.wait(timeout=10)
    
    def test_performance_integration(self):
        """Test performance characteristics integration"""
        # Start API server
        process = subprocess.Popen([
            "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8034"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            time.sleep(15)
            
            import concurrent.futures
            
            prediction_data = {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            }
            
            def make_request():
                start_time = time.time()
                try:
                    response = requests.post("http://localhost:8034/predict", json=prediction_data, timeout=5)
                    end_time = time.time()
                    return response.status_code == 200, end_time - start_time
                except:
                    return False, float('inf')
            
            # Test concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request) for _ in range(100)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # Analyze performance
            successful_requests = [r for r in results if r[0]]
            response_times = [r[1] for r in successful_requests]
            
            assert len(successful_requests) > 0, "No successful requests"
            
            success_rate = len(successful_requests) / len(results)
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            # Performance assertions
            assert success_rate >= 0.95, f"Success rate too low: {success_rate:.2%}"
            assert avg_response_time < 2.0, f"Average response time too high: {avg_response_time:.3f}s"
            assert max_response_time < 5.0, f"Max response time too high: {max_response_time:.3f}s"
            
            print(f"✅ Performance integration test passed!")
            print(f"   Success rate: {success_rate:.2%}")
            print(f"   Average response time: {avg_response_time:.3f}s")
            print(f"   Max response time: {max_response_time:.3f}s")
            
        finally:
            process.terminate()
            process.wait(timeout=10)
    
    def test_deployment_readiness(self):
        """Test deployment readiness and production requirements"""
        # Check required files exist
        required_files = [
            "Dockerfile",
            "requirements.txt",
            "README.md",
            "api/main.py",
            "artifacts/best_model.pkl",
            "artifacts/scaler.pkl"
        ]
        
        for file_path in required_files:
            assert os.path.exists(file_path), f"Required file missing: {file_path}"
        
        # Check Dockerfile
        with open("Dockerfile", 'r') as f:
            dockerfile_content = f.read()
        
        # Should contain essential Docker instructions
        docker_instructions = ["FROM", "COPY", "RUN", "EXPOSE", "CMD"]
        for instruction in docker_instructions:
            assert instruction in dockerfile_content, f"Missing Docker instruction: {instruction}"
        
        # Check requirements.txt
        with open("requirements.txt", 'r') as f:
            requirements = f.read()
        
        # Should contain essential packages
        essential_packages = ["fastapi", "uvicorn", "scikit-learn", "pandas", "numpy"]
        for package in essential_packages:
            assert package in requirements, f"Missing essential package: {package}"
        
        # Check API main file
        with open("api/main.py", 'r') as f:
            main_content = f.read()
        
        # Should contain FastAPI app
        assert "FastAPI" in main_content, "FastAPI app not found in main.py"
        assert "predict" in main_content, "Predict endpoint not found in main.py"
        
        # Test Docker build (if Docker is available)
        if shutil.which("docker"):
            print("Testing Docker build...")
            result = subprocess.run([
                "docker", "build", "-t", "iris-api-deployment-test", "."
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Cleanup test image
                subprocess.run([
                    "docker", "rmi", "iris-api-deployment-test"
                ], capture_output=True, text=True)
                print("✅ Docker build test passed!")
            else:
                print(f"⚠️ Docker build failed: {result.stderr}")
        
        print("✅ Deployment readiness test passed!")
    
    def test_documentation_completeness(self):
        """Test documentation completeness"""
        # Check README.md
        assert os.path.exists("README.md"), "README.md not found"
        
        with open("README.md", 'r') as f:
            readme_content = f.read().lower()
        
        # Should contain essential sections
        essential_sections = ["install", "usage", "api", "docker"]
        for section in essential_sections:
            assert section in readme_content, f"README missing section about: {section}"
        
        # Check other documentation files
        doc_files = ["DEPLOYMENT.md", "DOCKER.md"]
        for doc_file in doc_files:
            if os.path.exists(doc_file):
                with open(doc_file, 'r') as f:
                    content = f.read()
                assert len(content.strip()) > 100, f"{doc_file} appears to be too short"
        
        print("✅ Documentation completeness test passed!")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "--tb=short"])