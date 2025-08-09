"""
Prediction service for loading and managing ML models.
Handles model loading from local files and MLflow registry with fallback mechanisms.
"""

import os
import logging
import joblib
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
import time

try:
    import mlflow
    import mlflow.sklearn
    from mlflow.tracking import MlflowClient
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    logging.warning("MLflow not available, using local model files only")

from .config import Settings

logger = logging.getLogger(__name__)


class PredictionService:
    """
    Service for loading ML models and making predictions.
    Supports both local file loading and MLflow Model Registry.
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.model = None
        self.scaler = None
        self.model_version = "unknown"
        self.model_type = "unknown"
        self.model_loaded = False
        self.load_timestamp = None
        self.class_names = ["setosa", "versicolor", "virginica"]
        self.feature_names = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
        
        # MLflow client (if available)
        self.mlflow_client = None
        if MLFLOW_AVAILABLE and self.settings.use_mlflow_registry:
            try:
                mlflow.set_tracking_uri(self.settings.mlflow_tracking_uri)
                self.mlflow_client = MlflowClient()
                logger.info(f"MLflow client initialized with URI: {self.settings.mlflow_tracking_uri}")
            except Exception as e:
                logger.warning(f"Failed to initialize MLflow client: {e}")
    
    async def load_model(self) -> bool:
        """
        Load the ML model using the following priority:
        1. MLflow Model Registry (Production stage)
        2. MLflow Model Registry (Latest version)
        3. Local model file
        """
        try:
            # Try MLflow Model Registry first
            if self.mlflow_client and self.settings.use_mlflow_registry:
                if await self._load_from_mlflow_registry():
                    return True
                logger.warning("Failed to load from MLflow registry, falling back to local files")
            
            # Fallback to local files
            return await self._load_from_local_files()
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    async def _load_from_mlflow_registry(self) -> bool:
        """Load model from MLflow Model Registry"""
        try:
            model_name = self.settings.mlflow_model_name
            
            # Try to get production model first
            try:
                production_versions = self.mlflow_client.get_latest_versions(
                    model_name, stages=["Production"]
                )
                if production_versions:
                    model_version = production_versions[0]
                    logger.info(f"Loading production model version {model_version.version}")
                else:
                    # Fallback to latest version
                    latest_versions = self.mlflow_client.get_latest_versions(model_name)
                    if not latest_versions:
                        logger.warning(f"No versions found for model {model_name}")
                        return False
                    model_version = latest_versions[0]
                    logger.info(f"Loading latest model version {model_version.version}")
                
            except Exception as e:
                logger.warning(f"Error accessing model registry: {e}")
                return False
            
            # Load the model
            model_uri = f"models:/{model_name}/{model_version.version}"
            self.model = mlflow.sklearn.load_model(model_uri)
            
            # Try to load scaler from the same run
            try:
                run_id = model_version.run_id
                scaler_uri = f"runs:/{run_id}/scaler"
                self.scaler = mlflow.sklearn.load_model(scaler_uri)
                logger.info("Scaler loaded from MLflow")
            except Exception:
                logger.warning("Scaler not found in MLflow, will try local file")
                await self._load_scaler_from_local()
            
            self.model_version = f"mlflow-{model_version.version}"
            self.model_type = str(type(self.model).__name__)
            self.model_loaded = True
            self.load_timestamp = datetime.now()
            
            logger.info(f"✅ Model loaded from MLflow registry: {self.model_type} v{self.model_version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load from MLflow registry: {e}")
            return False
    
    async def _load_from_local_files(self) -> bool:
        """Load model and scaler from local files"""
        try:
            # Load model
            if not os.path.exists(self.settings.model_path):
                logger.error(f"Model file not found: {self.settings.model_path}")
                return False
            
            self.model = joblib.load(self.settings.model_path)
            logger.info(f"Model loaded from {self.settings.model_path}")
            
            # Load scaler
            await self._load_scaler_from_local()
            
            self.model_version = "local-1.0.0"
            self.model_type = str(type(self.model).__name__)
            self.model_loaded = True
            self.load_timestamp = datetime.now()
            
            logger.info(f"✅ Model loaded from local files: {self.model_type} v{self.model_version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load from local files: {e}")
            return False
    
    async def _load_scaler_from_local(self):
        """Load scaler from local file"""
        try:
            if os.path.exists(self.settings.scaler_path):
                self.scaler = joblib.load(self.settings.scaler_path)
                logger.info(f"Scaler loaded from {self.settings.scaler_path}")
            else:
                logger.warning(f"Scaler file not found: {self.settings.scaler_path}")
                self.scaler = None
        except Exception as e:
            logger.warning(f"Failed to load scaler: {e}")
            self.scaler = None
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded and ready for predictions"""
        return self.model_loaded and self.model is not None
    
    async def predict(self, features: np.ndarray) -> Dict[str, Any]:
        """
        Make prediction on input features.
        Returns prediction with confidence scores and metadata.
        """
        if not self.is_model_loaded():
            raise RuntimeError("Model not loaded. Please load model first.")
        
        start_time = time.time()
        
        try:
            # Preprocess features if scaler is available
            if self.scaler is not None:
                features_scaled = self.scaler.transform(features)
            else:
                features_scaled = features
                logger.warning("No scaler available, using raw features")
            
            # Make prediction
            prediction = self.model.predict(features_scaled)[0]
            
            # Get prediction probabilities
            if hasattr(self.model, 'predict_proba'):
                probabilities = self.model.predict_proba(features_scaled)[0]
                prob_dict = {
                    class_name: float(prob) 
                    for class_name, prob in zip(self.class_names, probabilities)
                }
                confidence = float(max(probabilities))
            else:
                # For models without predict_proba, use binary confidence
                prob_dict = {class_name: 1.0 if class_name == prediction else 0.0 
                           for class_name in self.class_names}
                confidence = 1.0
            
            processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            result = {
                "prediction": prediction,
                "confidence": confidence,
                "probabilities": prob_dict,
                "model_version": self.model_version,
                "processing_time_ms": processing_time,
                "timestamp": datetime.now()
            }
            
            logger.debug(f"Prediction made: {prediction} (confidence: {confidence:.3f})")
            return result
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise RuntimeError(f"Prediction failed: {str(e)}")
    
    async def predict_batch(self, features_batch: np.ndarray) -> Dict[str, Any]:
        """
        Make batch predictions on multiple samples.
        """
        if not self.is_model_loaded():
            raise RuntimeError("Model not loaded. Please load model first.")
        
        start_time = time.time()
        
        try:
            # Preprocess features if scaler is available
            if self.scaler is not None:
                features_scaled = self.scaler.transform(features_batch)
            else:
                features_scaled = features_batch
                logger.warning("No scaler available, using raw features")
            
            # Make predictions
            predictions = self.model.predict(features_scaled)
            
            # Get prediction probabilities
            if hasattr(self.model, 'predict_proba'):
                probabilities_batch = self.model.predict_proba(features_scaled)
            else:
                probabilities_batch = None
            
            # Format results
            results = []
            for i, prediction in enumerate(predictions):
                if probabilities_batch is not None:
                    probabilities = probabilities_batch[i]
                    prob_dict = {
                        class_name: float(prob) 
                        for class_name, prob in zip(self.class_names, probabilities)
                    }
                    confidence = float(max(probabilities))
                else:
                    prob_dict = {class_name: 1.0 if class_name == prediction else 0.0 
                               for class_name in self.class_names}
                    confidence = 1.0
                
                results.append({
                    "prediction": prediction,
                    "confidence": confidence,
                    "probabilities": prob_dict,
                    "model_version": self.model_version,
                    "timestamp": datetime.now()
                })
            
            total_processing_time = (time.time() - start_time) * 1000
            
            return {
                "predictions": results,
                "batch_size": len(predictions),
                "total_processing_time_ms": total_processing_time
            }
            
        except Exception as e:
            logger.error(f"Batch prediction failed: {e}")
            raise RuntimeError(f"Batch prediction failed: {str(e)}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the currently loaded model"""
        if not self.is_model_loaded():
            return {"error": "No model loaded"}
        
        return {
            "model_name": self.settings.mlflow_model_name,
            "model_version": self.model_version,
            "model_type": self.model_type,
            "load_timestamp": self.load_timestamp.isoformat() if self.load_timestamp else None,
            "features": self.feature_names,
            "classes": self.class_names,
            "scaler_available": self.scaler is not None
        }