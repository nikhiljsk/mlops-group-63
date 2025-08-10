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


@patch('api.main.prediction_service')
@patch('api.main.logging_service')
@patch('api.main.metrics_collector')
@patch('subprocess.run')
def test_retrain_endpoint(mock_subprocess, mock_metrics, mock_logging_service, mock_prediction_service):
    """Test retrain endpoint"""
    # Mock successful training
    mock_subprocess.return_value.returncode = 0
    mock_subprocess.return_value.stderr = ""
    
    mock_prediction_service.load_model.return_value = None
    mock_prediction_service.get_model_info.return_value = {
        "model_name": "iris-classifier",
        "model_type": "LogisticRegression",
        "model_version": "retrained-1.0.0"
    }
    
    with TestClient(app) as client:
        response = client.post("/retrain")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "timestamp" in data