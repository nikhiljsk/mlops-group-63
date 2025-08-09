"""Unit tests for configuration management"""
import pytest
from api.config import Settings

def test_settings_defaults():
    """Test default settings"""
    settings = Settings()
    assert settings.api_title == "Iris Classification API"
    assert settings.api_version == "1.0.0"
    assert settings.debug is False

def test_settings_env_override():
    """Test environment variable override"""
    import os
    os.environ["DEBUG"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    settings = Settings()
    assert settings.debug is True
    assert settings.log_level == "DEBUG"
    
    # Cleanup
    del os.environ["DEBUG"]
    del os.environ["LOG_LEVEL"]