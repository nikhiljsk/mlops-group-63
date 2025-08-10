# Final Dockerfile for Production Deployment on Render

# Use a slim Python image as a base
FROM python:3.11-slim

# Set environment variables for a clean Python environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app"

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Create and activate a virtual environment
RUN python -m venv /opt/venv

# Copy only the requirements file first to leverage Docker's build cache
WORKDIR /app
COPY requirements.txt .

# Install Python dependencies into the virtual environment
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ✨ THIS IS THE FIX: Copy all application code into the image
COPY api/ ./api/
COPY src/ ./src/
COPY artifacts/ ./artifacts/
COPY data/ ./data/

# Create a non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create and set permissions for the logs directory
RUN mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Health check to ensure the API is responsive
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose the port the application will run on
EXPOSE 8000

# The command to run the application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
