# Docker Setup Guide

This guide explains how to run the Iris Classification API using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Make (optional, for convenience commands)

## Quick Start

### 1. Build and Start Services

```bash
# Using Make (recommended)
make up

# Or using Docker Compose directly
docker-compose up -d
```

### 2. Check Service Health

```bash
# Check all services
make health

# Or manually
curl http://localhost:8000/health
curl http://localhost:5000/health
```

### 3. Test the API

```bash
# Make a prediction
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "sepal_length": 5.1,
    "sepal_width": 3.5,
    "petal_length": 1.4,
    "petal_width": 0.2
  }'
```

## Available Services

| Service | Port | Description |
|---------|------|-------------|
| iris-api | 8000 | Main API service |
| mlflow | 5000 | MLflow tracking server |
| prometheus | 9090 | Metrics collection (with monitoring profile) |
| grafana | 3000 | Visualization dashboard (with monitoring profile) |

## Development Mode

For development with hot reload:

```bash
# Start development environment
make dev

# Or with Docker Compose
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## Monitoring Stack

To start with full monitoring capabilities:

```bash
# Start with monitoring
make monitoring

# Access services
# - API: http://localhost:8000
# - MLflow: http://localhost:5000
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin)
```

## Environment Variables

Key environment variables for configuration:

| Variable | Default | Description |
|----------|---------|-------------|
| DEBUG | false | Enable debug mode |
| LOG_LEVEL | INFO | Logging level |
| MLFLOW_TRACKING_URI | http://mlflow:5000 | MLflow server URL |
| USE_MLFLOW_REGISTRY | true | Use MLflow model registry |
| DATABASE_URL | sqlite:///./logs.db | Database connection string |

## Volume Mounts

- `./artifacts` - Model artifacts
- `./data` - Training data
- `./logs` - Application logs
- `mlflow_data` - MLflow experiments and models
- `prometheus_data` - Prometheus metrics data
- `grafana_data` - Grafana dashboards and config

## Useful Commands

```bash
# View logs
make logs                    # All services
make api-logs               # API only
make mlflow-logs            # MLflow only

# Restart services
make restart-api            # Restart API only
docker-compose restart     # Restart all

# Execute shell in container
make shell                  # API container
docker-compose exec mlflow /bin/bash  # MLflow container

# Clean up
make clean                  # Remove everything
docker-compose down         # Stop services only
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change ports in docker-compose.yml if needed
2. **Permission issues**: Ensure Docker has access to mounted directories
3. **Memory issues**: Increase Docker memory allocation for ML workloads

### Health Checks

All services include health checks. Check status with:

```bash
docker-compose ps
```

### Logs

View detailed logs for debugging:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f iris-api
```

## Production Deployment

For production deployment:

1. Use environment-specific docker-compose files
2. Configure proper secrets management
3. Set up reverse proxy (nginx/traefik)
4. Configure monitoring and alerting
5. Set up backup strategies for volumes

Example production override:

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  iris-api:
    environment:
      - DEBUG=false
      - LOG_LEVEL=INFO
    restart: always
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```