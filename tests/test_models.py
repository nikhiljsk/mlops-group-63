"""
Unit tests for Pydantic models.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from api.models import (
    PredictionRequest, PredictionResponse, BatchPredictionRequest,
    BatchPredictionResponse, HealthResponse, ModelInfoResponse
)


class TestPredictionRequest:
    """Test PredictionRequest model"""
    
    def test_valid_prediction_request(self):
        """Test valid prediction request"""
        request = PredictionRequest(
            sepal_length=5.1,
            sepal_width=3.5,
            petal_length=1.4,
            petal_width=0.2
        )
        assert request.sepal_length == 5.1
        assert request.sepal_width == 3.5
        assert request.petal_length == 1.4
        assert request.petal_width == 0.2
    
    def test_negative_values_rejected(self):
        """Test that negative values are rejected"""
        with pytest.raises(ValidationError):
            PredictionRequest(
                sepal_length=-1.0,
                sepal_width=3.5,
                petal_length=1.4,
                petal_width=0.2
            )
    
    def test_too_large_values_rejected(self):
        """Test that unreasonably large values are rejected"""
        with pytest.raises(ValidationError):
            PredictionRequest(
                sepal_length=20.0,  # Too large
                sepal_width=3.5,
                petal_length=1.4,
                petal_width=0.2
            )
    
    def test_missing_fields_rejected(self):
        """Test that missing required fields are rejected"""
        with pytest.raises(ValidationError):
            PredictionRequest(
                sepal_length=5.1,
                sepal_width=3.5,
                # Missing petal_length and petal_width
            )
    
    def test_to_array_conversion(self):
        """Test conversion to numpy array"""
        request = PredictionRequest(
            sepal_length=5.1,
            sepal_width=3.5,
            petal_length=1.4,
            petal_width=0.2
        )
        array = request.to_array()
        assert array.shape == (1, 4)
        assert array[0, 0] == 5.1
        assert array[0, 1] == 3.5
        assert array[0, 2] == 1.4
        assert array[0, 3] == 0.2


class TestPredictionResponse:
    """Test PredictionResponse model"""
    
    def test_valid_prediction_response(self):
        """Test valid prediction response"""
        response = PredictionResponse(
            prediction="setosa",
            confidence=0.99,
            probabilities={"setosa": 0.99, "versicolor": 0.01, "virginica": 0.00},
            model_version="1.0.0"
        )
        assert response.prediction == "setosa"
        assert response.confidence == 0.99
        assert response.model_version == "1.0.0"
        assert isinstance(response.timestamp, datetime)
    
    def test_confidence_out_of_range_rejected(self):
        """Test that confidence values outside [0,1] are rejected"""
        with pytest.raises(ValidationError):
            PredictionResponse(
                prediction="setosa",
                confidence=1.5,  # Invalid confidence > 1
                probabilities={"setosa": 0.99, "versicolor": 0.01, "virginica": 0.00},
                model_version="1.0.0"
            )


class TestBatchPredictionRequest:
    """Test BatchPredictionRequest model"""
    
    def test_valid_batch_request(self):
        """Test valid batch prediction request"""
        request = BatchPredictionRequest(
            samples=[
                PredictionRequest(
                    sepal_length=5.1,
                    sepal_width=3.5,
                    petal_length=1.4,
                    petal_width=0.2
                ),
                PredictionRequest(
                    sepal_length=6.2,
                    sepal_width=2.9,
                    petal_length=4.3,
                    petal_width=1.3
                )
            ]
        )
        assert len(request.samples) == 2
        assert request.samples[0].sepal_length == 5.1
        assert request.samples[1].sepal_length == 6.2
    
    def test_empty_batch_rejected(self):
        """Test that empty batch is rejected"""
        with pytest.raises(ValidationError):
            BatchPredictionRequest(samples=[])
    
    def test_too_large_batch_rejected(self):
        """Test that batch size > 100 is rejected"""
        large_batch = [
            PredictionRequest(
                sepal_length=5.1,
                sepal_width=3.5,
                petal_length=1.4,
                petal_width=0.2
            )
        ] * 101  # 101 samples
        
        with pytest.raises(ValidationError):
            BatchPredictionRequest(samples=large_batch)


class TestHealthResponse:
    """Test HealthResponse model"""
    
    def test_valid_health_response(self):
        """Test valid health response"""
        response = HealthResponse(
            status="healthy",
            uptime_seconds=3600.5,
            version="1.0.0",
            model_loaded=True,
            database_connected=True
        )
        assert response.status == "healthy"
        assert response.uptime_seconds == 3600.5
        assert response.model_loaded is True
        assert response.database_connected is True
        assert isinstance(response.timestamp, datetime)


class TestModelInfoResponse:
    """Test ModelInfoResponse model"""
    
    def test_valid_model_info_response(self):
        """Test valid model info response"""
        response = ModelInfoResponse(
            model_name="iris-classifier",
            model_version="1.0.0",
            model_type="LogisticRegression",
            features=["sepal_length", "sepal_width", "petal_length", "petal_width"],
            classes=["setosa", "versicolor", "virginica"]
        )
        assert response.model_name == "iris-classifier"
        assert response.model_version == "1.0.0"
        assert response.model_type == "LogisticRegression"
        assert len(response.features) == 4
        assert len(response.classes) == 3