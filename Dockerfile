# Dockerfile (Radically Simplified for Git Clone on Render)

FROM python:3.11-slim

# Set environment variables for a clean Python environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:$PATH"

# Install system dependencies, including git
RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python -m venv /opt/venv

# Copy only the requirements file to install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Create a non-root user and a directory for our code
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    mkdir /app && \
    chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser
WORKDIR /app

# NOTE: We no longer COPY code. The startCommand in render.yaml will do that.
# The CMD is now just a placeholder.
CMD ["echo", "Starting container..."]
