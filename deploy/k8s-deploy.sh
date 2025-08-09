#!/bin/bash

# Kubernetes Deployment Script for Iris Classification API
# Handles deployment to Kubernetes clusters with monitoring and security

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="iris-api"
APP_NAME="iris-classifier"
DOCKER_HUB_USERNAME=${DOCKER_HUB_USERNAME:-"your-username"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
DOMAIN=${DOMAIN:-"iris-api.yourdomain.com"}

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

print_header() {
    echo -e "${PURPLE}$1${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    print_info "Checking Kubernetes deployment prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    print_status "kubectl is available"
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        print_info "Make sure you have a valid kubeconfig and cluster access"
        exit 1
    fi
    print_status "Connected to Kubernetes cluster"
    
    # Check Docker Hub username
    if [ "$DOCKER_HUB_USERNAME" = "your-username" ]; then
        print_error "Please set DOCKER_HUB_USERNAME environment variable"
        print_info "Example: export DOCKER_HUB_USERNAME=your-dockerhub-username"
        exit 1
    fi
    print_status "Docker Hub username configured: $DOCKER_HUB_USERNAME"
}

# Function to create namespace
create_namespace() {
    print_info "Creating namespace: $NAMESPACE"
    
    if kubectl get namespace $NAMESPACE &> /dev/null; then
        print_warning "Namespace $NAMESPACE already exists"
    else
        kubectl apply -f deploy/kubernetes/namespace.yaml
        print_status "Namespace created successfully"
    fi
}

# Function to update image references
update_image_references() {
    print_info "Updating image references..."
    
    # Create temporary deployment file with updated image
    sed "s|your-username/iris-classifier-api:latest|$DOCKER_HUB_USERNAME/iris-classifier-api:$IMAGE_TAG|g" \
        deploy/kubernetes/deployment.yaml > /tmp/deployment-updated.yaml
    
    # Update domain in ingress
    sed -i "s|iris-api.yourdomain.com|$DOMAIN|g" /tmp/deployment-updated.yaml
    
    print_status "Image references updated"
}

# Function to deploy storage
deploy_storage() {
    print_info "Deploying persistent storage..."
    
    kubectl apply -f deploy/kubernetes/storage.yaml
    
    # Wait for PVCs to be bound
    print_info "Waiting for persistent volume claims to be bound..."
    kubectl wait --for=condition=Bound pvc/iris-api-logs-pvc -n $NAMESPACE --timeout=300s
    kubectl wait --for=condition=Bound pvc/iris-api-data-pvc -n $NAMESPACE --timeout=300s
    kubectl wait --for=condition=Bound pvc/iris-api-artifacts-pvc -n $NAMESPACE --timeout=300s
    
    print_status "Storage deployed successfully"
}

# Function to deploy configuration
deploy_config() {
    print_info "Deploying configuration..."
    
    kubectl apply -f deploy/kubernetes/configmap.yaml
    print_status "Configuration deployed successfully"
}

# Function to deploy application
deploy_application() {
    print_info "Deploying application..."
    
    kubectl apply -f /tmp/deployment-updated.yaml
    
    # Wait for deployment to be ready
    print_info "Waiting for deployment to be ready..."
    kubectl wait --for=condition=Available deployment/iris-api-deployment -n $NAMESPACE --timeout=600s
    
    print_status "Application deployed successfully"
}

# Function to deploy monitoring
deploy_monitoring() {
    print_info "Deploying monitoring stack..."
    
    kubectl apply -f deploy/kubernetes/monitoring.yaml
    
    # Wait for monitoring deployments
    print_info "Waiting for monitoring components to be ready..."
    kubectl wait --for=condition=Available deployment/prometheus-deployment -n $NAMESPACE --timeout=300s
    kubectl wait --for=condition=Available deployment/grafana-deployment -n $NAMESPACE --timeout=300s
    
    print_status "Monitoring stack deployed successfully"
}

# Function to run health checks
run_health_checks() {
    print_info "Running health checks..."
    
    # Get service endpoint
    SERVICE_IP=$(kubectl get service iris-api-service -n $NAMESPACE -o jsonpath='{.spec.clusterIP}')
    
    # Port forward for testing
    print_info "Setting up port forwarding for health checks..."
    kubectl port-forward service/iris-api-service 8080:8000 -n $NAMESPACE &
    PORT_FORWARD_PID=$!
    
    # Wait for port forward to be ready
    sleep 10
    
    # Health check
    if curl -f http://localhost:8080/health &> /dev/null; then
        print_status "Health check passed"
    else
        print_error "Health check failed"
        kill $PORT_FORWARD_PID 2>/dev/null || true
        exit 1
    fi
    
    # Prediction test
    if curl -f -X POST "http://localhost:8080/predict" \
       -H "Content-Type: application/json" \
       -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}' &> /dev/null; then
        print_status "Prediction endpoint test passed"
    else
        print_error "Prediction endpoint test failed"
        kill $PORT_FORWARD_PID 2>/dev/null || true
        exit 1
    fi
    
    # Clean up port forward
    kill $PORT_FORWARD_PID 2>/dev/null || true
    
    print_status "All health checks passed"
}

# Function to display deployment summary
display_summary() {
    print_header "🎉 Kubernetes Deployment Summary"
    echo "=================================="
    
    echo "Namespace: $NAMESPACE"
    echo "Application: $APP_NAME"
    echo "Image: $DOCKER_HUB_USERNAME/iris-classifier-api:$IMAGE_TAG"
    echo "Domain: $DOMAIN"
    echo ""
    
    print_info "Deployed Resources:"
    kubectl get all -n $NAMESPACE
    echo ""
    
    print_info "Persistent Volume Claims:"
    kubectl get pvc -n $NAMESPACE
    echo ""
    
    print_info "Ingress:"
    kubectl get ingress -n $NAMESPACE
    echo ""
    
    print_header "📍 Access Information:"
    echo "External URL: https://$DOMAIN"
    echo "Health Check: https://$DOMAIN/health"
    echo "API Docs: https://$DOMAIN/docs"
    echo "Metrics: https://$DOMAIN/metrics"
    echo ""
    
    print_header "🛠️  Management Commands:"
    echo "View pods:           kubectl get pods -n $NAMESPACE"
    echo "View logs:           kubectl logs -f deployment/iris-api-deployment -n $NAMESPACE"
    echo "Scale deployment:    kubectl scale deployment iris-api-deployment --replicas=5 -n $NAMESPACE"
    echo "Port forward:        kubectl port-forward service/iris-api-service 8080:8000 -n $NAMESPACE"
    echo "Delete deployment:   kubectl delete namespace $NAMESPACE"
    echo ""
    
    print_header "📊 Monitoring:"
    echo "Prometheus:          kubectl port-forward service/prometheus-service 9090:9090 -n $NAMESPACE"
    echo "Grafana:             kubectl port-forward service/grafana-service 3000:3000 -n $NAMESPACE"
    echo "Grafana Login:       admin/admin"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --image-tag TAG     Docker image tag (default: latest)"
    echo "  --domain DOMAIN     Domain for ingress (default: iris-api.yourdomain.com)"
    echo "  --skip-monitoring   Skip monitoring stack deployment"
    echo "  --skip-health       Skip health checks"
    echo "  --dry-run          Show what would be deployed without applying"
    echo "  --help             Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  DOCKER_HUB_USERNAME  Docker Hub username (required)"
    echo "  IMAGE_TAG           Docker image tag"
    echo "  DOMAIN              Domain for ingress"
    echo ""
    echo "Examples:"
    echo "  DOCKER_HUB_USERNAME=myuser $0"
    echo "  DOCKER_HUB_USERNAME=myuser $0 --image-tag v1.0.0 --domain api.mycompany.com"
}

# Parse command line arguments
SKIP_MONITORING=false
SKIP_HEALTH=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --image-tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --skip-monitoring)
            SKIP_MONITORING=true
            shift
            ;;
        --skip-health)
            SKIP_HEALTH=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main deployment process
main() {
    print_header "🚀 Kubernetes Deployment for Iris Classification API"
    echo "====================================================="
    
    # Check prerequisites
    check_prerequisites
    
    # Show configuration
    print_info "Deployment Configuration:"
    echo "  Namespace: $NAMESPACE"
    echo "  Image: $DOCKER_HUB_USERNAME/iris-classifier-api:$IMAGE_TAG"
    echo "  Domain: $DOMAIN"
    echo "  Skip Monitoring: $SKIP_MONITORING"
    echo "  Skip Health Checks: $SKIP_HEALTH"
    echo "  Dry Run: $DRY_RUN"
    echo ""
    
    if [ "$DRY_RUN" = true ]; then
        print_warning "DRY RUN MODE - No changes will be applied"
        echo ""
    fi
    
    # Confirmation
    read -p "Proceed with deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Deployment cancelled"
        exit 0
    fi
    
    if [ "$DRY_RUN" = false ]; then
        # Execute deployment steps
        create_namespace
        update_image_references
        deploy_storage
        deploy_config
        deploy_application
        
        if [ "$SKIP_MONITORING" = false ]; then
            deploy_monitoring
        fi
        
        if [ "$SKIP_HEALTH" = false ]; then
            run_health_checks
        fi
        
        display_summary
        
        print_status "🎉 Deployment completed successfully!"
    else
        print_info "Dry run completed - no changes were made"
    fi
    
    # Cleanup temporary files
    rm -f /tmp/deployment-updated.yaml
}

# Run main function
main