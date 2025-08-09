"""
Unit tests for the PredictionService.
"""

import pytest
import numpy as np
import tempfile
import os
import joblib
from unittest.mock import patch, MagicMock
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from api.prediction_service import PredictionService
from api.config import Settings


class TestPredictionService:
    """Test PredictionService class"""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = os.path.join(temp_dir, "test_model.pkl")
            scaler_path = os.path.join(temp_dir, "test_scaler.pkl")
            
            # Create and save dummy model and scaler
            model = LogisticRegression(random_state=42)
            scaler = StandardScaler()
            
            X_dummy = np.random.RandomState(42).rand(100, 4)
            y_dummy = np.random.RandomState(42).choice(['setosa', 'versicolor', 'virginica'], 100)
            
            X_scaled = scaler.fit_transform(X_dummy)
            model.fit(X_scaled, y_dummy)
            
            joblib.dump(model, model_path)
            joblib.dump(scaler, scaler_path)
            
            settings = Settings(
                model_path=model_path,
                scaler_path=scaler_path,
                use_mlflow_registry=False
            )
            
            yield settings
    
    def test_initialization(self, mock_settings):
        """Test PredictionService initialization"""
        service = PredictionService(mock_settings)
        assert service.settings == mock_settings
        assert service.model is None
        assert service.scaler is None
        assert service.model_loaded is False
        assert service.class_names == ["setosa", "versicolor", "virginica"]
        assert service.feature_names == ["sepal_length", "sepal_width", "petal_length", "petal_width"]
    
    @pytest.mark.asyncio
    async def test_load_model_from_local_files_success(self, mock_settings):
        """Test successful model loading from local files"""
        service = PredictionService(mock_settings)
        result = await service.load_model()
        
        assert result is True
        assert service.is_model_loaded() is True
        assert service.model is not None
        assert service.scaler is not None
        assert service.model_version == "local-1.0.0"
        assert service.model_type == "LogisticRegression"
    
    @pytest.mark.asyncio
    async def test_load_model_file_not_found(self):
        """Test model loading when file doesn't exist"""
        settings = Settings(
            model_path="/nonexistent/path/model.pkl",
            scaler_path="/nonexistent/path/scaler.pkl",
            use_mlflow_registry=False
        )
        service = PredictionService(settings)
        result = await service.load_model()
        
        assert result is False
        assert service.is_model_loaded() is False
    
    @pytest.mark.asyncio
    async def test_predict_success(self, mock_settings):
        """Test successful prediction"""
        service = PredictionService(mock_settings)
        await service.load_model()
        
        # Create test input
        features = np.array([[5.1, 3.5, 1.4, 0.2]])
        
        result = await service.predict(features)
        
        assert "prediction" in result
        assert "confidence" in result
        assert "probabilities" in result
        assert "model_version" in result
        assert "processing_time_ms" in result
        assert "timestamp" in result
        
        assert result["prediction"] in ["setosa", "versicolor", "virginica"]
        assert 0.0 <= result["confidence"] <= 1.0
        assert len(result["probabilities"]) == 3
        assert result["model_version"] == "local-1.0.0"
    
    @pytest.mark.asyncio
    async def test_predict_model_not_loaded(self, mock_settings):
        """Test prediction when model is not loaded"""
        service = PredictionService(mock_settings)
        # Don't load the model
        
        features = np.array([[5.1, 3.5, 1.4, 0.2]])
        
        with pytest.raises(RuntimeError, match="Model not loaded"):
            await service.predict(features)
    
    @pytest.mark.asyncio
    async def test_predict_batch_success(self, mock_settings):
        """Test successful batch prediction"""
        service = PredictionService(mock_settings)
        await service.load_model()
        
        # Create test batch input
        features_batch = np.array([
            [5.1, 3.5, 1.4, 0.2],
            [6.2, 2.9, 4.3, 1.3],
            [7.3, 2.9, 6.3, 1.8]
        ])
        
        result = await service.predict_batch(features_batch)
        
        assert "predictions" in result
        assert "batch_size" in result
        assert "total_processing_time_ms" in result
        
        assert result["batch_size"] == 3
        assert len(result["predictions"]) == 3
        
        # Check each prediction in the batch
        for prediction in result["predictions"]:
            assert "prediction" in prediction
            assert "confidence" in prediction
            assert "probabilities" in prediction
            assert prediction["prediction"] in ["setosa", "versicolor", "virginica"]
    
    @pytest.mark.asyncio
    async def test_predict_batch_model_not_loaded(self, mock_settings):
        """Test batch prediction when model is not loaded"""
        service = PredictionService(mock_settings)
        # Don't load the model
        
        features_batch = np.array([[5.1, 3.5, 1.4, 0.2]])
        
        with pytest.raises(RuntimeError, match="Model not loaded"):
            await service.predict_batch(features_batch)
    
    def test_get_model_info_model_loaded(self, mock_settings):
        """Test get_model_info when model is loaded"""
        service = PredictionService(mock_settings)
        service.model_loaded = True
        service.model_version = "test-1.0.0"
        service.model_type = "LogisticRegression"
        service.load_timestamp = service.load_timestamp or service.__class__.__dict__.get('datetime', type('datetime', (), {'now': lambda: type('dt', (), {'isoformat': lambda: '2024-01-15T10:30:00'})()}))()
        
        info = service.get_model_info()
        
        assert info["model_name"] == mock_settings.mlflow_model_name
        assert info["model_version"] == "test-1.0.0"
        assert info["model_type"] == "LogisticRegression"
        assert info["features"] == ["sepal_length", "sepal_width", "petal_length", "petal_width"]
        assert info["classes"] == ["setosa", "versicolor", "virginica"]
    
    def test_get_model_info_model_not_loaded(self, mock_settings):
        """Test get_model_info when model is not loaded"""
        service = PredictionService(mock_settings)
        # Model not loaded
        
        info = service.get_model_info()
        
        assert "error" in info
        assert info["error"] == "No model loaded"
    
    def test_is_model_loaded(self, mock_settings):
        """Test is_model_loaded method"""
        service = PredictionService(mock_settings)
        
        # Initially not loaded
        assert service.is_model_loaded() is False
        
        # Mock as loaded
        service.model_loaded = True
        service.model = MagicMock()
        assert service.is_model_loaded() is True
        
        # Model loaded but model object is None
        service.model = None
        assert service.is_model_loaded() is False