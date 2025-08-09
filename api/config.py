"""
Configuration management for the Iris Classification API.
Handles environment variables and application settings.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application configuration using Pydantic BaseSettings.
    Automatically loads from environment variables with fallback defaults.
    """
    
    # API Configuration
    api_title: str = "Iris Classification API"
    api_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Model Configuration
    model_path: str = Field(default="artifacts/best_model.pkl", env="MODEL_PATH")
    scaler_path: str = Field(default="artifacts/scaler.pkl", env="SCALER_PATH")
    mlflow_tracking_uri: str = Field(default="file:./mlruns", env="MLFLOW_TRACKING_URI")
    mlflow_model_name: str = Field(default="iris-classifier", env="MLFLOW_MODEL_NAME")
    use_mlflow_registry: bool = Field(default=True, env="USE_MLFLOW_REGISTRY")
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///./logs.db", env="DATABASE_URL")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_requests: bool = Field(default=True, env="LOG_REQUESTS")
    log_predictions: bool = Field(default=True, env="LOG_PREDICTIONS")
    
    # Performance Configuration
    max_request_size: int = Field(default=1024, env="MAX_REQUEST_SIZE")  # bytes
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")  # seconds
    
    # Security Configuration
    cors_origins: list = Field(default=["*"], env="CORS_ORIGINS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()