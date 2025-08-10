# 🌸 MLOps Pipeline for Iris Classification

## 🎬 Video Demo

[Watch the video demo on YouTube](https://youtu.be/jteJDs5c3wY)

A complete, production-ready MLOps pipeline demonstrating industry best practices for machine learning model development, deployment, and monitoring using the Iris dataset.

## 🚀 Features

- **🤖 Model Training**: 5 ML algorithms with MLflow experiment tracking
- **🔥 FastAPI REST API** with comprehensive endpoints
- **🐳 Docker containerization** with multi-stage builds
- **⚙️ CI/CD pipeline** with GitHub Actions automation
- **📊 Advanced monitoring** with Prometheus metrics
- **🎯 Interactive web demo** for live demonstrations
- **📈 DVC integration** for data and model versioning
- **🔍 Comprehensive evaluation** with visualizations
- **✅ Input validation** with Pydantic models
- **📋 Structured logging** with SQLite storage

## 🎬 Quick Demo

### 🚀 One-Command Demo
```bash
./run_demo.sh full
```

This launches the complete MLOps pipeline:
- 📊 **Prometheus**: http://localhost:9090 (Metrics & monitoring)
- 🔥 **FastAPI**: http://localhost:8000 (ML API with docs)
- 🌐 **Web Demo**: http://localhost:3001 (Interactive dashboard)
- 📈 **Grafana**: http://localhost:3000 (Visualization dashboard)

### 📋 Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Git

### 🔧 Step-by-Step Setup
```bash
# 1. Clone and setup
git clone <your-repo-url>
cd mlops-iris-pipeline

# 2. Setup environment and DVC
./setup_dvc.sh

# 3. Run complete demo
./run_demo.sh full
```

### 🧪 Individual Components
```bash
# Setup only
./run_demo.sh setup

# Train models with MLflow tracking
./run_demo.sh train

# Start all services
./run_demo.sh start

# Run comprehensive tests
./run_demo.sh test
```

## 🎯 Demo Highlights

### 🌐 Interactive Web Dashboard
- **Real-time predictions** with confidence visualization
- **Live system monitoring** with health indicators
- **Batch testing** capabilities with sample data
- **Metrics visualization** with charts and graphs
- **Direct links** to MLflow, Prometheus, and API docs

### 🔥 API Endpoints
- `GET /` - API information and status
- `GET /health` - Comprehensive health check
- `POST /predict` - Single prediction with confidence
- `POST /predict/batch` - Batch predictions (up to 100 samples)
- `GET /model/info` - Model metadata and version info
- `GET /metrics` - Prometheus metrics for monitoring

### 📊 MLflow Integration
- **5 different algorithms** trained and compared
- **Experiment tracking** with parameters and metrics
- **Model registry** with versioning
- **Artifact storage** for reproducibility

### 📈 Prometheus Monitoring
- **Custom ML metrics**: predictions, confidence, latency
- **API performance**: request rate, response time, errors
- **System health**: uptime, memory, CPU usage
- **Ready for Grafana** dashboards and alerting

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           MLOps Iris Classification Pipeline                    │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Layer    │    │ Training Layer  │    │ Serving Layer   │    │ Monitoring      │
│                 │    │                 │    │                 │    │                 │
│ • Iris Dataset  │───▶│ • 5 ML Models   │───▶│ • FastAPI       │───▶│ • Prometheus    │
│ • DVC Tracking  │    │ • MLflow Track  │    │ • Docker        │    │ • Custom Metrics│
│ • Preprocessing │    │ • Best Selection│    │ • Load Balancer │    │ • Health Checks │
│ • params.yaml   │    │ • Evaluation    │    │ • Batch Predict │    │ • SQLite Logs   │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Version Control │    │   CI/CD Layer   │    │ User Interface  │    │ Orchestration   │
│                 │    │                 │    │                 │    │                 │
│ • Git + GitHub  │    │ • GitHub Actions│    │ • Web Dashboard │    │ • Docker Compose│
│ • DVC Pipeline  │    │ • Automated Test│    │ • API Docs      │    │ • Port Mapping  │
│ • Model Registry│    │ • Docker Build  │    │ • Live Metrics  │    │ • Service Mesh  │
│ • Artifact Store│    │ • Quality Gates │    │ • Retrain UI    │    │ • Health Probes │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘

                                    Service Endpoints:
                            ┌─────────────────────────────────┐
                            │ • Frontend:    localhost:3001   │
                            │ • API Server:  localhost:8000   │
                            │ • Prometheus:  localhost:9090   │
                            │ • Grafana:     localhost:3000   │
                            └─────────────────────────────────┘
```

## 📁 Project Structure

```
mlops-iris-pipeline/
├── 🌐 frontend/              # Interactive web demo
│   ├── index.html           # Dashboard interface
│   └── app.js              # Frontend logic
├── 🔥 api/                   # FastAPI application
│   ├── main.py             # API endpoints + /retrain
│   ├── models.py           # Pydantic models
│   ├── prediction_service.py # ML inference
│   ├── metrics.py          # Prometheus metrics
│   └── logging_service.py  # Structured logging
├── 🧠 src/                   # ML pipeline
│   ├── train.py            # Model training (5 algorithms)
│   ├── evaluate.py         # Model evaluation
│   └── preprocess.py       # Data preprocessing
├── 🧪 tests/                 # Comprehensive test suite
├── 📊 data/                  # Dataset (DVC tracked)
├── 🎯 artifacts/             # Models & scalers (DVC tracked)
├── ⚙️ .github/workflows/     # CI/CD automation
├── 🐳 Dockerfile            # Container definition
├── 📋 dvc.yaml              # DVC pipeline
├── ⚙️ params.yaml           # DVC parameters
├── 🚀 run_demo.sh           # Demo runner script
├── 🔧 demo_dvc.py           # DVC demonstration
└── 📋 integration_test.py   # End-to-end testing
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

## 🎯 Technical Implementation

### 📊 Data Management & Versioning
- Clean GitHub repository with professional structure
- Iris dataset with comprehensive preprocessing pipeline
- **DVC integration** for data and model versioning
- Centralized parameter management with `params.yaml`

### 🤖 Machine Learning Pipeline
- **5 ML algorithms** implemented: LogisticRegression, RandomForest, SVM, KNN, NaiveBayes
- **MLflow experiment tracking** with automated parameter and metric logging
- **Intelligent model selection** based on F1 score performance
- **Cross-validation** and comprehensive model evaluation

### 🔥 Production API & Containerization
- **FastAPI REST API** with 6 comprehensive endpoints
- **Docker containerization** using multi-stage builds for optimization
- **Pydantic validation** for robust input/output handling
- **Batch prediction** support for efficient processing

### ⚙️ DevOps & Automation
- **GitHub Actions CI/CD** with automated linting, testing, and deployment
- **Comprehensive testing** suite with pytest achieving 90%+ coverage
- **Docker Hub integration** for automated image building and distribution
- **Quality gates** ensuring code standards and reliability

### 📈 Monitoring & Observability
- **Structured logging** with SQLite database storage
- **Prometheus metrics** integration with custom ML-specific metrics
- **Real-time monitoring** of predictions, confidence scores, and latency
- **Health monitoring** endpoints for system status tracking

### 🌐 User Experience & Deployment
- **Interactive web dashboard** for live demonstrations and testing
- **Comprehensive API documentation** with automatic Swagger UI
- **Cloud deployment** ready with Render.com configuration
- **Live model retraining** capabilities via API endpoints

## 🔄 Data Flow & Process

```
Training Pipeline:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ iris.csv    │───▶│ preprocess  │───▶│ train 5     │───▶│ best_model  │
│ (DVC track) │    │ + scale     │    │ algorithms  │    │ selection   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                           │                   │                   │
                           ▼                   ▼                   ▼
                   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
                   │ scaler.pkl  │    │ MLflow      │    │ artifacts/  │
                   │ (artifacts) │    │ experiments │    │ (DVC track) │
                   └─────────────┘    └─────────────┘    └─────────────┘

Serving Pipeline:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ HTTP Request│───▶│ FastAPI     │───▶│ Model       │───▶│ JSON        │
│ (JSON data) │    │ Validation  │    │ Prediction  │    │ Response    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                           │                   │                   │
                           ▼                   ▼                   ▼
                   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
                   │ Prometheus  │    │ SQLite      │    │ Web         │
                   │ Metrics     │    │ Logging     │    │ Dashboard   │
                   └─────────────┘    └─────────────┘    └─────────────┘

Retraining Pipeline:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ /retrain    │───▶│ src/train.py│───▶│ New Model   │───▶│ Hot Reload  │
│ API Call    │    │ Execution   │    │ Selection   │    │ Service     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## 🧪 Testing & Validation

```bash
# Run all tests with coverage
pytest tests/ -v --cov=api --cov=src --cov-report=html

# Run pipeline tests
python test_pipeline.py

# Run integration tests
python integration_test.py

# Test with demo script
./run_demo.sh test

# Show DVC integration
python demo_dvc.py
```