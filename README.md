# 🌸 MLOps Pipeline for Iris Classification

A complete, production-ready MLOps pipeline demonstrating industry best practices for machine learning model deployment, monitoring, and lifecycle management using the Iris dataset.

## 🚀 Features

- **FastAPI REST API** with comprehensive endpoints
- **Docker containerization** with multi-stage builds
- **CI/CD pipeline** with GitHub Actions
- **Prometheus monitoring** and Grafana dashboards
- **Automated testing** (unit + integration)
- **Model retraining** with drift detection
- **Kubernetes deployment** ready
- **Security scanning** and best practices

## 📊 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Input    │───▶│  ML Pipeline    │───▶│   API Service   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MLflow        │    │   Model Store   │    │   Monitoring    │
│   Tracking      │    │   (Artifacts)   │    │  (Prometheus)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🏃 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Git

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd mlops-group-63
```

### 2. Local Development
```bash
# Start local development server
./deploy.sh local

# Or use Docker Compose
docker-compose up -d
```

### 3. Access Services
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## 🔧 API Endpoints

### Core Endpoints
- `GET /health` - Health check
- `POST /predict` - Single prediction
- `POST /predict/batch` - Batch predictions
- `GET /model/info` - Model information
- `GET /metrics` - Prometheus metrics

### Advanced Endpoints
- `POST /retrain` - Trigger model retraining
- `GET /retrain/status` - Retraining status

### Example Usage
```bash
# Health check
curl http://localhost:8000/health

# Make prediction
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'

# Trigger retraining
curl -X POST http://localhost:8000/retrain
```

## 🚢 Deployment Options

### Docker Deployment
```bash
# Development environment
./deploy.sh docker --environment development

# Production environment
DOCKER_HUB_USERNAME=your-username ./deploy.sh docker --environment production
```

### Kubernetes Deployment
```bash
# Set environment variables
export DOCKER_HUB_USERNAME=your-username
export DOMAIN=iris-api.yourdomain.com

# Deploy to Kubernetes
./deploy.sh k8s
```

### Docker Compose
```bash
# Development with hot reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production with monitoring
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
pytest tests/ -v --cov=api --cov=src --cov-report=term-missing

# Run integration tests
make test-integration

# Local CI/CD pipeline test
make test-local
```

## 📊 Monitoring & Observability

### Metrics Collected
- HTTP request rates and latencies
- Model prediction counts and confidence
- Error rates and types
- System resource usage

### Dashboards
- **Grafana**: Pre-configured dashboards for API and ML metrics
- **Prometheus**: Raw metrics and alerting rules

### Alerting
- High error rates (>10% for 5 minutes)
- High response times (>1s 95th percentile)
- Model prediction failures
- API downtime

## 🔄 CI/CD Pipeline

The GitHub Actions pipeline includes:

1. **Testing Phase**
   - Code linting (flake8)
   - Unit and integration tests
   - Coverage reporting

2. **Build Phase**
   - Multi-platform Docker builds
   - Security scanning (Trivy)
   - Docker Hub push

3. **Deploy Phase**
   - Automated deployment (main branch)
   - Health checks
   - Rollback on failure

### Required Secrets
```bash
DOCKER_HUB_USERNAME=your-dockerhub-username
DOCKER_HUB_ACCESS_TOKEN=your-access-token
```

## 🔒 Security Features

- **Container Security**: Non-root user, read-only filesystem
- **Input Validation**: Pydantic models with range validation
- **Security Scanning**: Automated vulnerability scanning
- **HTTPS Ready**: TLS termination support
- **Rate Limiting**: Configurable request limits

## 📁 Project Structure

```
├── api/                    # FastAPI application
│   ├── main.py            # Main application
│   ├── models.py          # Pydantic models
│   ├── prediction_service.py
│   ├── logging_service.py
│   ├── metrics.py         # Prometheus metrics
│   └── retraining.py      # Model retraining
├── src/                   # ML training code
├── tests/                 # Test suite
├── deploy/                # Deployment automation
├── monitoring/            # Monitoring configs
├── .github/workflows/     # CI/CD pipeline
├── docker-compose.yml     # Container orchestration
└── Dockerfile            # Container definition
```

## 🛠️ Development

### Setup Development Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Install development tools
make install-dev
```

### Code Quality
```bash
# Format code
make format

# Lint code
make lint
```

## 🔧 Configuration

### Environment Variables
```bash
# Application
DEBUG=false
LOG_LEVEL=INFO
USE_MLFLOW_REGISTRY=false

# Database
DATABASE_URL=sqlite:///./logs.db

# Monitoring
LOG_PREDICTIONS=true
LOG_REQUESTS=true
```

## 📈 Performance

### Benchmarks
- **Response Time**: <100ms (95th percentile)
- **Throughput**: >1000 requests/second
- **Memory Usage**: <512MB
- **Startup Time**: <30 seconds

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## 📚 Documentation

- [Deployment Guide](DEPLOYMENT.md)
- [API Documentation](http://localhost:8000/docs)
- [Testing Guide](tests/README.md)

## 🐛 Troubleshooting

### Common Issues

**Container won't start:**
```bash
docker logs iris-api-prod
```

**Health check fails:**
```bash
curl -v http://localhost:8000/health
```

**Model not loading:**
```bash
ls -la artifacts/
```

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Scikit-learn for the ML algorithms
- FastAPI for the web framework
- Prometheus & Grafana for monitoring
- Docker for containerization