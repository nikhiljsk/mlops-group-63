# Deployment Automation

This directory contains comprehensive deployment automation for the Iris Classification API, supporting multiple deployment targets and environments.

## 📁 Directory Structure

```
deploy/
├── README.md                    # This file
├── deploy-manager.py           # Advanced Python deployment manager
├── k8s-deploy.sh              # Kubernetes deployment script
├── config/
│   └── environments.yml       # Environment configurations
├── kubernetes/                # Kubernetes manifests
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── deployment.yaml
│   ├── storage.yaml
│   └── monitoring.yaml
├── terraform/                 # Infrastructure as Code (future)
├── ansible/                   # Configuration management (future)
└── logs/                      # Deployment logs
```

## 🚀 Deployment Options

### 1. Docker Deployment (Recommended for Development/Testing)

#### Using Python Deployment Manager

```bash
# List available environments
./deploy/deploy-manager.py list

# Deploy to development environment
./deploy/deploy-manager.py deploy development

# Deploy to staging with custom configuration
./deploy/deploy-manager.py deploy staging --config deploy/config/environments.yml

# Deploy to production (requires confirmation)
./deploy/deploy-manager.py deploy production

# Force deployment without confirmation
./deploy/deploy-manager.py deploy production --force

# Skip post-deployment tests
./deploy/deploy-manager.py deploy staging --skip-tests
```

#### Using Shell Scripts (Legacy)

```bash
# Basic deployment
./scripts/deploy.sh

# Custom deployment
./scripts/deploy.sh --image myuser/iris-classifier-api --tag v1.0.0 --port 8080
```

### 2. Kubernetes Deployment (Recommended for Production)

#### Prerequisites

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Configure cluster access
kubectl config use-context your-cluster-context

# Set required environment variables
export DOCKER_HUB_USERNAME=your-dockerhub-username
export IMAGE_TAG=latest
export DOMAIN=iris-api.yourdomain.com
```

#### Deployment Commands

```bash
# Basic Kubernetes deployment
./deploy/k8s-deploy.sh

# Custom deployment with specific image tag
./deploy/k8s-deploy.sh --image-tag v1.0.0 --domain api.mycompany.com

# Skip monitoring stack
./deploy/k8s-deploy.sh --skip-monitoring

# Dry run (show what would be deployed)
./deploy/k8s-deploy.sh --dry-run

# Skip health checks
./deploy/k8s-deploy.sh --skip-health
```

#### Manual Kubernetes Deployment

```bash
# Apply all manifests
kubectl apply -f deploy/kubernetes/

# Check deployment status
kubectl get all -n iris-api

# Port forward for testing
kubectl port-forward service/iris-api-service 8080:8000 -n iris-api
```

## 🔧 Configuration Management

### Environment Configuration

The `deploy/config/environments.yml` file defines environment-specific settings:

- **Development**: Local development with hot reload
- **Staging**: Pre-production testing environment
- **Production**: Full production deployment with monitoring

### Customizing Environments

```yaml
environments:
  my-custom-env:
    name: "My Custom Environment"
    description: "Custom deployment environment"
    docker:
      image_tag: "custom"
      container_name: "iris-api-custom"
      port: 8002
      restart_policy: "unless-stopped"
    environment_vars:
      DEBUG: "false"
      LOG_LEVEL: "INFO"
      # ... other variables
    volumes:
      - "./logs:/app/logs"
      - "./data:/app/data:ro"
    monitoring:
      prometheus: true
      grafana: true
```

## 📊 Monitoring and Observability

### Included Monitoring Stack

- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization dashboards
- **Application Metrics**: Custom API and ML metrics
- **Health Checks**: Automated health monitoring
- **Alerting**: Configurable alert rules

### Accessing Monitoring

#### Docker Deployment
```bash
# Prometheus
http://localhost:9090

# Grafana
http://localhost:3000
# Login: admin/admin
```

#### Kubernetes Deployment
```bash
# Port forward Prometheus
kubectl port-forward service/prometheus-service 9090:9090 -n iris-api

# Port forward Grafana
kubectl port-forward service/grafana-service 3000:3000 -n iris-api
```

### Key Metrics

- `http_requests_total`: Total HTTP requests
- `http_request_duration_seconds`: Request latency
- `ml_predictions_total`: Total ML predictions
- `ml_prediction_confidence`: Prediction confidence scores
- `ml_prediction_errors_total`: Prediction errors

## 🔒 Security Considerations

### Container Security

- **Non-root user**: Containers run as non-root user (UID 1000)
- **Read-only filesystem**: Root filesystem is read-only
- **No new privileges**: Prevents privilege escalation
- **Minimal base image**: Uses slim Python base image
- **Security scanning**: Trivy vulnerability scanning in CI/CD

### Kubernetes Security

- **Network policies**: Restrict pod-to-pod communication
- **RBAC**: Role-based access control
- **Pod security policies**: Enforce security standards
- **Secrets management**: Secure handling of sensitive data
- **TLS termination**: HTTPS with Let's Encrypt certificates

### Best Practices

1. **Use specific image tags** instead of `latest`
2. **Implement resource limits** to prevent resource exhaustion
3. **Enable security scanning** in CI/CD pipelines
4. **Rotate secrets regularly**
5. **Monitor security events** and alerts
6. **Keep base images updated**

## 🔄 Rollback Procedures

### Docker Rollback

```bash
# List available versions
./scripts/rollback.sh --list

# Rollback to specific version
./scripts/rollback.sh --tag v1.0.0

# Force rollback
./scripts/rollback.sh --tag previous-version --force
```

### Kubernetes Rollback

```bash
# Check rollout history
kubectl rollout history deployment/iris-api-deployment -n iris-api

# Rollback to previous version
kubectl rollout undo deployment/iris-api-deployment -n iris-api

# Rollback to specific revision
kubectl rollout undo deployment/iris-api-deployment --to-revision=2 -n iris-api

# Check rollout status
kubectl rollout status deployment/iris-api-deployment -n iris-api
```

## 🧪 Testing Deployments

### Automated Tests

The deployment automation includes comprehensive testing:

1. **Health checks**: Verify service is responding
2. **Functional tests**: Test prediction endpoints
3. **Performance tests**: Basic load testing
4. **Integration tests**: End-to-end functionality

### Manual Testing

```bash
# Health check
curl http://localhost:8000/health

# Prediction test
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'

# Batch prediction test
curl -X POST "http://localhost:8000/predict/batch" \
  -H "Content-Type: application/json" \
  -d '{"samples": [{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}]}'

# Model info
curl http://localhost:8000/model/info

# Metrics
curl http://localhost:8000/metrics
```

## 🚨 Troubleshooting

### Common Issues

#### Container Won't Start

```bash
# Check container logs
docker logs iris-api-prod

# Check container status
docker ps -a

# Inspect container
docker inspect iris-api-prod
```

#### Kubernetes Pod Issues

```bash
# Check pod status
kubectl get pods -n iris-api

# View pod logs
kubectl logs -f deployment/iris-api-deployment -n iris-api

# Describe pod for events
kubectl describe pod <pod-name> -n iris-api

# Execute into pod
kubectl exec -it <pod-name> -n iris-api -- /bin/bash
```

#### Health Check Failures

```bash
# Test health endpoint
curl -v http://localhost:8000/health

# Check if model files exist
ls -la artifacts/

# Check database connectivity
sqlite3 logs.db ".tables"
```

#### Performance Issues

```bash
# Monitor resource usage
docker stats iris-api-prod

# Check Kubernetes resource usage
kubectl top pods -n iris-api

# View detailed metrics
curl http://localhost:8000/metrics
```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# Docker deployment with debug
docker run -d \
  --name iris-api-debug \
  -p 8000:8000 \
  -e DEBUG=true \
  -e LOG_LEVEL=DEBUG \
  your-username/iris-classifier-api:latest

# Kubernetes debug
kubectl set env deployment/iris-api-deployment DEBUG=true LOG_LEVEL=DEBUG -n iris-api
```

## 📈 Scaling

### Docker Scaling

```bash
# Use Docker Compose for multiple replicas
docker-compose up --scale iris-api=3

# Use load balancer (nginx, traefik, etc.)
```

### Kubernetes Scaling

```bash
# Manual scaling
kubectl scale deployment iris-api-deployment --replicas=5 -n iris-api

# Horizontal Pod Autoscaler
kubectl autoscale deployment iris-api-deployment --cpu-percent=70 --min=2 --max=10 -n iris-api

# Check HPA status
kubectl get hpa -n iris-api
```

## 🔧 Customization

### Adding New Environments

1. Edit `deploy/config/environments.yml`
2. Add new environment configuration
3. Test with deployment manager:
   ```bash
   ./deploy/deploy-manager.py deploy your-new-env
   ```

### Custom Kubernetes Resources

1. Add new YAML files to `deploy/kubernetes/`
2. Update `deploy/k8s-deploy.sh` to include new resources
3. Test deployment:
   ```bash
   ./deploy/k8s-deploy.sh --dry-run
   ```

### Environment Variables

Common environment variables for customization:

```bash
# Docker configuration
DOCKER_HUB_USERNAME=your-username
IMAGE_TAG=latest

# Application configuration
DEBUG=false
LOG_LEVEL=INFO
USE_MLFLOW_REGISTRY=false
DATABASE_URL=sqlite:///./logs.db

# Kubernetes configuration
NAMESPACE=iris-api
DOMAIN=iris-api.yourdomain.com
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [MLOps Best Practices](https://ml-ops.org/)

## 🤝 Contributing

To contribute to the deployment automation:

1. Fork the repository
2. Create a feature branch
3. Add your improvements
4. Test thoroughly
5. Submit a pull request

## 📄 License

This deployment automation is part of the Iris Classification API project and follows the same license terms.