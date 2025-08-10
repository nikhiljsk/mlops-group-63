# Radically Simplified Dockerfile for Development

FROM python:3.11-slim

# Set environment variables for a clean Python environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app"

# Install system dependencies, including git to avoid MLflow warnings
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python -m venv /opt/venv

# Copy only the requirements file to leverage Docker's build cache
COPY requirements.txt .

# Install Python dependencies into the virtual environment
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Create a non-root user for security and the directories we need
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Set the working directory
WORKDIR /app

# The command to run the application. This will be started by docker-compose.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
