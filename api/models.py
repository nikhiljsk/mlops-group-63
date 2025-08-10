"""
Pydantic models for request/response validation in the Iris Classification API.
These models ensure type safety and provide automatic validation for API endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
from pydantic import BaseModel, Field, field_validator


class PredictionRequest(BaseModel):
    """
    Request model for iris flower prediction.
    Validates input features with appropriate ranges based on the Iris dataset.
    """

    sepal_length: float = Field(
        ..., ge=0.0, le=10.0, description="Sepal length in centimeters (0-10 cm range)"
    )
    sepal_width: float = Field(
        ..., ge=0.0, le=10.0, description="Sepal width in centimeters (0-10 cm range)"
    )
    petal_length: float = Field(
        ..., ge=0.0, le=10.0, description="Petal length in centimeters (0-10 cm range)"
    )
    petal_width: float = Field(
        ..., ge=0.0, le=10.0, description="Petal width in centimeters (0-10 cm range)"
    )

    @field_validator("sepal_length", "sepal_width", "petal_length", "petal_width")
    @classmethod
    def validate_measurements(cls, v):
        """Ensure measurements are reasonable for iris flowers"""
        if v < 0:
            raise ValueError("Measurements cannot be negative")
        if v > 15:  # More lenient upper bound for edge cases
            raise ValueError("Measurement seems unusually large for iris flowers")
        return round(v, 2)  # Round to 2 decimal places for consistency

    def to_array(self) -> np.ndarray:
        """Convert to numpy array for model prediction"""
        return np.array(
            [[self.sepal_length, self.sepal_width, self.petal_length, self.petal_width]]
        )

    class Config:
        json_schema_extra = {
            "example": {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2,
            }
        }


class PredictionResponse(BaseModel):
    """
    Response model for iris flower prediction results.
    Includes prediction, confidence scores, and metadata.
    """

    prediction: str = Field(..., description="Predicted iris species")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score for the prediction"
    )
    probabilities: Dict[str, float] = Field(
        ..., description="Probability scores for all classes"
    )
    model_version: str = Field(
        ..., description="Version of the model used for prediction"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Prediction timestamp"
    )
    processing_time_ms: Optional[float] = Field(
        None, description="Processing time in milliseconds"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "prediction": "setosa",
                "confidence": 0.99,
                "probabilities": {
                    "setosa": 0.99,
                    "versicolor": 0.01,
                    "virginica": 0.00,
                },
                "model_version": "1.0.0",
                "timestamp": "2024-01-15T10:30:00",
                "processing_time_ms": 12.5,
            }
        }


class BatchPredictionRequest(BaseModel):
    """
    Request model for batch predictions.
    Allows multiple iris flower predictions in a single request.
    """

    samples: List[PredictionRequest] = Field(
        ...,
        min_length=1,
        max_length=100,  # Reasonable batch size limit
        description="List of iris flower measurements for batch prediction",
    )

    @field_validator("samples")
    @classmethod
    def validate_batch_size(cls, v):
        """Ensure batch size is reasonable"""
        if len(v) > 100:
            raise ValueError("Batch size cannot exceed 100 samples")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "samples": [
                    {
                        "sepal_length": 5.1,
                        "sepal_width": 3.5,
                        "petal_length": 1.4,
                        "petal_width": 0.2,
                    },
                    {
                        "sepal_length": 6.2,
                        "sepal_width": 2.9,
                        "petal_length": 4.3,
                        "petal_width": 1.3,
                    },
                ]
            }
        }


class BatchPredictionResponse(BaseModel):
    """
    Response model for batch prediction results.
    """

    predictions: List[PredictionResponse] = Field(
        ..., description="List of prediction results"
    )
    batch_size: int = Field(..., description="Number of samples processed")
    total_processing_time_ms: float = Field(
        ..., description="Total processing time for the batch"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "predictions": [
                    {
                        "prediction": "setosa",
                        "confidence": 0.99,
                        "probabilities": {
                            "setosa": 0.99,
                            "versicolor": 0.01,
                            "virginica": 0.00,
                        },
                        "model_version": "1.0.0",
                        "timestamp": "2024-01-15T10:30:00",
                    }
                ],
                "batch_size": 2,
                "total_processing_time_ms": 25.3,
            }
        }


class HealthResponse(BaseModel):
    """
    Response model for health check endpoint.
    """

    status: str = Field(..., description="Overall service status")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Health check timestamp"
    )
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    version: str = Field(..., description="API version")
    model_loaded: bool = Field(..., description="Whether the ML model is loaded")
    database_connected: bool = Field(
        ..., description="Whether the database is connected"
    )
    issues: Optional[List[str]] = Field(None, description="List of any issues detected")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-15T10:30:00",
                "uptime_seconds": 3600.5,
                "version": "1.0.0",
                "model_loaded": True,
                "database_connected": True,
            }
        }


class ModelInfoResponse(BaseModel):
    """
    Response model for model information endpoint.
    """

    model_name: str = Field(..., description="Name of the current model")
    model_version: str = Field(..., description="Version of the current model")
    model_type: str = Field(..., description="Type of ML algorithm used")
    training_date: Optional[datetime] = Field(
        None, description="When the model was trained"
    )
    accuracy: Optional[float] = Field(None, description="Model accuracy on test set")
    features: List[str] = Field(..., description="List of input features")
    classes: List[str] = Field(..., description="List of possible output classes")

    class Config:
        json_schema_extra = {
            "example": {
                "model_name": "iris-classifier",
                "model_version": "1.0.0",
                "model_type": "LogisticRegression",
                "training_date": "2024-01-15T09:00:00",
                "accuracy": 0.97,
                "features": [
                    "sepal_length",
                    "sepal_width",
                    "petal_length",
                    "petal_width",
                ],
                "classes": ["setosa", "versicolor", "virginica"],
            }
        }


class ErrorResponse(BaseModel):
    """
    Standard error response model.
    """

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Detailed error message")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Error timestamp"
    )
    request_id: Optional[str] = Field(None, description="Request ID for tracking")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid input: sepal_length must be greater than 0",
                "timestamp": "2024-01-15T10:30:00",
                "request_id": "req_123456",
            }
        }
