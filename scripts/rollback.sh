#!/bin/bash

# Rollback script for Iris Classification API
# This script helps rollback to a previous version in case of deployment issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Configuration
DOCKER_HUB_USERNAME=${DOCKER_HUB_USERNAME:-"your-dockerhub-username"}
IMAGE_NAME=${IMAGE_NAME:-"$DOCKER_HUB_USERNAME/iris-classifier-api"}
CONTAINER_NAME=${CONTAINER_NAME:-"iris-api-prod"}
BACKUP_CONTAINER_NAME="${CONTAINER_NAME}-backup"
PORT=${PORT:-"8000"}

# Parse command line arguments
ROLLBACK_TAG=""
LIST_VERSIONS=false
FORCE_ROLLBACK=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --tag)
            ROLLBACK_TAG="$2"
            shift 2
            ;;
        --list)
            LIST_VERSIONS=true
            shift
            ;;
        --force)
            FORCE_ROLLBACK=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --tag TAG        Tag/version to rollback to"
            echo "  --list           List available image tags"
            echo "  --force          Force rollback without confirmation"
            echo "  --help           Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --list                    # List available versions"
            echo "  $0 --tag v1.2.0             # Rollback to specific version"
            echo "  $0 --tag latest --force     # Force rollback to latest"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "🔄 Iris Classification API Rollback Tool"
echo "========================================"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running"
    exit 1
fi

# List available versions if requested
if [ "$LIST_VERSIONS" = true ]; then
    print_info "Fetching available image tags from Docker Hub..."
    
    # Try to get tags from Docker Hub API (requires curl and jq)
    if command -v curl &> /dev/null && command -v jq &> /dev/null; then
        REPO_NAME=$(echo $IMAGE_NAME | cut -d'/' -f2)
        USERNAME=$(echo $IMAGE_NAME | cut -d'/' -f1)
        
        echo ""
        echo "📦 Available tags for $IMAGE_NAME:"
        echo "================================================"
        
        curl -s "https://registry.hub.docker.com/v2/repositories/$USERNAME/$REPO_NAME/tags/" | \
        jq -r '.results[] | "\(.name) - \(.last_updated | split("T")[0])"' | \
        head -20
        
        echo ""
        print_info "Showing latest 20 tags. Use --tag <TAG> to rollback to a specific version."
    else
        print_warning "curl and jq are required to list remote tags"
        print_info "You can check available tags at: https://hub.docker.com/r/$IMAGE_NAME/tags"
    fi
    
    # Show local images
    echo ""
    echo "🏠 Local images:"
    echo "==============="
    docker images $IMAGE_NAME --format "table {{.Tag}}\t{{.CreatedAt}}\t{{.Size}}" | head -10
    
    exit 0
fi

# Check if rollback tag is provided
if [ -z "$ROLLBACK_TAG" ]; then
    print_error "Rollback tag not specified"
    echo "Use --tag <TAG> to specify the version to rollback to"
    echo "Use --list to see available versions"
    exit 1
fi

ROLLBACK_IMAGE="$IMAGE_NAME:$ROLLBACK_TAG"

print_info "Rollback target: $ROLLBACK_IMAGE"
print_info "Current container: $CONTAINER_NAME"

# Check if current container exists
if ! docker ps -a --format 'table {{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
    print_error "Current container '$CONTAINER_NAME' not found"
    print_info "Available containers:"
    docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
    exit 1
fi

# Get current image info
CURRENT_IMAGE=$(docker inspect $CONTAINER_NAME --format='{{.Config.Image}}' 2>/dev/null || echo "unknown")
print_info "Current image: $CURRENT_IMAGE"

# Confirmation prompt (unless forced)
if [ "$FORCE_ROLLBACK" != true ]; then
    echo ""
    print_warning "This will rollback from:"
    echo "  Current: $CURRENT_IMAGE"
    echo "  To:      $ROLLBACK_IMAGE"
    echo ""
    read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Rollback cancelled"
        exit 0
    fi
fi

echo ""
print_info "Starting rollback process..."

# Step 1: Pull the rollback image
print_info "Pulling rollback image: $ROLLBACK_IMAGE"
if ! docker pull $ROLLBACK_IMAGE; then
    print_error "Failed to pull rollback image: $ROLLBACK_IMAGE"
    print_info "Make sure the tag exists and you have access to it"
    exit 1
fi

print_status "Rollback image pulled successfully"

# Step 2: Create backup of current container
print_info "Creating backup of current container..."
if docker ps --format 'table {{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
    # Container is running, commit it to a backup image
    BACKUP_IMAGE="$IMAGE_NAME:backup-$(date +%Y%m%d-%H%M%S)"
    docker commit $CONTAINER_NAME $BACKUP_IMAGE
    print_status "Current state backed up as: $BACKUP_IMAGE"
fi

# Step 3: Stop current container
print_info "Stopping current container: $CONTAINER_NAME"
docker stop $CONTAINER_NAME || true

# Step 4: Rename current container as backup
print_info "Renaming current container to backup..."
docker rename $CONTAINER_NAME $BACKUP_CONTAINER_NAME || true

# Step 5: Start new container with rollback image
print_info "Starting new container with rollback image..."

# Get the original run configuration (simplified)
ORIGINAL_PORTS=$(docker port $BACKUP_CONTAINER_NAME 2>/dev/null | grep "8000/tcp" | cut -d' ' -f3 | cut -d':' -f2 || echo "$PORT")

docker run -d \
  --name $CONTAINER_NAME \
  --restart unless-stopped \
  -p $ORIGINAL_PORTS:8000 \
  -e LOG_LEVEL=INFO \
  -e DEBUG=false \
  -e USE_MLFLOW_REGISTRY=false \
  -e DATABASE_URL=sqlite:///./logs.db \
  -e LOG_PREDICTIONS=true \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/artifacts:/app/artifacts \
  $ROLLBACK_IMAGE

print_status "New container started with rollback image"

# Step 6: Health check
print_info "Performing health check..."
sleep 15

HEALTH_URL="http://localhost:$ORIGINAL_PORTS/health"
MAX_RETRIES=10

for i in $(seq 1 $MAX_RETRIES); do
    if curl -f -s $HEALTH_URL > /dev/null 2>&1; then
        print_status "Health check passed!"
        break
    fi
    
    if [ $i -eq $MAX_RETRIES ]; then
        print_error "Health check failed after rollback!"
        print_error "Rolling back to previous version..."
        
        # Emergency rollback
        docker stop $CONTAINER_NAME || true
        docker rm $CONTAINER_NAME || true
        docker rename $BACKUP_CONTAINER_NAME $CONTAINER_NAME || true
        docker start $CONTAINER_NAME || true
        
        print_error "Rollback failed! Previous container restored."
        exit 1
    fi
    
    print_info "Health check attempt $i/$MAX_RETRIES, retrying..."
    sleep 10
done

# Step 7: Test critical functionality
print_info "Testing critical functionality..."
PREDICTION_URL="http://localhost:$ORIGINAL_PORTS/predict"
PREDICTION_DATA='{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'

if curl -f -s -X POST "$PREDICTION_URL" \
   -H "Content-Type: application/json" \
   -d "$PREDICTION_DATA" > /dev/null 2>&1; then
    print_status "Prediction endpoint working correctly"
else
    print_warning "Prediction endpoint test failed (may need investigation)"
fi

# Success summary
echo ""
print_status "🎉 Rollback completed successfully!"
echo "=================================="
print_status "Rolled back to: $ROLLBACK_IMAGE"
print_status "Container: $CONTAINER_NAME"
print_status "Backup container: $BACKUP_CONTAINER_NAME"
echo ""
echo "📍 Service endpoints:"
echo "  🌐 API:     http://localhost:$ORIGINAL_PORTS"
echo "  🏥 Health:  http://localhost:$ORIGINAL_PORTS/health"
echo "  📚 Docs:    http://localhost:$ORIGINAL_PORTS/docs"
echo ""
echo "🛠️  Post-rollback actions:"
echo "  Monitor logs:     docker logs $CONTAINER_NAME -f"
echo "  Remove backup:    docker rm $BACKUP_CONTAINER_NAME"
echo "  Test thoroughly:  Run your test suite"
echo ""

# Quick health status
print_info "Current service status:"
curl -s $HEALTH_URL | python -m json.tool 2>/dev/null || echo "Service status check failed"

print_status "Rollback process completed!"