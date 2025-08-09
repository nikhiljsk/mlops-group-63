#!/bin/bash

# Demo Script for Iris Classification API
# Demonstrates end-to-end functionality

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}$1${NC}"
}

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

API_URL=${API_URL:-"http://localhost:8000"}

print_header "🌸 Iris Classification API Demo"
echo "=================================="
echo ""

# Check if API is running
print_info "Checking API availability..."
if curl -f -s "$API_URL/health" > /dev/null; then
    print_status "API is running at $API_URL"
else
    echo "❌ API not available at $API_URL"
    echo "Please start the API first:"
    echo "  ./deploy.sh local"
    echo "  # or"
    echo "  docker-compose up -d"
    exit 1
fi

echo ""
print_header "1. Health Check"
echo "GET $API_URL/health"
curl -s "$API_URL/health" | python -m json.tool
echo ""

print_header "2. Model Information"
echo "GET $API_URL/model/info"
curl -s "$API_URL/model/info" | python -m json.tool
echo ""

print_header "3. Single Prediction - Setosa"
echo "POST $API_URL/predict"
echo "Data: Sepal Length=5.1, Sepal Width=3.5, Petal Length=1.4, Petal Width=0.2"
curl -s -X POST "$API_URL/predict" \
  -H "Content-Type: application/json" \
  -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}' | python -m json.tool
echo ""

print_header "4. Single Prediction - Versicolor"
echo "POST $API_URL/predict"
echo "Data: Sepal Length=6.2, Sepal Width=2.9, Petal Length=4.3, Petal Width=1.3"
curl -s -X POST "$API_URL/predict" \
  -H "Content-Type: application/json" \
  -d '{"sepal_length": 6.2, "sepal_width": 2.9, "petal_length": 4.3, "petal_width": 1.3}' | python -m json.tool
echo ""

print_header "5. Single Prediction - Virginica"
echo "POST $API_URL/predict"
echo "Data: Sepal Length=7.3, Sepal Width=2.9, Petal Length=6.3, Petal Width=1.8"
curl -s -X POST "$API_URL/predict" \
  -H "Content-Type: application/json" \
  -d '{"sepal_length": 7.3, "sepal_width": 2.9, "petal_length": 6.3, "petal_width": 1.8}' | python -m json.tool
echo ""

print_header "6. Batch Prediction"
echo "POST $API_URL/predict/batch"
echo "Data: Multiple samples"
curl -s -X POST "$API_URL/predict/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "samples": [
      {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2},
      {"sepal_length": 6.2, "sepal_width": 2.9, "petal_length": 4.3, "petal_width": 1.3},
      {"sepal_length": 7.3, "sepal_width": 2.9, "petal_length": 6.3, "petal_width": 1.8}
    ]
  }' | python -m json.tool
echo ""

print_header "7. Error Handling - Invalid Input"
echo "POST $API_URL/predict (with negative values)"
curl -s -X POST "$API_URL/predict" \
  -H "Content-Type: application/json" \
  -d '{"sepal_length": -1.0, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}' | python -m json.tool
echo ""

print_header "8. Retraining Status"
echo "GET $API_URL/retrain/status"
curl -s "$API_URL/retrain/status" | python -m json.tool
echo ""

print_header "9. Metrics Sample"
echo "GET $API_URL/metrics (first 20 lines)"
curl -s "$API_URL/metrics" | head -20
echo "..."
echo ""

print_header "🎉 Demo Complete!"
echo "=================="
print_status "All API endpoints tested successfully"
echo ""
print_info "Available endpoints:"
echo "  🌐 API Base:     $API_URL"
echo "  🏥 Health:       $API_URL/health"
echo "  📊 Prediction:   $API_URL/predict"
echo "  📈 Metrics:      $API_URL/metrics"
echo "  📚 API Docs:     $API_URL/docs"
echo ""
print_info "Monitoring (if enabled):"
echo "  📊 Prometheus:   http://localhost:9090"
echo "  📈 Grafana:      http://localhost:3000 (admin/admin)"