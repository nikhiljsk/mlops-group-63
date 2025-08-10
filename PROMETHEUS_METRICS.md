# Prometheus Metrics Guide for Iris Classification API

## Access Prometheus UI
- **Prometheus UI**: http://localhost:9090
- **API Metrics Endpoint**: http://localhost:8000/metrics

## Key Metrics to Monitor

### 🔥 Essential ML Metrics
```promql
# Total predictions made by model version
ml_predictions_total

# Prediction confidence distribution
ml_prediction_confidence

# Prediction latency (response time)
ml_prediction_duration_seconds

# Prediction errors
ml_prediction_errors_total
```

### 📊 API Performance Metrics
```promql
# HTTP request rate
rate(http_requests_total[5m])

# HTTP request duration
http_request_duration_seconds

# API error rate
rate(api_errors_total[5m])

# API uptime
api_uptime_seconds
```

### 🎯 Model-Specific Queries
```promql
# Predictions per species (setosa, versicolor, virginica)
sum by (prediction_class) (ml_predictions_total)

# Average prediction confidence by species
avg by (prediction_class) (ml_prediction_confidence)

# 95th percentile prediction latency
histogram_quantile(0.95, ml_prediction_duration_seconds_bucket)

# Prediction throughput (predictions per second)
rate(ml_predictions_total[1m])
```

### 🚨 Health & Error Monitoring
```promql
# Error rate percentage
(rate(api_errors_total[5m]) / rate(http_requests_total[5m])) * 100

# Model load status (should be > 0 when loaded)
ml_model_load_timestamp_seconds

# Database connection health
database_connections_active
```

### 📈 Useful Dashboard Queries

#### Request Rate by Endpoint
```promql
sum by (endpoint) (rate(http_requests_total[5m]))
```

#### Prediction Accuracy Trends (if you add accuracy metrics)
```promql
avg_over_time(ml_prediction_confidence[1h])
```

#### Top Predicted Classes
```promql
topk(3, sum by (prediction_class) (ml_predictions_total))
```

## Quick Start in Prometheus UI

1. Go to http://localhost:9090
2. Click "Graph" tab
3. Try these starter queries:
   - `ml_predictions_total` - See total predictions
   - `rate(http_requests_total[5m])` - Request rate
   - `ml_prediction_duration_seconds` - Prediction latency
   - `up` - Service health (1 = up, 0 = down)

## Creating Alerts (Advanced)
You can set up alerts for:
- High error rates: `rate(api_errors_total[5m]) > 0.1`
- Slow predictions: `histogram_quantile(0.95, ml_prediction_duration_seconds_bucket) > 0.1`
- Service down: `up == 0`