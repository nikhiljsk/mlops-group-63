"""
Comprehensive End-to-End System Tests
Tests the complete MLOps pipeline from training to prediction, CI/CD, and monitoring.
"""

import pytest
import requests
import time
import subprocess
import os
import json
import docker
import tempfile
import shutil
from pathlib import Path
import sqlite3
import yaml
import concurrent.futures
from unittest.mock import patch, MagicMock


class TestCompleteMLOpsPipeline:
    """Test complete MLOps pipeline functionality"""
    
    @pytest.fixture(scope="class")
    def docker_client(self):
        """Docker client for container management"""
        return docker.from_env()
    
    @pytest.fixture(scope="class")
    def temp_workspace(self):
        """Create temporary workspace for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_training_pipeline_integration(self, temp_workspace):
        """Test complete training pipeline from data to model registry"""
        # Test data preprocessing
        result = subprocess.run([
            "python", "src/preprocess.py"
        ], capture_output=True, text=True, cwd=".")
        
        assert result.returncode == 0, f"Preprocessing failed: {result.stderr}"
        
        # Test model training
        result = subprocess.run([
            "python", "src/train.py"
        ], capture_output=True, text=True, cwd=".")
        
        assert result.returncode == 0, f"Training failed: {result.stderr}"
        
        # Verify artifacts are created
        assert os.path.exists("artifacts/best_model.pkl"), "Model artifact not created"
        assert os.path.exists("artifacts/scaler.pkl"), "Scaler artifact not created"
        
        # Test model evaluation
        result = subprocess.run([
            "python", "src/model_evaluation.py"
        ], capture_output=True, text=True, cwd=".")
        
        assert result.returncode == 0, f"Model evaluation failed: {result.stderr}"
    
    def test_api_server_lifecycle(self):
        """Test complete API server lifecycle"""
        # Start API server
        process = subprocess.Popen([
            "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8001"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            # Wait for server to start
            time.sleep(15)
            
            # Test server is running
            response = requests.get("http://localhost:8001/health", timeout=10)
            assert response.status_code == 200
            
            health_data = response.json()
            assert health_data["status"] in ["healthy", "degraded"]
            assert "uptime_seconds" in health_data
            assert "model_loaded" in health_data
            assert "database_connected" in health_data
            
            # Test all API endpoints
            self._test_all_api_endpoints("http://localhost:8001")
            
        finally:
            # Clean shutdown
            process.terminate()
            process.wait(timeout=10)
    
    def _test_all_api_endpoints(self, base_url):
        """Test all API endpoints comprehensively"""
        # Test root endpoint
        response = requests.get(f"{base_url}/")
        assert response.status_code == 200
        root_data = response.json()
        assert root_data["message"] == "Iris Classification API"
        
        # Test health endpoint
        response = requests.get(f"{base_url}/health")
        assert response.status_code == 200
        health_data = response.json()
        assert "status" in health_data
        assert "timestamp" in health_data
        
        # Test model info endpoint
        response = requests.get(f"{base_url}/model/info")
        assert response.status_code == 200
        model_data = response.json()
        assert "model_name" in model_data
        assert "features" in model_data
        assert len(model_data["features"]) == 4
        
        # Test prediction endpoint
        prediction_data = {
            "sepal_length": 5.1,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2
        }
        response = requests.post(f"{base_url}/predict", json=prediction_data)
        assert response.status_code == 200
        pred_result = response.json()
        assert "prediction" in pred_result
        assert "confidence" in pred_result
        assert "probabilities" in pred_result
        assert pred_result["prediction"] in ["setosa", "versicolor", "virginica"]
        
        # Test batch prediction endpoint
        batch_data = {
            "samples": [prediction_data, prediction_data]
        }
        response = requests.post(f"{base_url}/predict/batch", json=batch_data)
        assert response.status_code == 200
        batch_result = response.json()
        assert "predictions" in batch_result
        assert len(batch_result["predictions"]) == 2
        
        # Test metrics endpoint
        response = requests.get(f"{base_url}/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")
        metrics_text = response.text
        assert "# HELP" in metrics_text
        assert "# TYPE" in metrics_text
        
        # Test retraining status endpoint
        response = requests.get(f"{base_url}/retrain/status")
        assert response.status_code == 200
        retrain_data = response.json()
        # The actual response has different structure - check for key fields
        assert "last_training" in retrain_data
        assert "needs_retraining" in retrain_data
        assert "current_model" in retrain_data
        
        # Test error handling
        invalid_data = {"sepal_length": -1.0}
        response = requests.post(f"{base_url}/predict", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_docker_containerization(self, docker_client):
        """Test Docker containerization and deployment"""
        # Build Docker image
        image_tag = "iris-api-e2e-test"
        
        try:
            # Build image
            image, build_logs = docker_client.images.build(
                path=".",
                tag=image_tag,
                rm=True,
                forcerm=True
            )
            
            # Verify image was built
            assert image is not None
            assert image_tag in [tag for tag in image.tags]
            
            # Start container
            container = docker_client.containers.run(
                image_tag,
                ports={'8000/tcp': 8002},
                detach=True,
                name="iris-api-e2e-container"
            )
            
            try:
                # Wait for container to be ready
                time.sleep(30)
                
                # Test container health
                response = requests.get("http://localhost:8002/health", timeout=10)
                assert response.status_code == 200
                
                # Test container functionality
                self._test_all_api_endpoints("http://localhost:8002")
                
                # Test container logs
                logs = container.logs().decode('utf-8')
                assert "Application startup complete" in logs or "Started server process" in logs
                
            finally:
                # Cleanup container
                container.stop()
                container.remove()
                
        finally:
            # Cleanup image
            try:
                docker_client.images.remove(image_tag, force=True)
            except:
                pass
    
    def test_docker_compose_stack(self):
        """Test Docker Compose stack functionality"""
        # Start Docker Compose stack
        result = subprocess.run([
            "docker-compose", "up", "-d"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Docker Compose up failed: {result.stderr}"
        
        try:
            # Wait for services to be ready
            time.sleep(60)
            
            # Test API service
            response = requests.get("http://localhost:8000/health", timeout=15)
            assert response.status_code == 200
            
            # Test MLflow service (if configured)
            try:
                response = requests.get("http://localhost:5000/health", timeout=10)
                # MLflow might not have a health endpoint, so check for any response
                assert response.status_code in [200, 404]
            except requests.exceptions.RequestException:
                # MLflow service might not be configured in compose
                pass
            
            # Test complete workflow through compose
            self._test_all_api_endpoints("http://localhost:8000")
            
        finally:
            # Cleanup Docker Compose stack
            subprocess.run([
                "docker-compose", "down", "-v"
            ], capture_output=True, text=True)
    
    def test_database_integration(self):
        """Test database logging and persistence"""
        # Start API server for database testing
        process = subprocess.Popen([
            "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8003"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            time.sleep(15)
            
            # Make several predictions to generate logs
            prediction_data = {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            }
            
            for _ in range(5):
                response = requests.post("http://localhost:8003/predict", json=prediction_data)
                assert response.status_code == 200
                time.sleep(1)
            
            # Check database logs
            if os.path.exists("logs.db"):
                conn = sqlite3.connect("logs.db")
                cursor = conn.cursor()
                
                # Check prediction logs table exists
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='prediction_logs'
                """)
                assert cursor.fetchone() is not None
                
                # Check logs were created
                cursor.execute("SELECT COUNT(*) FROM prediction_logs")
                log_count = cursor.fetchone()[0]
                assert log_count >= 5
                
                # Check log structure
                cursor.execute("SELECT * FROM prediction_logs LIMIT 1")
                columns = [description[0] for description in cursor.description]
                expected_columns = ["id", "timestamp", "request_data", "prediction", "probabilities"]
                for col in expected_columns:
                    assert col in columns
                
                conn.close()
            
        finally:
            process.terminate()
            process.wait(timeout=10)
    
    def test_monitoring_and_metrics(self):
        """Test monitoring and metrics collection"""
        # Start API server
        process = subprocess.Popen([
            "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8004"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            time.sleep(15)
            
            # Make requests to generate metrics
            prediction_data = {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            }
            
            # Generate various types of requests
            for _ in range(10):
                requests.post("http://localhost:8004/predict", json=prediction_data)
                requests.get("http://localhost:8004/health")
                time.sleep(0.5)
            
            # Test metrics endpoint
            response = requests.get("http://localhost:8004/metrics")
            assert response.status_code == 200
            
            metrics_text = response.text
            
            # Check for expected Prometheus metrics
            expected_metrics = [
                "# HELP",
                "# TYPE",
                "http_requests_total",
                "http_request_duration_seconds",
                "ml_predictions_total",
                "python_info"
            ]
            
            for metric in expected_metrics:
                assert metric in metrics_text, f"Missing metric: {metric}"
            
            # Test metrics format
            lines = metrics_text.split('\n')
            help_lines = [line for line in lines if line.startswith('# HELP')]
            type_lines = [line for line in lines if line.startswith('# TYPE')]
            
            assert len(help_lines) > 0, "No HELP lines found in metrics"
            assert len(type_lines) > 0, "No TYPE lines found in metrics"
            
        finally:
            process.terminate()
            process.wait(timeout=10)
    
    def test_configuration_validation(self):
        """Test configuration files and validation"""
        # Test Docker Compose configuration
        result = subprocess.run([
            "docker-compose", "config"
        ], capture_output=True, text=True)
        assert result.returncode == 0, f"Docker Compose config invalid: {result.stderr}"
        
        # Test Prometheus configuration
        if os.path.exists("monitoring/prometheus.yml"):
            with open("monitoring/prometheus.yml", 'r') as f:
                prometheus_config = yaml.safe_load(f)
            
            assert "global" in prometheus_config
            assert "scrape_configs" in prometheus_config
            assert len(prometheus_config["scrape_configs"]) > 0
            
            # Check for iris-api job
            iris_job = None
            for job in prometheus_config["scrape_configs"]:
                if job["job_name"] == "iris-api":
                    iris_job = job
                    break
            
            assert iris_job is not None, "iris-api job not found in Prometheus config"
            assert "static_configs" in iris_job
        
        # Test alert rules
        if os.path.exists("monitoring/alert_rules.yml"):
            with open("monitoring/alert_rules.yml", 'r') as f:
                alert_config = yaml.safe_load(f)
            
            assert "groups" in alert_config
            assert len(alert_config["groups"]) > 0
            
            # Check for expected alerts
            alerts = []
            for group in alert_config["groups"]:
                if "rules" in group:
                    alerts.extend([rule["alert"] for rule in group["rules"] if "alert" in rule])
            
            expected_alerts = ["HighErrorRate", "HighResponseTime", "APIDown"]
            for alert in expected_alerts:
                assert alert in alerts, f"Missing alert: {alert}"
    
    def test_performance_and_load(self):
        """Test system performance under load"""
        # Start API server
        process = subprocess.Popen([
            "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8005"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            time.sleep(15)
            
            prediction_data = {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            }
            
            def make_request():
                start_time = time.time()
                response = requests.post("http://localhost:8005/predict", json=prediction_data)
                end_time = time.time()
                return response.status_code, end_time - start_time
            
            # Test concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request) for _ in range(50)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # Analyze results
            successful_requests = [r for r in results if r[0] == 200]
            response_times = [r[1] for r in successful_requests]
            
            # Performance assertions
            success_rate = len(successful_requests) / len(results)
            assert success_rate >= 0.95, f"Success rate too low: {success_rate}"
            
            avg_response_time = sum(response_times) / len(response_times)
            assert avg_response_time < 2.0, f"Average response time too high: {avg_response_time}"
            
            max_response_time = max(response_times)
            assert max_response_time < 5.0, f"Max response time too high: {max_response_time}"
            
        finally:
            process.terminate()
            process.wait(timeout=10)
    
    def test_error_handling_and_recovery(self):
        """Test error handling and system recovery"""
        # Start API server
        process = subprocess.Popen([
            "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8006"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            time.sleep(15)
            
            # Test various error conditions
            
            # 1. Invalid input validation
            invalid_inputs = [
                {"sepal_length": -1.0, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2},
                {"sepal_length": "invalid", "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2},
                {"sepal_length": 5.1},  # Missing fields
                {},  # Empty request
                {"extra_field": 1.0, "sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}
            ]
            
            for invalid_input in invalid_inputs:
                response = requests.post("http://localhost:8006/predict", json=invalid_input)
                assert response.status_code == 422, f"Expected 422 for input: {invalid_input}"
                
                error_data = response.json()
                assert "detail" in error_data
            
            # 2. Test malformed JSON
            response = requests.post(
                "http://localhost:8006/predict",
                data="invalid json",
                headers={"Content-Type": "application/json"}
            )
            assert response.status_code == 422
            
            # 3. Test unsupported methods
            response = requests.put("http://localhost:8006/predict")
            assert response.status_code == 405  # Method not allowed
            
            # 4. Test non-existent endpoints
            response = requests.get("http://localhost:8006/nonexistent")
            assert response.status_code == 404
            
            # 5. Verify system still works after errors
            valid_data = {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            }
            response = requests.post("http://localhost:8006/predict", json=valid_data)
            assert response.status_code == 200
            
        finally:
            process.terminate()
            process.wait(timeout=10)
    
    def test_deployment_scripts(self):
        """Test deployment and utility scripts"""
        # Test script syntax
        scripts_to_test = [
            "deploy.sh",
            "demo.sh",
            "scripts/test-local.sh",
            "scripts/e2e-test.sh",
            "scripts/rollback.sh"
        ]
        
        for script in scripts_to_test:
            if os.path.exists(script):
                result = subprocess.run([
                    "bash", "-n", script
                ], capture_output=True, text=True)
                assert result.returncode == 0, f"Script {script} has syntax errors: {result.stderr}"
    
    def test_ci_cd_workflow_validation(self):
        """Test CI/CD workflow configuration"""
        workflow_file = ".github/workflows/ci-cd.yml"
        
        if os.path.exists(workflow_file):
            with open(workflow_file, 'r') as f:
                workflow_config = yaml.safe_load(f)
            
            # Validate workflow structure
            assert "name" in workflow_config
            assert "on" in workflow_config
            assert "jobs" in workflow_config
            
            # Check for expected jobs
            expected_jobs = ["test", "docker-build-push", "integration-test"]
            for job in expected_jobs:
                assert job in workflow_config["jobs"], f"Missing job: {job}"
            
            # Validate job dependencies
            if "docker-build-push" in workflow_config["jobs"]:
                docker_job = workflow_config["jobs"]["docker-build-push"]
                assert "needs" in docker_job
                assert "test" in docker_job["needs"]
            
            if "integration-test" in workflow_config["jobs"]:
                integration_job = workflow_config["jobs"]["integration-test"]
                assert "needs" in integration_job
                assert "docker-build-push" in integration_job["needs"]
    
    def test_model_retraining_workflow(self):
        """Test model retraining trigger and workflow"""
        # Start API server
        process = subprocess.Popen([
            "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8007"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            time.sleep(15)
            
            # Test retraining status endpoint
            response = requests.get("http://localhost:8007/retrain/status")
            assert response.status_code == 200
            
            status_data = response.json()
            assert "last_training" in status_data
            assert "needs_retraining" in status_data
            assert "current_model" in status_data
            
            # Test retraining trigger (if implemented)
            response = requests.post("http://localhost:8007/retrain/trigger")
            # This might return 501 (Not Implemented) or 202 (Accepted)
            assert response.status_code in [202, 501]
            
        finally:
            process.terminate()
            process.wait(timeout=10)
    
    def test_security_and_validation(self):
        """Test security measures and input validation"""
        # Start API server
        process = subprocess.Popen([
            "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8008"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            time.sleep(15)
            
            # Test SQL injection attempts (should be handled by Pydantic)
            malicious_inputs = [
                {"sepal_length": "'; DROP TABLE prediction_logs; --", "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2},
                {"sepal_length": "<script>alert('xss')</script>", "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}
            ]
            
            for malicious_input in malicious_inputs:
                response = requests.post("http://localhost:8008/predict", json=malicious_input)
                assert response.status_code == 422  # Should be rejected by validation
            
            # Test extremely large values
            extreme_input = {
                "sepal_length": 999999.0,
                "sepal_width": 999999.0,
                "petal_length": 999999.0,
                "petal_width": 999999.0
            }
            response = requests.post("http://localhost:8008/predict", json=extreme_input)
            # Should either be rejected by validation or handled gracefully
            assert response.status_code in [200, 422]
            
            # Test request size limits (if implemented)
            large_batch = {
                "samples": [
                    {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}
                ] * 1000  # Very large batch
            }
            response = requests.post("http://localhost:8008/predict/batch", json=large_batch)
            # Should handle large requests appropriately
            assert response.status_code in [200, 413, 422]
            
        finally:
            process.terminate()
            process.wait(timeout=10)


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "--tb=short"])