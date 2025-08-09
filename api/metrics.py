"""
Prometheus metrics collection for the Iris Classification API.
Tracks API performance, prediction metrics, and system health indicators.
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict

from prometheus_client import (CONTENT_TYPE_LATEST, Counter, Gauge, Histogram,
                               Info, generate_latest)

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects and manages Prometheus metrics for the API.
    Tracks predictions, performance, and system health.
    """

    def __init__(self):
        # API request metrics
        self.http_requests_total = Counter(
            "http_requests_total",
            "Total number of HTTP requests",
            ["method", "endpoint", "status_code"],
        )

        self.http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"],
        )

        # Prediction metrics
        self.predictions_total = Counter(
            "ml_predictions_total",
            "Total number of ML predictions made",
            ["model_version", "prediction_class"],
        )

        self.prediction_confidence = Histogram(
            "ml_prediction_confidence",
            "Confidence scores of ML predictions",
            ["model_version", "prediction_class"],
            buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0],
        )

        self.prediction_duration_seconds = Histogram(
            "ml_prediction_duration_seconds",
            "Time taken to make ML predictions",
            ["model_version"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
        )

        # Batch prediction metrics
        self.batch_predictions_total = Counter(
            "ml_batch_predictions_total",
            "Total number of batch predictions made",
            ["model_version"],
        )

        self.batch_size = Histogram(
            "ml_batch_size",
            "Size of batch predictions",
            ["model_version"],
            buckets=[1, 5, 10, 25, 50, 100],
        )

        # System metrics
        self.model_info = Info("ml_model_info", "Information about the loaded ML model")

        self.model_load_timestamp = Gauge(
            "ml_model_load_timestamp_seconds", "Timestamp when the model was loaded"
        )

        self.api_uptime_seconds = Gauge("api_uptime_seconds", "API uptime in seconds")

        self.database_connections = Gauge(
            "database_connections_active", "Number of active database connections"
        )

        # Error metrics
        self.prediction_errors_total = Counter(
            "ml_prediction_errors_total",
            "Total number of prediction errors",
            ["error_type", "model_version"],
        )

        self.api_errors_total = Counter(
            "api_errors_total", "Total number of API errors", ["endpoint", "error_type"]
        )

        # Initialize startup time
        self.startup_time = time.time()

    def record_http_request(
        self, method: str, endpoint: str, status_code: int, duration: float
    ):
        """Record HTTP request metrics"""
        self.http_requests_total.labels(
            method=method, endpoint=endpoint, status_code=str(status_code)
        ).inc()

        self.http_request_duration_seconds.labels(
            method=method, endpoint=endpoint
        ).observe(duration)

    def record_prediction(
        self, model_version: str, prediction: str, confidence: float, duration: float
    ):
        """Record single prediction metrics"""
        self.predictions_total.labels(
            model_version=model_version, prediction_class=prediction
        ).inc()

        self.prediction_confidence.labels(
            model_version=model_version, prediction_class=prediction
        ).observe(confidence)

        self.prediction_duration_seconds.labels(model_version=model_version).observe(
            duration / 1000.0
        )  # Convert ms to seconds

    def record_batch_prediction(
        self, model_version: str, batch_size: int, duration: float
    ):
        """Record batch prediction metrics"""
        self.batch_predictions_total.labels(model_version=model_version).inc()

        self.batch_size.labels(model_version=model_version).observe(batch_size)

        # Record average prediction time per sample
        avg_duration_per_sample = (
            (duration / 1000.0) / batch_size if batch_size > 0 else 0
        )
        self.prediction_duration_seconds.labels(model_version=model_version).observe(
            avg_duration_per_sample
        )

    def record_prediction_error(self, error_type: str, model_version: str = "unknown"):
        """Record prediction error"""
        self.prediction_errors_total.labels(
            error_type=error_type, model_version=model_version
        ).inc()

    def record_api_error(self, endpoint: str, error_type: str):
        """Record API error"""
        self.api_errors_total.labels(endpoint=endpoint, error_type=error_type).inc()

    def update_model_info(self, model_info: Dict[str, Any]):
        """Update model information metrics"""
        try:
            self.model_info.info(
                {
                    "model_name": model_info.get("model_name", "unknown"),
                    "model_version": model_info.get("model_version", "unknown"),
                    "model_type": model_info.get("model_type", "unknown"),
                    "features": ",".join(model_info.get("features", [])),
                    "classes": ",".join(model_info.get("classes", [])),
                }
            )

            # Update model load timestamp if available
            if "load_timestamp" in model_info and model_info["load_timestamp"]:
                try:
                    load_time = datetime.fromisoformat(
                        model_info["load_timestamp"].replace("Z", "+00:00")
                    )
                    self.model_load_timestamp.set(load_time.timestamp())
                except Exception as e:
                    logger.warning(f"Failed to parse model load timestamp: {e}")

        except Exception as e:
            logger.error(f"Failed to update model info metrics: {e}")

    def update_system_metrics(self, uptime_seconds: float, db_connections: int = 1):
        """Update system health metrics"""
        self.api_uptime_seconds.set(uptime_seconds)
        self.database_connections.set(db_connections)

    def get_metrics(self) -> str:
        """Get Prometheus metrics in text format"""
        try:
            return generate_latest()
        except Exception as e:
            logger.error(f"Failed to generate metrics: {e}")
            return "# Error generating metrics\n"

    def get_content_type(self) -> str:
        """Get the content type for Prometheus metrics"""
        return CONTENT_TYPE_LATEST


# Global metrics collector instance
metrics_collector = MetricsCollector()
