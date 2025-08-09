"""
Pytest configuration and fixtures for the Iris Classification API tests.
"""

import pytest
import tempfile
import os
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from fastapi.testclient import TestClient

from api.main import app
from api.config import Settings


@pytest.fixture
def test_settings():
    """Create test settings with temporary paths"""
    with tempfile.TemporaryDirectory() as temp_dir:
        model_path = os.path.join(temp_dir, "test_model.pkl")
        scaler_path = os.path.join(temp_dir, "test_scaler.pkl")
        db_path = os.path.join(temp_dir, "test_logs.db")
        
        # Create dummy model and scaler
        model = LogisticRegression(random_state=42)
        scaler = StandardScaler()
        
        # Create dummy training data
        X_dummy = np.random.RandomState(42).rand(100, 4)
        y_dummy = np.random.RandomState(42).choice(['setosa', 'versicolor', 'virginica'], 100)
        
        # Fit and save
        X_scaled = scaler.fit_transform(X_dummy)
        model.fit(X_scaled, y_dummy)
        
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        
        # Create test settings
        settings = Settings(
            model_path=model_path,
            scaler_path=scaler_path,
            database_url=f"sqlite:///{db_path}",
            use_mlflow_registry=False,
            log_predictions=True
        )
        
        yield settings


@pytest.fixture
def client():
    """Create test client for FastAPI app"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_prediction_request():
    """Sample prediction request data"""
    return {
        "sepal_length": 5.1,
        "sepal_width": 3.5,
        "petal_length": 1.4,
        "petal_width": 0.2
    }


@pytest.fixture
def sample_batch_request():
    """Sample batch prediction request data"""
    return {
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