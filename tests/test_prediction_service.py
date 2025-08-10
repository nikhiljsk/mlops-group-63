"""Basic tests for PredictionService."""

import pytest
import numpy as np
from unittest.mock import MagicMock

from api.prediction_service import PredictionService


def test_prediction_service_initialization():
    """Test PredictionService initialization"""
    mock_settings = MagicMock()
    service = PredictionService(mock_settings)
    assert service is not None


def test_is_model_loaded_false_initially():
    """Test model loaded status is false initially"""
    mock_settings = MagicMock()
    service = PredictionService(mock_settings)
    assert service.is_model_loaded() is False