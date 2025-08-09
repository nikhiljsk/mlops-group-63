"""
FastAPI application for Iris classification model serving.
This module provides REST API endpoints for model predictions, health checks,
and monitoring metrics following MLOps best practices.
"""

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .config import Settings
from .prediction_service import PredictionService
from .logging_service import LoggingService
from .models import (
    PredictionRequest, PredictionResponse, 
    BatchPredictionRequest, BatchPredictionResponse,
    ModelInfoResponse, HealthResponse
)
from .metrics import metrics_collector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global services - will be initialized during startup
prediction_service: PredictionService = None
logging_service: LoggingService = None
app_start_time: datetime = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    Handles model loading and service initialization.
    """
    global prediction_service, logging_service, app_start_time
    
    # Startup
    logger.info("Starting Iris Classification API...")
    app_start_time = datetime.now()
    
    try:
        # Initialize configuration
        settings = Settings()
        
        # Initialize services
        prediction_service = PredictionService(settings)
        logging_service = LoggingService(settings)
        
        # Load model
        await prediction_service.load_model()
        logger.info("✅ Model loaded successfully")
        
        # Initialize database
        await logging_service.initialize_database()
        logger.info("✅ Database initialized")
        
        # Initialize metrics with model info
        if prediction_service.is_model_loaded():
            model_info = prediction_service.get_model_info()
            metrics_collector.update_model_info(model_info)
        
        logger.info("🚀 API startup complete")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Iris Classification API...")
    if logging_service:
        await logging_service.close()
    logger.info("✅ Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Iris Classification API",
    description="MLOps-enabled REST API for Iris flower classification using scikit-learn models",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Iris Classification API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.post("/predict")
async def predict(request: "PredictionRequest") -> "PredictionResponse":
    """
    Make a prediction for a single iris flower sample.
    Accepts flower measurements and returns species prediction with confidence.
    """
    if not prediction_service or not prediction_service.is_model_loaded():
        raise HTTPException(
            status_code=503, 
            detail="Model not available. Please check service health."
        )
    
    try:
        # Convert request to numpy array
        features = request.to_array()
        
        # Make prediction
        result = await prediction_service.predict(features)
        
        # Record metrics
        metrics_collector.record_prediction(
            model_version=result.get("model_version", "unknown"),
            prediction=result.get("prediction", "unknown"),
            confidence=result.get("confidence", 0.0),
            duration=result.get("processing_time_ms", 0.0)
        )
        
        # Log the prediction if logging service is available
        if logging_service:
            await logging_service.log_prediction(request.dict(), result)
        
        # Return formatted response
        from .models import PredictionResponse
        return PredictionResponse(**result)
        
    except Exception as e:
        logger.error(f"Prediction endpoint error: {e}")
        metrics_collector.record_api_error("/predict", "prediction_error")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/predict/batch")
async def predict_batch(request: "BatchPredictionRequest") -> "BatchPredictionResponse":
    """
    Make predictions for multiple iris flower samples in a single request.
    Useful for processing multiple samples efficiently.
    """
    if not prediction_service or not prediction_service.is_model_loaded():
        raise HTTPException(
            status_code=503, 
            detail="Model not available. Please check service health."
        )
    
    try:
        # Convert all samples to numpy array
        import numpy as np
        features_batch = np.vstack([sample.to_array() for sample in request.samples])
        
        # Make batch prediction
        result = await prediction_service.predict_batch(features_batch)
        
        # Record batch metrics
        if result.get("predictions"):
            model_version = result["predictions"][0].get("model_version", "unknown")
            metrics_collector.record_batch_prediction(
                model_version=model_version,
                batch_size=result.get("batch_size", 0),
                duration=result.get("total_processing_time_ms", 0.0)
            )
        
        # Log batch prediction if logging service is available
        if logging_service:
            await logging_service.log_batch_prediction(
                [sample.dict() for sample in request.samples], 
                result
            )
        
        # Return formatted response
        from .models import BatchPredictionResponse, PredictionResponse
        formatted_predictions = [PredictionResponse(**pred) for pred in result["predictions"]]
        
        return BatchPredictionResponse(
            predictions=formatted_predictions,
            batch_size=result["batch_size"],
            total_processing_time_ms=result["total_processing_time_ms"]
        )
        
    except Exception as e:
        logger.error(f"Batch prediction endpoint error: {e}")
        metrics_collector.record_api_error("/predict/batch", "batch_prediction_error")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")


@app.get("/model/info")
async def get_model_info() -> "ModelInfoResponse":
    """
    Get information about the currently loaded model.
    Returns model metadata, version, and performance metrics.
    """
    if not prediction_service or not prediction_service.is_model_loaded():
        raise HTTPException(
            status_code=503, 
            detail="Model not available. Please check service health."
        )
    
    try:
        model_info = prediction_service.get_model_info()
        
        from .models import ModelInfoResponse
        return ModelInfoResponse(
            model_name=model_info.get("model_name", "unknown"),
            model_version=model_info.get("model_version", "unknown"),
            model_type=model_info.get("model_type", "unknown"),
            training_date=model_info.get("load_timestamp"),
            features=model_info.get("features", []),
            classes=model_info.get("classes", [])
        )
        
    except Exception as e:
        logger.error(f"Model info endpoint error: {e}")
        metrics_collector.record_api_error("/model/info", "model_info_error")
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancer probes.
    Returns detailed service health information.
    """
    try:
        uptime = (datetime.now() - app_start_time).total_seconds() if app_start_time else 0
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": uptime,
            "version": "1.0.0",
            "model_loaded": prediction_service is not None and prediction_service.is_model_loaded(),
            "database_connected": logging_service is not None and await logging_service.is_healthy()
        }
        
        # Check if all critical services are working
        if not health_status["model_loaded"]:
            health_status["status"] = "degraded"
            health_status["issues"] = ["Model not loaded"]
        
        if not health_status["database_connected"]:
            health_status["status"] = "degraded" if health_status["status"] == "healthy" else "unhealthy"
            health_status.setdefault("issues", []).append("Database not connected")
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


@app.get("/metrics")
async def get_metrics():
    """
    Prometheus metrics endpoint.
    Returns metrics in Prometheus text format for scraping.
    """
    try:
        # Update system metrics before returning
        uptime = (datetime.now() - app_start_time).total_seconds() if app_start_time else 0
        metrics_collector.update_system_metrics(uptime)
        
        # Return metrics in Prometheus format
        metrics_data = metrics_collector.get_metrics()
        return Response(
            content=metrics_data,
            media_type=metrics_collector.get_content_type()
        )
        
    except Exception as e:
        logger.error(f"Metrics endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate metrics: {str(e)}")


@app.post("/retrain")
async def trigger_retraining():
    """
    Trigger model retraining process.
    Checks if retraining is needed and initiates the process.
    """
    try:
        from .retraining import retraining_service
        
        # Check if retraining is needed
        needs_retraining = await retraining_service.check_retraining_needed()
        
        if not needs_retraining:
            return {
                "status": "skipped",
                "message": "Retraining not needed at this time",
                "timestamp": datetime.now().isoformat()
            }
        
        # Trigger retraining
        result = await retraining_service.trigger_retraining()
        
        return {
            "retraining_result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Retraining endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Retraining failed: {str(e)}")


@app.get("/retrain/status")
async def get_retraining_status():
    """
    Get current retraining status and model information.
    """
    try:
        from .retraining import retraining_service
        
        needs_retraining = await retraining_service.check_retraining_needed()
        last_training = await retraining_service._get_last_training_time()
        
        return {
            "needs_retraining": needs_retraining,
            "last_training": last_training.isoformat() if last_training else None,
            "current_model": prediction_service.get_model_info() if prediction_service else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Retraining status error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get retraining status: {str(e)}")


if __name__ == "__main__":
    # Development server configuration
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )