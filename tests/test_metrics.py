"""Unit tests for metrics collection"""
import pytest
from api.metrics import MetricsCollector

def test_metrics_collector_initialization():
    """Test metrics collector initialization"""
    collector = MetricsCollector()
    assert collector.http_requests_total is not None
    assert collector.predictions_total is not None

def test_record_prediction():
    """Test prediction recording"""
    collector = MetricsCollector()
    collector.record_prediction("v1.0.0", "setosa", 0.95, 10.5)
    # Should not raise any exceptions

def test_record_http_request():
    """Test HTTP request recording"""
    collector = MetricsCollector()
    collector.record_http_request("POST", "/predict", 200, 0.1)
    # Should not raise any exceptions

def test_get_metrics():
    """Test metrics generation"""
    collector = MetricsCollector()
    metrics = collector.get_metrics()
    assert isinstance(metrics, str)
    assert "# HELP" in metrics