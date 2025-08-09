"""
Unit tests for the LoggingService.
"""

import pytest
import tempfile
import os
import asyncio
from datetime import datetime

from api.logging_service import LoggingService
from api.config import Settings


class TestLoggingService:
    """Test LoggingService class"""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_logs.db")
            settings = Settings(
                database_url=f"sqlite:///{db_path}",
                log_predictions=True
            )
            yield settings
    
    @pytest.mark.asyncio
    async def test_initialization_and_database_setup(self, mock_settings):
        """Test LoggingService initialization and database setup"""
        service = LoggingService(mock_settings)
        await service.initialize_database()
        
        assert service.connection is not None
        assert await service.is_healthy() is True
        
        await service.close()
    
    @pytest.mark.asyncio
    async def test_log_prediction(self, mock_settings):
        """Test logging a single prediction"""
        service = LoggingService(mock_settings)
        await service.initialize_database()
        
        request_data = {
            "sepal_length": 5.1,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2
        }
        
        prediction_result = {
            "prediction": "setosa",
            "confidence": 0.99,
            "probabilities": {"setosa": 0.99, "versicolor": 0.01, "virginica": 0.00},
            "model_version": "test-1.0.0",
            "processing_time_ms": 10.5
        }
        
        # Should not raise any exceptions
        await service.log_prediction(request_data, prediction_result)
        
        # Verify the log was stored
        cursor = service.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM prediction_logs")
        count = cursor.fetchone()[0]
        assert count == 1
        
        await service.close()
    
    @pytest.mark.asyncio
    async def test_log_batch_prediction(self, mock_settings):
        """Test logging batch predictions"""
        service = LoggingService(mock_settings)
        await service.initialize_database()
        
        request_data = [
            {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2},
            {"sepal_length": 6.2, "sepal_width": 2.9, "petal_length": 4.3, "petal_width": 1.3}
        ]
        
        batch_result = {
            "predictions": [
                {
                    "prediction": "setosa",
                    "confidence": 0.99,
                    "probabilities": {"setosa": 0.99, "versicolor": 0.01, "virginica": 0.00},
                    "model_version": "test-1.0.0"
                },
                {
                    "prediction": "versicolor",
                    "confidence": 0.85,
                    "probabilities": {"setosa": 0.05, "versicolor": 0.85, "virginica": 0.10},
                    "model_version": "test-1.0.0"
                }
            ],
            "batch_size": 2,
            "total_processing_time_ms": 25.3
        }
        
        await service.log_batch_prediction(request_data, batch_result)
        
        # Verify both predictions were logged
        cursor = service.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM prediction_logs")
        count = cursor.fetchone()[0]
        assert count == 2
        
        await service.close()
    
    @pytest.mark.asyncio
    async def test_log_system_event(self, mock_settings):
        """Test logging system events"""
        service = LoggingService(mock_settings)
        await service.initialize_database()
        
        event_data = {
            "event": "model_loaded",
            "model_version": "test-1.0.0",
            "timestamp": datetime.now().isoformat()
        }
        
        await service.log_system_event("model_load", event_data, "INFO")
        
        # Verify the event was logged
        cursor = service.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM system_events")
        count = cursor.fetchone()[0]
        assert count == 1
        
        cursor.execute("SELECT event_type, severity FROM system_events")
        row = cursor.fetchone()
        assert row[0] == "model_load"
        assert row[1] == "INFO"
        
        await service.close()
    
    @pytest.mark.asyncio
    async def test_log_api_metrics(self, mock_settings):
        """Test logging API metrics"""
        service = LoggingService(mock_settings)
        await service.initialize_database()
        
        await service.log_api_metrics(
            endpoint="/predict",
            method="POST",
            status_code=200,
            response_time_ms=15.5,
            request_size=256,
            response_size=512
        )
        
        # Verify the metrics were logged
        cursor = service.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM api_metrics")
        count = cursor.fetchone()[0]
        assert count == 1
        
        cursor.execute("SELECT endpoint, method, status_code FROM api_metrics")
        row = cursor.fetchone()
        assert row[0] == "/predict"
        assert row[1] == "POST"
        assert row[2] == 200
        
        await service.close()
    
    @pytest.mark.asyncio
    async def test_get_prediction_stats_empty(self, mock_settings):
        """Test getting prediction stats when no predictions exist"""
        service = LoggingService(mock_settings)
        await service.initialize_database()
        
        stats = await service.get_prediction_stats(24)
        
        assert stats["total_predictions"] == 0
        assert stats["prediction_distribution"] == {}
        
        await service.close()
    
    @pytest.mark.asyncio
    async def test_get_prediction_stats_with_data(self, mock_settings):
        """Test getting prediction stats with existing data"""
        service = LoggingService(mock_settings)
        await service.initialize_database()
        
        # Add some test predictions
        request_data = {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}
        
        for i in range(3):
            prediction_result = {
                "prediction": "setosa",
                "confidence": 0.99,
                "probabilities": {"setosa": 0.99, "versicolor": 0.01, "virginica": 0.00},
                "model_version": "test-1.0.0",
                "processing_time_ms": 10.0 + i
            }
            await service.log_prediction(request_data, prediction_result)
        
        # Add one different prediction
        prediction_result = {
            "prediction": "versicolor",
            "confidence": 0.85,
            "probabilities": {"setosa": 0.05, "versicolor": 0.85, "virginica": 0.10},
            "model_version": "test-1.0.0",
            "processing_time_ms": 12.0
        }
        await service.log_prediction(request_data, prediction_result)
        
        stats = await service.get_prediction_stats(24)
        
        assert stats["total_predictions"] == 4
        assert stats["prediction_distribution"]["setosa"] == 3
        assert stats["prediction_distribution"]["versicolor"] == 1
        assert stats["avg_confidence"] > 0
        assert stats["avg_processing_time_ms"] > 0
        
        await service.close()
    
    @pytest.mark.asyncio
    async def test_get_recent_predictions(self, mock_settings):
        """Test getting recent predictions"""
        service = LoggingService(mock_settings)
        await service.initialize_database()
        
        # Add some test predictions
        request_data = {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}
        
        for i in range(5):
            prediction_result = {
                "prediction": f"class_{i}",
                "confidence": 0.9 + i * 0.01,
                "probabilities": {"setosa": 0.99, "versicolor": 0.01, "virginica": 0.00},
                "model_version": "test-1.0.0",
                "processing_time_ms": 10.0 + i
            }
            await service.log_prediction(request_data, prediction_result)
        
        recent = await service.get_recent_predictions(3)
        
        assert len(recent) == 3
        # Should be in reverse chronological order (most recent first)
        assert recent[0]["prediction"] == "class_4"
        assert recent[1]["prediction"] == "class_3"
        assert recent[2]["prediction"] == "class_2"
        
        await service.close()
    
    @pytest.mark.asyncio
    async def test_is_healthy(self, mock_settings):
        """Test health check functionality"""
        service = LoggingService(mock_settings)
        
        # Before initialization
        assert await service.is_healthy() is False
        
        # After initialization
        await service.initialize_database()
        assert await service.is_healthy() is True
        
        # After closing
        await service.close()
        assert await service.is_healthy() is False
    
    @pytest.mark.asyncio
    async def test_logging_disabled(self):
        """Test that logging can be disabled"""
        settings = Settings(
            database_url="sqlite:///test.db",
            log_predictions=False  # Disabled
        )
        service = LoggingService(settings)
        await service.initialize_database()
        
        request_data = {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}
        prediction_result = {
            "prediction": "setosa",
            "confidence": 0.99,
            "probabilities": {"setosa": 0.99, "versicolor": 0.01, "virginica": 0.00},
            "model_version": "test-1.0.0",
            "processing_time_ms": 10.5
        }
        
        # Should not log anything
        await service.log_prediction(request_data, prediction_result)
        
        cursor = service.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM prediction_logs")
        count = cursor.fetchone()[0]
        assert count == 0  # Nothing should be logged
        
        await service.close()