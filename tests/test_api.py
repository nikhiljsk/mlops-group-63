"""Basic tests for the FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from api.main import app


def test_root_endpoint():
    """Test the root endpoint"""
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Iris Classification API"


@patch('api.main.prediction_service')
@patch('api.main.logging_service')
def test_health_endpoint(mock_logging_service, mock_prediction_service):
    """Test health endpoint"""
    mock_prediction_service.is_model_loaded.return_value = True
    mock_logging_service.is_healthy.return_value = True
    
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


@patch('api.main.prediction_service')
@patch('api.main.logging_service')
@patch('api.main.metrics_collector')
def test_predict_endpoint(mock_metrics, mock_logging_service, mock_prediction_service):
    """Test prediction endpoint"""
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


def test_predict_invalid_input():
    """Test prediction with invalid input"""
    with TestClient(app) as client:
        response = client.post("/predict", json={
            "sepal_length": -1.0,  # Invalid
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2
        })
        assert response.status_code == 422