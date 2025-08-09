# Deployment Guide

This guide covers deployment strategies for the Iris Classification API, including CI/CD automation, manual deployment, and production best practices.

## Table of Contents

- [CI/CD Pipeline](#cicd-pipeline)
- [Manual Deployment](#manual-deployment)
- [Production Deployment](#production-deployment)
- [Docker Hub Integration](#docker-hub-integration)
- [Rollback Procedures](#rollback-procedures)
- [Monitoring and Health Checks](#monitoring-and-health-checks)
- [Troubleshooting](#troubleshooting)

## CI/CD Pipeline

### GitHub Actions Workflow

The automated CI/CD pipeline is defined in `.github/workflows/ci-cd.yml` and includes:

1. **Testing Phase**
   - Code linting (flake8)
   - Code formatting checks (black, isort)
   - Unit tests with coverage
   - Integration tests

2. **Build Phase**
   - Multi-platform Docker build (linux/amd64, linux/arm64)
   - Docker Hub push with multiple tags
   - Security scanning with Trivy
   - Build caching for faster builds

3. **Deploy Phase** (main branch only)
   - Automated deployment to production
   - Health checks and post-deployment tests
   - Deployment summary generation

### Required Secrets

Configure these secrets in your GitHub repository:

```bash
# GitHub Repository Settings > Secrets and Variables > Actions
DOCKER_HUB_USERNAME=your-dockerhub-username
DOCKER_HUB_ACCESS_TOKEN=your-dockerhub-access-token
```

### Image Tagging Strategy

The pipeline automatically creates multiple tags:

- `latest` - Latest stable version (main branch)
- `main-<sha>` - Main branch with commit SHA
- `develop-<sha>` - Develop branch with commit SHA
- `pr-<number>` - Pull request builds

## Manual Deployment

### Quick Deployment

Use the deployment script for easy manual deployment:

```bash
# Basic deployment
./scripts/deploy.sh

# Custom configuration
./scripts/deploy.sh \
  --image your-username/iris-classifier-api \
  --tag v1.0.0 \
  --port 8080 \
  --environment production
```

### Docker Compose Deployment

#### Development Environment

```bash
# Start development environment
docker-compose up -d

# With hot reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

#### Production Environment

```bash
# Set environment variables
export DOCKER_HUB_USERNAME=your-username
export IMAGE_TAG=latest

# Start production environment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Manual Docker Commands

```bash
# Pull the latest image
docker pull your-username/iris-classifier-api:latest

# Run the container
docker run -d \
  --name iris-api-prod \
  --restart unless-stopped \
  -p 8000:8000 \
  -e LOG_LEVEL=INFO \
  -e USE_MLFLOW_REGISTRY=false \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/artifacts:/app/artifacts \
  your-username/iris-classifier-api:latest
```

## Production Deployment

### Environment Configuration

#### Required Environment Variables

```bash
# Application Configuration
LOG_LEVEL=INFO
DEBUG=false
USE_MLFLOW_REGISTRY=false
DATABASE_URL=sqlite:///./logs.db

# Logging Configuration
LOG_PREDICTIONS=true
LOG_REQUESTS=true

# Performance Configuration
MAX_REQUEST_SIZE=1024
REQUEST_TIMEOUT=30
```

#### Optional Environment Variables

```bash
# MLflow Configuration (if using MLflow registry)
MLFLOW_TRACKING_URI=http://mlflow:5001
MLFLOW_MODEL_NAME=iris-classifier

# Security Configuration
CORS_ORIGINS=["https://yourdomain.com"]
```

### Volume Mounts

```bash
# Required volumes for production
-v /path/to/logs:/app/logs          # Persistent logging
-v /path/to/data:/app/data          # Input data (read-only)
-v /path/to/artifacts:/app/artifacts # Model artifacts (read-only)
```

### Health Checks

The container includes built-in health checks:

```bash
# Docker health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Manual health check
curl http://localhost:8000/health
```

### Resource Requirements

#### Minimum Requirements
- **CPU**: 0.5 cores
- **Memory**: 512MB
- **Storage**: 1GB (for logs and data)

#### Recommended for Production
- **CPU**: 1-2 cores
- **Memory**: 1-2GB
- **Storage**: 5GB (for logs, data, and artifacts)

## Docker Hub Integration

### Image Repository Structure

```
your-username/iris-classifier-api:
├── latest          # Latest stable release
├── v1.0.0          # Semantic version tags
├── main-abc123     # Main branch builds
├── develop-def456  # Development builds
└── pr-42           # Pull request builds
```

### Building and Pushing Images

```bash
# Build multi-platform image
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag your-username/iris-classifier-api:latest \
  --push .

# Build for specific platform
docker build -t your-username/iris-classifier-api:latest .
docker push your-username/iris-classifier-api:latest
```

### Image Security

- **Base Image**: python:3.11-slim (regularly updated)
- **Security Scanning**: Trivy vulnerability scanning in CI/CD
- **Non-root User**: Container runs as non-root user
- **Minimal Dependencies**: Only required packages included

## Rollback Procedures

### Automated Rollback

Use the rollback script for safe version rollback:

```bash
# List available versions
./scripts/rollback.sh --list

# Rollback to specific version
./scripts/rollback.sh --tag v1.0.0

# Force rollback without confirmation
./scripts/rollback.sh --tag previous-version --force
```

### Manual Rollback

```bash
# Stop current container
docker stop iris-api-prod

# Start previous version
docker run -d \
  --name iris-api-prod-rollback \
  --restart unless-stopped \
  -p 8000:8000 \
  your-username/iris-classifier-api:previous-tag

# Verify health
curl http://localhost:8000/health
```

### Rollback Strategy

1. **Immediate Rollback**: For critical issues
2. **Staged Rollback**: For non-critical issues with testing
3. **Blue-Green Deployment**: For zero-downtime rollbacks

## Monitoring and Health Checks

### Health Endpoints

```bash
# Basic health check
GET /health
{
  "status": "healthy",
  "uptime_seconds": 3600,
  "model_loaded": true,
  "database_connected": true
}

# Detailed metrics
GET /metrics
# Returns Prometheus-format metrics

# Model information
GET /model/info
{
  "model_name": "iris-classifier",
  "model_version": "1.0.0",
  "model_type": "LogisticRegression"
}
```

### Monitoring Stack

The production deployment includes:

- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **Application Logs**: Structured logging to files and database

### Key Metrics to Monitor

- **Request Rate**: Requests per second
- **Response Time**: API response latency
- **Error Rate**: 4xx/5xx error percentage
- **Model Performance**: Prediction accuracy and confidence
- **Resource Usage**: CPU, memory, disk usage

## Troubleshooting

### Common Issues

#### Container Won't Start

```bash
# Check container logs
docker logs iris-api-prod

# Check container status
docker ps -a

# Inspect container configuration
docker inspect iris-api-prod
```

#### Health Check Failures

```bash
# Test health endpoint manually
curl -v http://localhost:8000/health

# Check if model files exist
docker exec iris-api-prod ls -la /app/artifacts/

# Check database connectivity
docker exec iris-api-prod sqlite3 /app/logs.db ".tables"
```

#### Performance Issues

```bash
# Monitor resource usage
docker stats iris-api-prod

# Check application logs
docker logs iris-api-prod --tail 100

# Test API performance
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/predict
```

#### Network Issues

```bash
# Check port binding
docker port iris-api-prod

# Test network connectivity
docker exec iris-api-prod curl http://localhost:8000/health

# Check firewall rules
sudo ufw status
```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
# Start container in debug mode
docker run -d \
  --name iris-api-debug \
  -p 8000:8000 \
  -e DEBUG=true \
  -e LOG_LEVEL=DEBUG \
  your-username/iris-classifier-api:latest

# View debug logs
docker logs iris-api-debug -f
```

### Log Analysis

```bash
# View application logs
docker logs iris-api-prod --tail 100 -f

# View structured logs from database
docker exec iris-api-prod sqlite3 /app/logs.db \
  "SELECT * FROM prediction_logs ORDER BY timestamp DESC LIMIT 10;"

# Export logs for analysis
docker exec iris-api-prod sqlite3 /app/logs.db \
  ".mode csv" ".output /tmp/logs.csv" \
  "SELECT * FROM prediction_logs;"
```

### Performance Tuning

#### Container Resources

```bash
# Limit container resources
docker run -d \
  --name iris-api-prod \
  --memory=1g \
  --cpus=1.0 \
  --restart unless-stopped \
  -p 8000:8000 \
  your-username/iris-classifier-api:latest
```

#### Application Tuning

```bash
# Increase worker processes
docker run -d \
  --name iris-api-prod \
  -p 8000:8000 \
  your-username/iris-classifier-api:latest \
  uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Security Considerations

### Container Security

- Run as non-root user
- Use minimal base images
- Regular security updates
- Vulnerability scanning

### Network Security

- Use HTTPS in production
- Implement rate limiting
- Configure CORS properly
- Use reverse proxy (nginx/traefik)

### Data Security

- Encrypt sensitive data
- Secure database connections
- Implement input validation
- Log security events

## Backup and Recovery

### Data Backup

```bash
# Backup logs database
docker exec iris-api-prod sqlite3 /app/logs.db ".backup /tmp/logs_backup.db"
docker cp iris-api-prod:/tmp/logs_backup.db ./backups/

# Backup application data
docker cp iris-api-prod:/app/data ./backups/data-$(date +%Y%m%d)
```

### Disaster Recovery

1. **Image Recovery**: Pull from Docker Hub
2. **Data Recovery**: Restore from backups
3. **Configuration Recovery**: Use infrastructure as code
4. **Service Recovery**: Automated health checks and restarts

This deployment guide provides comprehensive coverage of deployment scenarios and operational procedures for the Iris Classification API.