# Iris Classification API Dockerfile for Render

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy only essential application code
COPY api ./api
COPY src ./src

# Create all necessary directories
RUN mkdir -p ./artifacts ./data ./logs

# Create dummy model files for the application to work
RUN python -c "
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import numpy as np

print('Creating model files for container...')
model = LogisticRegression(random_state=42)
scaler = StandardScaler()
X = np.random.RandomState(42).rand(100, 4)
y = np.random.RandomState(42).choice(['setosa', 'versicolor', 'virginica'], 100)
X_scaled = scaler.fit_transform(X)
model.fit(X_scaled, y)
joblib.dump(model, './artifacts/best_model.pkl')
joblib.dump(scaler, './artifacts/scaler.pkl')
print('Model files created successfully')
"

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create directories and set permissions
RUN mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
