"""Basic pytest configuration."""

import pytest


@pytest.fixture
def sample_prediction_request():
    """Sample prediction request data"""
    return {
        "sepal_length": 5.1,
        "sepal_width": 3.5,
        "petal_length": 1.4,
        "petal_width": 0.2
    }