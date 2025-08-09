"""Database integration tests"""
import pytest
import tempfile
import os
from api.logging_service import LoggingService
from api.config import Settings

class TestDatabaseIntegration:
    """Test database integration functionality"""
    
    @pytest.fixture
    def temp_db_service(self):
        """Create temporary database service"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            settings = Settings(database_url=f"sqlite:///{db_path}")
            service = LoggingService(settings)
            yield service
    
    @pytest.mark.asyncio
    async def test_database_lifecycle(self, temp_db_service):
        """Test complete database lifecycle"""
        service = temp_db_service
        
        # Initialize
        await service.initialize_database()
        assert await service.is_healthy()
        
        # Log prediction
        request_data = {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}
        result_data = {"prediction": "setosa", "confidence": 0.95, "model_version": "test"}
        await service.log_prediction(request_data, result_data)
        
        # Get stats
        stats = await service.get_prediction_stats(24)
        assert stats["total_predictions"] == 1
        
        # Close
        await service.close()
        assert not await service.is_healthy()