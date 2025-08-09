#!/bin/bash

# Universal Deployment Wrapper for Iris Classification API
# This script provides a unified interface for all deployment methods

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

print_header() {
    echo -e "${PURPLE}$1${NC}"
}

# Function to show usage
show_usage() {
    echo -e "${CYAN}🚀 Iris Classification API - Universal Deployment Tool${NC}"
    echo "============================================================"
    echo ""
    echo "Usage: $0 <deployment-type> [options]"
    echo ""
    echo "Deployment Types:"
    echo "  docker      Deploy using Docker (local/single machine)"
    echo "  k8s         Deploy to Kubernetes cluster"
    echo "  compose     Deploy using Docker Compose"
    echo "  local       Deploy locally for development"
    echo ""
    echo "Docker Deployment Options:"
    echo "  --environment ENV    Environment (development, staging, production)"
    echo "  --image-tag TAG      Docker image tag"
    echo "  --port PORT          Host port to bind"
    echo "  --force              Skip confirmation prompts"
    echo ""
    echo "Kubernetes Deployment Options:"
    echo "  --image-tag TAG      Docker image tag"
    echo "  --domain DOMAIN      Domain for ingress"
    echo "  --skip-monitoring    Skip monitoring stack"
    echo "  --dry-run           Show what would be deployed"
    echo ""
    echo "Docker Compose Options:"
    echo "  --profile PROFILE    Docker Compose profile (monitoring, etc.)"
    echo "  --env ENV           Environment (dev, prod)"
    echo ""
    echo "Global Options:"
    echo "  --help              Show this help message"
    echo "  --version           Show version information"
    echo ""
    echo "Environment Variables:"
    echo "  DOCKER_HUB_USERNAME  Docker Hub username (required)"
    echo "  IMAGE_TAG           Docker image tag (default: latest)"
    echo "  DOMAIN              Domain for Kubernetes ingress"
    echo ""
    echo "Examples:"
    echo "  # Docker deployment to staging"
    echo "  DOCKER_HUB_USERNAME=myuser $0 docker --environment staging"
    echo ""
    echo "  # Kubernetes deployment with custom domain"
    echo "  DOCKER_HUB_USERNAME=myuser $0 k8s --domain api.mycompany.com"
    echo ""
    echo "  # Local development with Docker Compose"
    echo "  $0 compose --env dev"
    echo ""
    echo "  # Local development server"
    echo "  $0 local"
}

# Function to show version
show_version() {
    echo "Iris Classification API Deployment Tool v1.0.0"
    echo "MLOps Pipeline with CI/CD Automation"
}

# Function to check prerequisites
check_prerequisites() {
    local deployment_type=$1
    
    case $deployment_type in
        docker)
            if ! command -v docker &> /dev/null; then
                print_error "Docker is not installed"
                exit 1
            fi
            if ! docker info &> /dev/null; then
                print_error "Docker daemon is not running"
                exit 1
            fi
            ;;
        k8s)
            if ! command -v kubectl &> /dev/null; then
                print_error "kubectl is not installed"
                exit 1
            fi
            if ! kubectl cluster-info &> /dev/null; then
                print_error "Cannot connect to Kubernetes cluster"
                exit 1
            fi
            ;;
        compose)
            if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
                print_error "Docker Compose is not installed"
                exit 1
            fi
            ;;
        local)
            if ! command -v python3 &> /dev/null; then
                print_error "Python 3 is not installed"
                exit 1
            fi
            ;;
    esac
}

# Function to deploy with Docker
deploy_docker() {
    local args=("$@")
    
    print_header "🐳 Docker Deployment"
    print_info "Using advanced Python deployment manager..."
    
    if [ ! -f "deploy/deploy-manager.py" ]; then
        print_error "Deployment manager not found. Using fallback script..."
        exec ./scripts/deploy.sh "${args[@]}"
    else
        exec ./deploy/deploy-manager.py deploy "${args[@]}"
    fi
}

# Function to deploy to Kubernetes
deploy_kubernetes() {
    local args=("$@")
    
    print_header "☸️  Kubernetes Deployment"
    print_info "Using Kubernetes deployment script..."
    
    if [ ! -f "deploy/k8s-deploy.sh" ]; then
        print_error "Kubernetes deployment script not found"
        exit 1
    fi
    
    exec ./deploy/k8s-deploy.sh "${args[@]}"
}

# Function to deploy with Docker Compose
deploy_compose() {
    local profile=""
    local env="dev"
    
    # Parse compose-specific arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --profile)
                profile="$2"
                shift 2
                ;;
            --env)
                env="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done
    
    print_header "🐙 Docker Compose Deployment"
    
    local compose_files="-f docker-compose.yml"
    
    if [ "$env" = "prod" ]; then
        compose_files="$compose_files -f docker-compose.prod.yml"
        print_info "Using production configuration"
    elif [ "$env" = "dev" ]; then
        if [ -f "docker-compose.dev.yml" ]; then
            compose_files="$compose_files -f docker-compose.dev.yml"
        fi
        print_info "Using development configuration"
    fi
    
    if [ -n "$profile" ]; then
        print_info "Using profile: $profile"
        docker-compose $compose_files --profile $profile up -d
    else
        docker-compose $compose_files up -d
    fi
    
    print_status "Docker Compose deployment completed"
    print_info "Services are starting up..."
    
    # Wait a bit and show status
    sleep 10
    docker-compose $compose_files ps
}

# Function to deploy locally
deploy_local() {
    print_header "💻 Local Development Deployment"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv venv
        print_status "Virtual environment created"
    fi
    
    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    
    # Install dependencies
    print_info "Installing dependencies..."
    pip install -r requirements.txt
    
    # Create necessary directories
    mkdir -p logs artifacts data
    
    # Check if model files exist
    if [ ! -f "artifacts/best_model.pkl" ]; then
        print_warning "Model files not found. Creating dummy models for development..."
        python -c "
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import numpy as np

model = LogisticRegression(random_state=42)
scaler = StandardScaler()
X_dummy = np.random.RandomState(42).rand(100, 4)
y_dummy = np.random.RandomState(42).choice(['setosa', 'versicolor', 'virginica'], 100)
X_scaled = scaler.fit_transform(X_dummy)
model.fit(X_scaled, y_dummy)
joblib.dump(model, 'artifacts/best_model.pkl')
joblib.dump(scaler, 'artifacts/scaler.pkl')
print('✅ Dummy models created for development')
"
    fi
    
    print_status "Starting local development server..."
    print_info "API will be available at: http://localhost:8000"
    print_info "API docs will be available at: http://localhost:8000/docs"
    print_info "Press Ctrl+C to stop the server"
    
    # Start the server
    export PYTHONPATH=.
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
}

# Main function
main() {
    local deployment_type=""
    local args=()
    
    # Parse global arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help)
                show_usage
                exit 0
                ;;
            --version)
                show_version
                exit 0
                ;;
            docker|k8s|compose|local)
                deployment_type="$1"
                shift
                break
                ;;
            *)
                if [ -z "$deployment_type" ]; then
                    print_error "Unknown deployment type: $1"
                    echo ""
                    show_usage
                    exit 1
                fi
                args+=("$1")
                shift
                ;;
        esac
    done
    
    # Collect remaining arguments
    while [[ $# -gt 0 ]]; do
        args+=("$1")
        shift
    done
    
    # Check if deployment type is provided
    if [ -z "$deployment_type" ]; then
        print_error "Deployment type is required"
        echo ""
        show_usage
        exit 1
    fi
    
    # Check prerequisites
    check_prerequisites "$deployment_type"
    
    # Execute deployment
    case $deployment_type in
        docker)
            deploy_docker "${args[@]}"
            ;;
        k8s)
            deploy_kubernetes "${args[@]}"
            ;;
        compose)
            deploy_compose "${args[@]}"
            ;;
        local)
            deploy_local "${args[@]}"
            ;;
        *)
            print_error "Unknown deployment type: $deployment_type"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"