# Makefile for Iris Classification API Docker operations

.PHONY: help build up down logs clean train test test-unit test-integration dev monitoring lint format install-dev deploy deploy-prod rollback test-local

# Default target
help:
	@echo "Available commands:"
	@echo "  build         - Build the Docker image"
	@echo "  up            - Start all services"
	@echo "  down          - Stop all services"
	@echo "  logs          - View logs from all services"
	@echo "  clean         - Remove all containers, volumes, and images"
	@echo "  train         - Run the model training script inside Docker (services must be up)"
	@echo "  test          - Run all tests"
	@echo "  test-unit     - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-local    - Run local CI/CD pipeline test"
	@echo "  lint          - Run code linting (flake8)"
	@echo "  format        - Format code (black, isort)"
	@echo "  install-dev   - Install development dependencies"
	@echo "  dev           - Start development environment with hot reload"
	@echo "  monitoring    - Start all services, including monitoring"
	@echo "  deploy        - Deploy using deployment script"
	@echo "  deploy-prod   - Deploy production environment with docker-compose"
	@echo "  rollback      - Rollback to previous version"

# Build the Docker image
build:
	docker-compose build

# Start all services
up:
	docker-compose up -d

# Stop all services
down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Clean up everything
clean:
	docker-compose down -v --rmi all --remove-orphans

# ✨ UPDATED: Run the training script non-interactively inside the RUNNING container
train:
	@echo "Running model training inside the running 'iris-api' container..."
	@echo "NOTE: This requires services to be running. Run 'make monitoring' first if they are not."
	docker-compose exec -T iris-api python src/train.py

# Install development dependencies
install-dev:
	pip install flake8 black isort pytest pytest-cov

# Run all tests
test:
	python -m pytest tests/ -v --cov=api --cov=src --cov-report=term-missing

# Run unit tests only
test-unit:
	python -m pytest tests/ -v -m "not integration" --cov=api --cov=src --cov-report=term-missing

# Run integration tests only
test-integration:
	python -m pytest tests/integration/ -v

# Run tests in Docker container
test-docker:
	docker-compose run --rm iris-api python -m pytest tests/ -v

# Lint code
lint:
	flake8 api/ src/ --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 api/ src/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Format code
format:
	black api/ src/
	isort api/ src/

# Check code formatting
format-check:
	black --check --diff api/ src/
	isort --check-only --diff api/ src/

# Development environment with hot reload
dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Start with monitoring stack
monitoring: up

# View API logs only
api-logs:
	docker-compose logs -f iris-api

# View MLflow logs only
mlflow-logs:
	docker-compose logs -f mlflow

# Restart API service only
restart-api:
	docker-compose restart iris-api

# Execute shell in API container
shell:
	docker-compose exec iris-api /bin/bash

# Check service health
health:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health | python -m json.tool || echo "API not responding"
	@curl -s -o /dev/null -w "MLflow: HTTP %{http_code}\n" http://localhost:5001/health || echo "MLflow not responding"

# Run local CI/CD pipeline test
test-local:
	./scripts/test-local.sh

# Deploy using deployment script
deploy:
	./scripts/deploy.sh

# Deploy production environment with docker-compose
deploy-prod:
	@echo "Starting production deployment..."
	@if [ -z "$(DOCKER_HUB_USERNAME)" ]; then \
		echo "Error: DOCKER_HUB_USERNAME environment variable is required"; \
		echo "Usage: DOCKER_HUB_USERNAME=your-username make deploy-prod"; \
		exit 1; \
	fi
	DOCKER_HUB_USERNAME=$(DOCKER_HUB_USERNAME) IMAGE_TAG=$(IMAGE_TAG) \
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "Production deployment started. Check status with 'make health'"

# Stop production deployment
stop-prod:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

# Rollback to previous version
rollback:
	./scripts/rollback.sh

# Build and push Docker image
build-push:
	@if [ -z "$(DOCKER_HUB_USERNAME)" ]; then \
		echo "Error: DOCKER_HUB_USERNAME environment variable is required"; \
		echo "Usage: DOCKER_HUB_USERNAME=your-username make build-push"; \
		exit 1; \
	fi
	docker build -t $(DOCKER_HUB_USERNAME)/iris-classifier-api:latest .
	docker push $(DOCKER_HUB_USERNAME)/iris-classifier-api:latest
	@echo "Image pushed to Docker Hub: $(DOCKER_HUB_USERNAME)/iris-classifier-api:latest"

# Build multi-platform image
build-multiplatform:
	@if [ -z "$(DOCKER_HUB_USERNAME)" ]; then \
		echo "Error: DOCKER_HUB_USERNAME environment variable is required"; \
		echo "Usage: DOCKER_HUB_USERNAME=your-username make build-multiplatform"; \
		exit 1; \
	fi
	docker buildx build --platform linux/amd64,linux/arm64 \
		-t $(DOCKER_HUB_USERNAME)/iris-classifier-api:latest \
		--push .
