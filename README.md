# MLOps Pipeline for Iris Classification

A minimal but complete MLOps pipeline demonstrating best practices for machine learning model deployment using the Iris dataset.

## Features

- **Model Training**: Logistic Regression and Random Forest with MLflow tracking
- **FastAPI REST API** for predictions
- **Docker containerization**
- **CI/CD pipeline** with GitHub Actions
- **Basic logging** with SQLite storage
- **Input validation** with Pydantic
- **Prometheus metrics** endpoint

## Quick Start

### Prerequisites
- Python 3.11+
- Docker
- Git

### 1. Setup
```bash
git clone <your-repo-url>
cd mlops-iris-pipeline
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. Train Models
```bash
python src/train.py
```

### 3. Run API
```bash
# Local development
uvicorn api.main:app --reload

# Or with Docker
docker build -t iris-api .
docker run -p 8000:8000 iris-api
```

### 4. Test API
```bash
# Health check
curl http://localhost:8000/health

# Make prediction
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'
```

## API Endpoints

- `GET /health` - Health check
- `POST /predict` - Single prediction
- `POST /predict/batch` - Batch predictions
- `GET /model/info` - Model information
- `GET /metrics` - Prometheus metrics

## Project Structure

```
├── api/                   # FastAPI application
├── src/                   # ML training code
├── tests/                 # Test suite
├── data/                  # Dataset
├── artifacts/             # Trained models
├── .github/workflows/     # CI/CD pipeline
├── Dockerfile            # Container definition
└── requirements.txt      # Dependencies
```

## CI/CD Pipeline

The GitHub Actions pipeline includes:
1. **Linting** with flake8
2. **Testing** with pytest
3. **Docker build** and push to Docker Hub
4. **Local deployment** testing

### Required Secrets
- `DOCKER_HUB_USERNAME`
- `DOCKER_HUB_ACCESS_TOKEN`

## Testing

```bash
pytest tests/ -v --cov=api --cov=src
```