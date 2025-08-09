"""
Integration tests for the complete API functionality.
"""

import pytest
import requests
import time
import subprocess
import os
import signal
from multiprocessing import Process


class TestAPIIntegration:
    """Integration tests for the complete API"""
    
    @pytest.fixture(scope="class")
    def api_server(self):
        """Start API server for integration testing"""
        # This would be used in a real integration test environment
        # For CI/CD, the server is started separately
        yield "http://localhost:8000"
    
    def test_health_endpoint_integration(self, api_server):
        """Test health endpoint integration"""
        try:
            response = requests.get(f"{api_server}/health", timeout=10)
            assert response.status_code == 200
            
            data = response.json()
            assert "status" in data
            assert "timestamp" in data
            assert "uptime_seconds" in data
            assert "version" in data
            assert "model_loaded" in data
            assert "database_connected" in data
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"API server not available: {e}")
    
    def test_prediction_endpoint_integration(self, api_server):
        """Test prediction endpoint integration"""
        try:
            prediction_data = {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            }
            
            response = requests.post(
                f"{api_server}/predict", 
                json=prediction_data,
                timeout=10
            )
            assert response.status_code == 200
            
            data = response.json()
            assert "prediction" in data
            assert "confidence" in data
            assert "probabilities" in data
            assert "model_version" in data
            assert "timestamp" in data
            
            # Validate prediction is one of the expected classes
            assert data["prediction"] in ["setosa", "versicolor", "virginica"]
            
            # Validate confidence is between 0 and 1
            assert 0.0 <= data["confidence"] <= 1.0
            
            # Validate probabilities sum to approximately 1
            prob_sum = sum(data["probabilities"].values())
            assert abs(prob_sum - 1.0) < 0.01
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"API server not available: {e}")
    
    def test_batch_prediction_endpoint_integration(self, api_server):
        """Test batch prediction endpoint integration"""
        try:
            batch_data = {
                "samples": [
                    {
                        "sepal_length": 5.1,
                        "sepal_width": 3.5,
                        "petal_length": 1.4,
                        "petal_width": 0.2
                    },
                    {
                        "sepal_length": 6.2,
                        "sepal_width": 2.9,
                        "petal_length": 4.3,
                        "petal_width": 1.3
                    }
                ]
            }
            
            response = requests.post(
                f"{api_server}/predict/batch", 
                json=batch_data,
                timeout=10
            )
            assert response.status_code == 200
            
            data = response.json()
            assert "predictions" in data
            assert "batch_size" in data
            assert "total_processing_time_ms" in data
            
            assert data["batch_size"] == 2
            assert len(data["predictions"]) == 2
            
            # Validate each prediction
            for prediction in data["predictions"]:
                assert "prediction" in prediction
                assert "confidence" in prediction
                assert "probabilities" in prediction
                assert prediction["prediction"] in ["setosa", "versicolor", "virginica"]
                assert 0.0 <= prediction["confidence"] <= 1.0
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"API server not available: {e}")
    
    def test_model_info_endpoint_integration(self, api_server):
        """Test model info endpoint integration"""
        try:
            response = requests.get(f"{api_server}/model/info", timeout=10)
            assert response.status_code == 200
            
            data = response.json()
            assert "model_name" in data
            assert "model_version" in data
            assert "model_type" in data
            assert "features" in data
            assert "classes" in data
            
            # Validate expected features and classes
            expected_features = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
            expected_classes = ["setosa", "versicolor", "virginica"]
            
            assert len(data["features"]) == 4
            assert len(data["classes"]) == 3
            
            for feature in expected_features:
                assert feature in data["features"]
            
            for cls in expected_classes:
                assert cls in data["classes"]
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"API server not available: {e}")
    
    def test_metrics_endpoint_integration(self, api_server):
        """Test metrics endpoint integration"""
        try:
            response = requests.get(f"{api_server}/metrics", timeout=10)
            assert response.status_code == 200
            
            # Should return Prometheus format
            content_type = response.headers.get("content-type", "")
            assert "text/plain" in content_type
            
            # Should contain some basic metrics
            metrics_text = response.text
            assert "# HELP" in metrics_text
            assert "# TYPE" in metrics_text
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"API server not available: {e}")
    
    def test_invalid_prediction_input_integration(self, api_server):
        """Test API error handling with invalid input"""
        try:
            # Test with negative values
            invalid_data = {
                "sepal_length": -1.0,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            }
            
            response = requests.post(
                f"{api_server}/predict", 
                json=invalid_data,
                timeout=10
            )
            assert response.status_code == 422  # Validation error
            
            # Test with missing fields
            incomplete_data = {
                "sepal_length": 5.1,
                "sepal_width": 3.5
                # Missing petal_length and petal_width
            }
            
            response = requests.post(
                f"{api_server}/predict", 
                json=incomplete_data,
                timeout=10
            )
            assert response.status_code == 422  # Validation error
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"API server not available: {e}")
    
    def test_api_performance_integration(self, api_server):
        """Test API performance characteristics"""
        try:
            prediction_data = {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            }
            
            # Test response time
            start_time = time.time()
            response = requests.post(
                f"{api_server}/predict", 
                json=prediction_data,
                timeout=10
            )
            end_time = time.time()
            
            assert response.status_code == 200
            
            # Response should be reasonably fast (less than 1 second)
            response_time = end_time - start_time
            assert response_time < 1.0
            
            # Test multiple concurrent requests
            import concurrent.futures
            
            def make_request():
                return requests.post(
                    f"{api_server}/predict", 
                    json=prediction_data,
                    timeout=10
                )
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request) for _ in range(5)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # All requests should succeed
            for result in results:
                assert result.status_code == 200
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"API server not available: {e}")
    
    def test_root_endpoint_integration(self, api_server):
        """Test root endpoint integration"""
        try:
            response = requests.get(f"{api_server}/", timeout=10)
            assert response.status_code == 200
            
            data = response.json()
            assert data["message"] == "Iris Classification API"
            assert data["version"] == "1.0.0"
            assert data["status"] == "running"
            assert data["docs"] == "/docs"
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"API server not available: {e}")