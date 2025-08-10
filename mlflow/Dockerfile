# MLflow Server Dockerfile for Render Deployment

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /mlflow

# Install MLflow and dependencies
RUN pip install --upgrade pip && \
    pip install \
    mlflow[extras]==2.8.1 \
    psycopg2-binary \
    boto3 \
    azure-storage-blob \
    google-cloud-storage \
    requests \
    flask

# Copy server wrapper
COPY mlflow_server.py /mlflow/mlflow_server.py

# Create non-root user
RUN groupadd -r mlflow && useradd -r -g mlflow mlflow

# Create directories and set permissions
RUN mkdir -p /mlflow/artifacts /mlflow/backend && \
    chown -R mlflow:mlflow /mlflow && \
    chmod +x /mlflow/mlflow_server.py

# Switch to non-root user
USER mlflow

# Health check for MLflow server
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

# Expose port (Render will map this to external port)
EXPOSE 5001

# Start MLflow server wrapper
CMD ["python", "/mlflow/mlflow_server.py"]
