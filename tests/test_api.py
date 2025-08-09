"""
Unit tests for the FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from api.main import app


class TestAPIEndpoints:
    """Test class for API endpoints"""
    
    def test_root_endpoint(self):
        """Test the root endpoint"""
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Iris Classification API"
            assert data["version"] == "1.0.0"
            assert data["status"] == "running"
    
    @patch('api.main.prediction_service')
    @patch('api.main.logging_service')
    def test_health_endpoint_healthy(self, mock_logging_service, mock_prediction_service):
        """Test health endpoint when services are healthy"""
        # Mock services as healthy
        mock_prediction_service.is_model_loaded.return_value = True
        mock_logging_service.is_healthy.return_value = True
        
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["model_loaded"] is True
            assert data["database_connected"] is True
    
    @patch('api.main.prediction_service')
    @patch('api.main.logging_service')
    def test_health_endpoint_degraded(self, mock_logging_service, mock_prediction_service):
        """Test health endpoint when model is not loaded"""
        # Mock model as not loaded
        mock_prediction_service.is_model_loaded.return_value = False
        mock_logging_service.is_healthy.return_value = True
        
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["model_loaded"] is False
            assert "issues" in data
    
    @patch('api.main.prediction_service')
    def test_predict_endpoint_model_not_loaded(self, mock_prediction_service):
        """Test prediction endpoint when model is not loaded"""
        mock_prediction_service.is_model_loaded.return_value = False
        
        with TestClient(app) as client:
            response = client.post("/predict", json={
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            })
            assert response.status_code == 503
            assert "Model not available" in response.json()["detail"]
    
    @patch('api.main.prediction_service')
    @patch('api.main.logging_service')
    @patch('api.main.metrics_collector')
    def test_predict_endpoint_success(self, mock_metrics, mock_logging_service, mock_prediction_service):
        """Test successful prediction"""
        # Mock successful prediction
        mock_prediction_service.is_model_loaded.return_value = True
        mock_prediction_service.predict.return_value = {
            "prediction": "setosa",
            "confidence": 0.99,
            "probabilities": {"setosa": 0.99, "versicolor": 0.01, "virginica": 0.00},
            "model_version": "test-1.0.0",
            "processing_time_ms": 10.5,
            "timestamp": "2024-01-15T10:30:00"
        }
        
        with TestClient(app) as client:
            response = client.post("/predict", json={
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            })
            assert response.status_code == 200
            data = response.json()
            assert data["prediction"] == "setosa"
            assert data["confidence"] == 0.99
            assert "probabilities" in data
    
    def test_predict_endpoint_invalid_input(self):
        """Test prediction endpoint with invalid input"""
        with TestClient(app) as client:
            response = client.post("/predict", json={
                "sepal_length": -1.0,  # Invalid negative value
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            })
            assert response.status_code == 422  # Validation error
    
    def test_predict_endpoint_missing_fields(self):
        """Test prediction endpoint with missing fields"""
        with TestClient(app) as client:
            response = client.post("/predict", json={
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                # Missing petal_length and petal_width
            })
            assert response.status_code == 422  # Validation error
    
    @patch('api.main.prediction_service')
    def test_model_info_endpoint_model_not_loaded(self, mock_prediction_service):
        """Test model info endpoint when model is not loaded"""
        mock_prediction_service.is_model_loaded.return_value = False
        
        with TestClient(app) as client:
            response = client.get("/model/info")
            assert response.status_code == 503
    
    @patch('api.main.prediction_service')
    def test_model_info_endpoint_success(self, mock_prediction_service):
        """Test successful model info retrieval"""
        mock_prediction_service.is_model_loaded.return_value = True
        mock_prediction_service.get_model_info.return_value = {
            "model_name": "iris-classifier",
            "model_version": "test-1.0.0",
            "model_type": "LogisticRegression",
            "load_timestamp": "2024-01-15T09:00:00",
            "features": ["sepal_length", "sepal_width", "petal_length", "petal_width"],
            "classes": ["setosa", "versicolor", "virginica"]
        }
        
        with TestClient(app) as client:
            response = client.get("/model/info")
            assert response.status_code == 200
            data = response.json()
            assert data["model_name"] == "iris-classifier"
            assert data["model_type"] == "LogisticRegression"
            assert len(data["features"]) == 4
            assert len(data["classes"]) == 3
    
    @patch('api.main.metrics_collector')
    def test_metrics_endpoint(self, mock_metrics_collector):
        """Test metrics endpoint"""
        mock_metrics_collector.get_metrics.return_value = "# HELP test_metric Test metric\n# TYPE test_metric counter\ntest_metric 1.0\n"
        mock_metrics_collector.get_content_type.return_value = "text/plain; version=0.0.4; charset=utf-8"
        
        with TestClient(app) as client:
            response = client.get("/metrics")
            assert response.status_code == 200
            assert "test_metric" in response.text
    
    @patch('api.main.prediction_service')
    @patch('api.main.logging_service')
    @patch('api.main.metrics_collector')
    def test_batch_predict_endpoint_success(self, mock_metrics, mock_logging_service, mock_prediction_service):
        """Test successful batch prediction"""
        mock_prediction_service.is_model_loaded.return_value = True
        mock_prediction_service.predict_batch.return_value = {
            "predictions": [
                {
                    "prediction": "setosa",
                    "confidence": 0.99,
                    "probabilities": {"setosa": 0.99, "versicolor": 0.01, "virginica": 0.00},
                    "model_version": "test-1.0.0",
                    "timestamp": "2024-01-15T10:30:00"
                },
                {
                    "prediction": "versicolor",
                    "confidence": 0.85,
                    "probabilities": {"setosa": 0.05, "versicolor": 0.85, "virginica": 0.10},
                    "model_version": "test-1.0.0",
                    "timestamp": "2024-01-15T10:30:01"
                }
            ],
            "batch_size": 2,
            "total_processing_time_ms": 25.3
        }
        
        with TestClient(app) as client:
            response = client.post("/predict/batch", json={
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
            })
            assert response.status_code == 200
            data = response.json()
            assert data["batch_size"] == 2
            assert len(data["predictions"]) == 2
            assert data["predictions"][0]["prediction"] == "setosa"
            assert data["predictions"][1]["prediction"] == "versicolor"