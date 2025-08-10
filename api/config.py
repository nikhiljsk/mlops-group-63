"""Simple configuration for the Iris Classification API."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration."""
    
    # Model paths
    model_path: str = Field(default="artifacts/best_model.pkl", env="MODEL_PATH")
    scaler_path: str = Field(default="artifacts/scaler.pkl", env="SCALER_PATH")
    
    # MLflow
    mlflow_tracking_uri: str = Field(default="file:./mlruns", env="MLFLOW_TRACKING_URI")
    mlflow_model_name: str = Field(default="iris-classifier", env="MLFLOW_MODEL_NAME")
    use_mlflow_registry: bool = Field(default=False, env="USE_MLFLOW_REGISTRY")
    
    # Database
    database_url: str = Field(default="sqlite:///./logs.db", env="DATABASE_URL")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_predictions: bool = Field(default=True, env="LOG_PREDICTIONS")

    model_config = {"env_file": ".env"}
