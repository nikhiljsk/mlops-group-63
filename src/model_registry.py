"""
MLflow Model Registry utilities for managing model versions and deployments.
This module provides functions to interact with the MLflow Model Registry,
including model promotion, version management, and production deployment.
"""

import mlflow
from mlflow.tracking import MlflowClient
from typing import Optional, Dict, Any
import logging

# Set up logging for model registry operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelRegistry:
    """Handles MLflow Model Registry operations for the Iris classifier"""
    
    def __init__(self, model_name: str = "iris-classifier"):
        self.model_name = model_name
        self.client = MlflowClient()
    
    def promote_model_to_production(self, version: str) -> bool:
        """
        Promote a model version to Production stage.
        This will automatically archive any existing Production models.
        """
        try:
            # Archive current production model if exists
            current_production = self.get_production_model()
            if current_production:
                self.client.transition_model_version_stage(
                    name=self.model_name,
                    version=current_production.version,
                    stage="Archived"
                )
                logger.info(f"Archived previous production model version {current_production.version}")
            
            # Promote new model to production
            self.client.transition_model_version_stage(
                name=self.model_name,
                version=version,
                stage="Production"
            )
            logger.info(f"Promoted model version {version} to Production")
            return True
            
        except Exception as e:
            logger.error(f"Failed to promote model to production: {e}")
            return False
    
    def get_production_model(self) -> Optional[Any]:
        """Get the current production model version"""
        try:
            versions = self.client.get_latest_versions(
                self.model_name, 
                stages=["Production"]
            )
            return versions[0] if versions else None
        except Exception as e:
            logger.error(f"Failed to get production model: {e}")
            return None
    
    def get_model_info(self, version: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed information about a model version"""
        try:
            if version:
                model_version = self.client.get_model_version(self.model_name, version)
            else:
                # Get latest production model
                production_model = self.get_production_model()
                if not production_model:
                    return {"error": "No production model found"}
                model_version = production_model
            
            return {
                "name": model_version.name,
                "version": model_version.version,
                "stage": model_version.current_stage,
                "description": model_version.description,
                "creation_timestamp": model_version.creation_timestamp,
                "run_id": model_version.run_id
            }
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {"error": str(e)}
    
    def list_model_versions(self) -> list:
        """List all versions of the registered model"""
        try:
            versions = self.client.search_model_versions(f"name='{self.model_name}'")
            return [
                {
                    "version": v.version,
                    "stage": v.current_stage,
                    "description": v.description,
                    "creation_timestamp": v.creation_timestamp
                }
                for v in versions
            ]
        except Exception as e:
            logger.error(f"Failed to list model versions: {e}")
            return []
    
    def load_production_model(self):
        """Load the current production model for inference"""
        try:
            production_model = self.get_production_model()
            if not production_model:
                logger.warning("No production model found, attempting to load latest version")
                # Fallback to latest version
                latest_versions = self.client.get_latest_versions(self.model_name)
                if not latest_versions:
                    raise Exception("No model versions found")
                production_model = latest_versions[0]
            
            model_uri = f"models:/{self.model_name}/{production_model.version}"
            model = mlflow.sklearn.load_model(model_uri)
            logger.info(f"Loaded model version {production_model.version} from registry")
            return model, production_model.version
            
        except Exception as e:
            logger.error(f"Failed to load model from registry: {e}")
            raise
    
    def compare_model_performance(self, version1: str, version2: str) -> Dict[str, Any]:
        """Compare performance metrics between two model versions"""
        try:
            v1_info = self.client.get_model_version(self.model_name, version1)
            v2_info = self.client.get_model_version(self.model_name, version2)
            
            # Get run metrics for both versions
            v1_run = self.client.get_run(v1_info.run_id)
            v2_run = self.client.get_run(v2_info.run_id)
            
            comparison = {
                "version_1": {
                    "version": version1,
                    "metrics": v1_run.data.metrics
                },
                "version_2": {
                    "version": version2,
                    "metrics": v2_run.data.metrics
                }
            }
            
            # Calculate performance differences
            if "f1_score" in v1_run.data.metrics and "f1_score" in v2_run.data.metrics:
                f1_diff = v2_run.data.metrics["f1_score"] - v1_run.data.metrics["f1_score"]
                comparison["f1_improvement"] = f1_diff
                comparison["better_model"] = version2 if f1_diff > 0 else version1
            
            return comparison
            
        except Exception as e:
            logger.error(f"Failed to compare models: {e}")
            return {"error": str(e)}


def setup_model_registry(model_name: str = "iris-classifier") -> ModelRegistry:
    """Initialize and return a ModelRegistry instance"""
    return ModelRegistry(model_name)