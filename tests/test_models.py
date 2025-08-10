"""Basic tests for Pydantic models."""

import pytest
from pydantic import ValidationError
from api.models import PredictionRequest


def test_valid_prediction_request():
    """Test valid prediction request"""
    request = PredictionRequest(
        sepal_length=5.1,
        sepal_width=3.5,
        petal_length=1.4,
        petal_width=0.2
    )
    assert request.sepal_length == 5.1
    assert request.sepal_width == 3.5


def test_negative_values_rejected():
    """Test that negative values are rejected"""
    with pytest.raises(ValidationError):
        PredictionRequest(
            sepal_length=-1.0,
            sepal_width=3.5,
            petal_length=1.4,
            petal_width=0.2
        )


def test_to_array_conversion():
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