"""
Logging service for tracking API requests, predictions, and system events.
Provides persistent storage of prediction logs and system metrics.
"""

import asyncio
import json
import logging
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from .config import Settings

logger = logging.getLogger(__name__)


class LoggingService:
    """
    Service for logging API requests, predictions, and system events.
    Uses SQLite for persistent storage with async support.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.db_path = self._extract_db_path(settings.database_url)
        self.connection = None
        self._lock = asyncio.Lock()

    def _extract_db_path(self, database_url: str) -> str:
        """Extract database file path from database URL"""
        if database_url.startswith("sqlite:///"):
            return database_url.replace("sqlite:///", "")
        elif database_url.startswith("sqlite://"):
            return database_url.replace("sqlite://", "")
        else:
            return "logs.db"  # Default fallback

    async def initialize_database(self):
        """Initialize database and create tables if they don't exist"""
        try:
            async with self._lock:
                self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
                self.connection.row_factory = sqlite3.Row  # Enable dict-like access

                # Create tables
                await self._create_tables()
                logger.info(f"Database initialized: {self.db_path}")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    async def _create_tables(self):
        """Create database tables for logging"""
        cursor = self.connection.cursor()

        # Prediction logs table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS prediction_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                request_data TEXT NOT NULL,
                prediction TEXT NOT NULL,
                probabilities TEXT,
                confidence REAL,
                model_version TEXT,
                processing_time_ms REAL,
                batch_size INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # System events table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS system_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                event_data TEXT,
                severity TEXT DEFAULT 'INFO',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # API metrics table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS api_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                status_code INTEGER,
                response_time_ms REAL,
                request_size_bytes INTEGER,
                response_size_bytes INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        self.connection.commit()
        logger.info("Database tables created/verified")

    async def log_prediction(
        self, request_data: Dict[str, Any], prediction_result: Dict[str, Any]
    ):
        """Log a single prediction request and result"""
        if not self.settings.log_predictions:
            return

        try:
            async with self._lock:
                cursor = self.connection.cursor()
                cursor.execute(
                    """
                    INSERT INTO prediction_logs 
                    (request_data, prediction, probabilities, confidence, model_version, processing_time_ms)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        json.dumps(request_data),
                        prediction_result.get("prediction", ""),
                        json.dumps(prediction_result.get("probabilities", {})),
                        prediction_result.get("confidence", 0.0),
                        prediction_result.get("model_version", "unknown"),
                        prediction_result.get("processing_time_ms", 0.0),
                    ),
                )
                self.connection.commit()

                logger.debug(
                    f"Logged prediction: {prediction_result.get('prediction')}"
                )

        except Exception as e:
            logger.error(f"Failed to log prediction: {e}")

    async def log_batch_prediction(
        self, request_data: List[Dict[str, Any]], batch_result: Dict[str, Any]
    ):
        """Log a batch prediction request and results"""
        if not self.settings.log_predictions:
            return

        try:
            async with self._lock:
                cursor = self.connection.cursor()

                # Log each prediction in the batch
                for i, prediction_result in enumerate(
                    batch_result.get("predictions", [])
                ):
                    individual_request = (
                        request_data[i] if i < len(request_data) else {}
                    )

                    cursor.execute(
                        """
                        INSERT INTO prediction_logs 
                        (request_data, prediction, probabilities, confidence, model_version, 
                         processing_time_ms, batch_size)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            json.dumps(individual_request),
                            prediction_result.get("prediction", ""),
                            json.dumps(prediction_result.get("probabilities", {})),
                            prediction_result.get("confidence", 0.0),
                            prediction_result.get("model_version", "unknown"),
                            batch_result.get("total_processing_time_ms", 0.0)
                            / len(batch_result.get("predictions", [1])),
                            batch_result.get("batch_size", 1),
                        ),
                    )

                self.connection.commit()
                logger.debug(
                    f"Logged batch prediction: {batch_result.get('batch_size')} samples"
                )

        except Exception as e:
            logger.error(f"Failed to log batch prediction: {e}")

    async def log_system_event(
        self, event_type: str, event_data: Dict[str, Any], severity: str = "INFO"
    ):
        """Log system events like model loading, errors, etc."""
        try:
            async with self._lock:
                cursor = self.connection.cursor()
                cursor.execute(
                    """
                    INSERT INTO system_events (event_type, event_data, severity)
                    VALUES (?, ?, ?)
                """,
                    (event_type, json.dumps(event_data), severity),
                )
                self.connection.commit()

                logger.debug(f"Logged system event: {event_type}")

        except Exception as e:
            logger.error(f"Failed to log system event: {e}")

    async def log_api_metrics(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        request_size: int = 0,
        response_size: int = 0,
    ):
        """Log API performance metrics"""
        try:
            async with self._lock:
                cursor = self.connection.cursor()
                cursor.execute(
                    """
                    INSERT INTO api_metrics 
                    (endpoint, method, status_code, response_time_ms, request_size_bytes, response_size_bytes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        endpoint,
                        method,
                        status_code,
                        response_time_ms,
                        request_size,
                        response_size,
                    ),
                )
                self.connection.commit()

        except Exception as e:
            logger.error(f"Failed to log API metrics: {e}")

    async def get_prediction_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get prediction statistics for the last N hours"""
        try:
            async with self._lock:
                cursor = self.connection.cursor()
                cursor.execute(
                    """
                    SELECT 
                        COUNT(*) as total_predictions,
                        COUNT(DISTINCT prediction) as unique_predictions,
                        AVG(confidence) as avg_confidence,
                        AVG(processing_time_ms) as avg_processing_time,
                        prediction,
                        COUNT(*) as count
                    FROM prediction_logs 
                    WHERE timestamp >= datetime('now', '-{} hours')
                    GROUP BY prediction
                    ORDER BY count DESC
                """.format(
                        hours
                    )
                )

                results = cursor.fetchall()

                if not results:
                    return {"total_predictions": 0, "prediction_distribution": {}}

                # Get overall stats
                cursor.execute(
                    """
                    SELECT 
                        COUNT(*) as total_predictions,
                        AVG(confidence) as avg_confidence,
                        AVG(processing_time_ms) as avg_processing_time
                    FROM prediction_logs 
                    WHERE timestamp >= datetime('now', '-{} hours')
                """.format(
                        hours
                    )
                )

                overall_stats = cursor.fetchone()

                # Build prediction distribution
                prediction_distribution = {}
                for row in results:
                    prediction_distribution[row["prediction"]] = row["count"]

                return {
                    "total_predictions": overall_stats["total_predictions"],
                    "avg_confidence": round(overall_stats["avg_confidence"] or 0, 3),
                    "avg_processing_time_ms": round(
                        overall_stats["avg_processing_time"] or 0, 2
                    ),
                    "prediction_distribution": prediction_distribution,
                    "time_window_hours": hours,
                }

        except Exception as e:
            logger.error(f"Failed to get prediction stats: {e}")
            return {"error": str(e)}

    async def get_recent_predictions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent predictions for monitoring"""
        try:
            async with self._lock:
                cursor = self.connection.cursor()
                cursor.execute(
                    """
                    SELECT timestamp, prediction, confidence, model_version, processing_time_ms
                    FROM prediction_logs 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """,
                    (limit,),
                )

                results = cursor.fetchall()
                return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Failed to get recent predictions: {e}")
            return []

    async def is_healthy(self) -> bool:
        """Check if the logging service is healthy"""
        try:
            if not self.connection:
                return False

            async with self._lock:
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                return True

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def close(self):
        """Close database connection"""
        try:
            if self.connection:
                async with self._lock:
                    self.connection.close()
                    self.connection = None
                logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")
