#!/bin/bash

# Production deployment script for Iris Classification API
# This script can be used for local deployment or in CI/CD pipelines

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Configuration with defaults
DOCKER_HUB_USERNAME=${DOCKER_HUB_USERNAME:-"your-dockerhub-username"}
IMAGE_NAME=${IMAGE_NAME:-"$DOCKER_HUB_USERNAME/iris-classifier-api"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
CONTAINER_NAME=${CONTAINER_NAME:-"iris-api-prod"}
PORT=${PORT:-"8000"}
ENVIRONMENT=${ENVIRONMENT:-"production"}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --image)
            IMAGE_NAME="$2"
            shift 2
            ;;
        --tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --container-name)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --image IMAGE_NAME        Docker image name (default: $DOCKER_HUB_USERNAME/iris-classifier-api)"
            echo "  --tag TAG                 Image tag (default: latest)"
            echo "  --port PORT               Host port to bind (default: 8000)"
            echo "  --container-name NAME     Container name (default: iris-api-prod)"
            echo "  --environment ENV         Environment (default: production)"
            echo "  --help                    Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  DOCKER_HUB_USERNAME       Docker Hub username"
            echo "  IMAGE_NAME                Full image name"
            echo "  IMAGE_TAG                 Image tag"
            echo "  CONTAINER_NAME            Container name"
            echo "  PORT                      Host port"
            echo "  ENVIRONMENT               Deployment environment"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

FULL_IMAGE_NAME="$IMAGE_NAME:$IMAGE_TAG"

echo "🚀 Starting deployment of Iris Classification API"
echo "=================================================="
print_info "Image: $FULL_IMAGE_NAME"
print_info "Container: $CONTAINER_NAME"
print_info "Port: $PORT"
print_info "Environment: $ENVIRONMENT"
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running"
    exit 1
fi

print_status "Docker is available and running"

# Pull the latest image
print_info "Pulling latest image: $FULL_IMAGE_NAME"
if ! docker pull $FULL_IMAGE_NAME; then
    print_error "Failed to pull image: $FULL_IMAGE_NAME"
    print_info "Make sure the image exists and you have access to it"
    exit 1
fi

print_status "Image pulled successfully"

# Stop and remove existing container if it exists
if docker ps -a --format 'table {{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
    print_info "Stopping existing container: $CONTAINER_NAME"
    docker stop $CONTAINER_NAME || true
    
    print_info "Removing existing container: $CONTAINER_NAME"
    docker rm $CONTAINER_NAME || true
    
    print_status "Existing container removed"
fi

# Create necessary directories
print_info "Creating necessary directories..."
mkdir -p logs data artifacts

# Start new container
print_info "Starting new container: $CONTAINER_NAME"

# Set environment-specific configuration
ENV_VARS=""
if [ "$ENVIRONMENT" = "production" ]; then
    ENV_VARS="-e LOG_LEVEL=INFO -e DEBUG=false"
elif [ "$ENVIRONMENT" = "staging" ]; then
    ENV_VARS="-e LOG_LEVEL=DEBUG -e DEBUG=true"
else
    ENV_VARS="-e LOG_LEVEL=DEBUG -e DEBUG=true"
fi

docker run -d \
  --name $CONTAINER_NAME \
  --restart unless-stopped \
  -p $PORT:8000 \
  $ENV_VARS \
  -e USE_MLFLOW_REGISTRY=false \
  -e DATABASE_URL=sqlite:///./logs.db \
  -e LOG_PREDICTIONS=true \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/artifacts:/app/artifacts \
  $FULL_IMAGE_NAME

print_status "Container started successfully"

# Wait for container to be ready
print_info "Waiting for container to be ready..."
sleep 10

# Health check with retries
print_info "Performing health check..."
HEALTH_CHECK_URL="http://localhost:$PORT/health"
MAX_RETRIES=12
RETRY_INTERVAL=10

for i in $(seq 1 $MAX_RETRIES); do
    if curl -f -s $HEALTH_CHECK_URL > /dev/null 2>&1; then
        print_status "Health check passed!"
        break
    fi
    
    if [ $i -eq $MAX_RETRIES ]; then
        print_error "Health check failed after $MAX_RETRIES attempts"
        print_info "Container logs:"
        docker logs $CONTAINER_NAME --tail 50
        exit 1
    fi
    
    print_info "Health check attempt $i/$MAX_RETRIES failed, retrying in ${RETRY_INTERVAL}s..."
    sleep $RETRY_INTERVAL
done

# Run post-deployment tests
print_info "Running post-deployment tests..."

# Test prediction endpoint
PREDICTION_URL="http://localhost:$PORT/predict"
PREDICTION_DATA='{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'

if curl -f -s -X POST "$PREDICTION_URL" \
   -H "Content-Type: application/json" \
   -d "$PREDICTION_DATA" > /dev/null 2>&1; then
    print_status "Prediction endpoint test passed"
else
    print_error "Prediction endpoint test failed"
    exit 1
fi

# Test metrics endpoint
METRICS_URL="http://localhost:$PORT/metrics"
if curl -f -s $METRICS_URL > /dev/null 2>&1; then
    print_status "Metrics endpoint test passed"
else
    print_warning "Metrics endpoint test failed (non-critical)"
fi

# Display deployment summary
echo ""
echo "🎉 Deployment completed successfully!"
echo "====================================="
print_status "Container: $CONTAINER_NAME"
print_status "Image: $FULL_IMAGE_NAME"
print_status "Port: $PORT"
echo ""
echo "📍 Available endpoints:"
echo "  🌐 API Base:     http://localhost:$PORT"
echo "  🏥 Health:       http://localhost:$PORT/health"
echo "  📊 Prediction:   http://localhost:$PORT/predict"
echo "  📈 Metrics:      http://localhost:$PORT/metrics"
echo "  📚 API Docs:     http://localhost:$PORT/docs"
echo "  🔍 Redoc:        http://localhost:$PORT/redoc"
echo ""
echo "🛠️  Management commands:"
echo "  View logs:       docker logs $CONTAINER_NAME"
echo "  Stop container:  docker stop $CONTAINER_NAME"
echo "  Start container: docker start $CONTAINER_NAME"
echo "  Remove:          docker stop $CONTAINER_NAME && docker rm $CONTAINER_NAME"
echo ""
echo "📊 Quick health check:"
curl -s $HEALTH_CHECK_URL | python -m json.tool 2>/dev/null || echo "Health endpoint not responding"
echo ""

print_status "Deployment script completed successfully!"