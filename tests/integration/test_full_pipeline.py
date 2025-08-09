"""Full pipeline integration tests"""
import pytest
import requests
import time
import subprocess
import os

class TestFullPipeline:
    """Test complete ML pipeline integration"""
    
    @pytest.fixture(scope="class")
    def api_server(self):
        """Start API server for testing"""
        # This assumes the server is already running
        yield "http://localhost:8000"
    
    def test_complete_prediction_workflow(self, api_server):
        """Test complete prediction workflow"""
        try:
            # Test health
            response = requests.get(f"{api_server}/health", timeout=10)
            assert response.status_code == 200
            
            # Test model info
            response = requests.get(f"{api_server}/model/info", timeout=10)
            assert response.status_code == 200
            
            # Test prediction
            data = {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}
            response = requests.post(f"{api_server}/predict", json=data, timeout=10)
            assert response.status_code == 200
            result = response.json()
            assert "prediction" in result
            assert "confidence" in result
            
            # Test batch prediction
            batch_data = {"samples": [data, data]}
            response = requests.post(f"{api_server}/predict/batch", json=batch_data, timeout=10)
            assert response.status_code == 200
            result = response.json()
            assert "predictions" in result
            assert len(result["predictions"]) == 2
            
        except requests.exceptions.RequestException:
            pytest.skip("API server not available")
    
    def test_error_handling(self, api_server):
        """Test API error handling"""
        try:
            # Test invalid input
            data = {"sepal_length": -1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}
            response = requests.post(f"{api_server}/predict", json=data, timeout=10)
            assert response.status_code == 422
            
        except requests.exceptions.RequestException:
            pytest.skip("API server not available")