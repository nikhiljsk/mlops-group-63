"""
Monitoring and Alerting System Tests
Tests the complete monitoring infrastructure including Prometheus, Grafana, and alerting.
"""

import pytest
import requests
import time
import subprocess
import os
import yaml
import json
import tempfile
import docker
from pathlib import Path
import concurrent.futures


class TestMonitoringAndAlerting:
    """Test monitoring and alerting system functionality"""
    
    @pytest.fixture(scope="class")
    def docker_client(self):
        """Docker client for testing"""
        return docker.from_env()
    
    def test_prometheus_configuration(self):
        """Test Prometheus configuration and setup"""
        prometheus_config = "monitoring/prometheus.yml"
        
        assert os.path.exists(prometheus_config), "Prometheus configuration not found"
        
        with open(prometheus_config, 'r') as f:
            config = yaml.safe_load(f)
        
        # Validate basic structure
        assert "global" in config, "Prometheus config missing global section"
        assert "scrape_configs" in config, "Prometheus config missing scrape_configs"
        
        # Check global configuration
        global_config = config["global"]
        assert "scrape_interval" in global_config, "Missing scrape_interval in global config"
        assert "evaluation_interval" in global_config, "Missing evaluation_interval in global config"
        
        # Check scrape configurations
        scrape_configs = config["scrape_configs"]
        assert len(scrape_configs) > 0, "No scrape configurations defined"
        
        # Find iris-api job
        iris_job = None
        for job in scrape_configs:
            if job.get("job_name") == "iris-api":
                iris_job = job
                break
        
        assert iris_job is not None, "iris-api job not found in scrape configs"
        assert "static_configs" in iris_job, "iris-api job missing static_configs"
        assert "metrics_path" in iris_job, "iris-api job missing metrics_path"
        assert iris_job["metrics_path"] == "/metrics", "Incorrect metrics path"
        
        # Check alerting configuration
        if "alerting" in config:
            alerting_config = config["alerting"]
            assert "alertmanagers" in alerting_config, "Alerting config missing alertmanagers"
    
    def test_alert_rules_configuration(self):
        """Test alert rules configuration"""
        alert_rules_file = "monitoring/alert_rules.yml"
        
        assert os.path.exists(alert_rules_file), "Alert rules file not found"
        
        with open(alert_rules_file, 'r') as f:
            alert_config = yaml.safe_load(f)
        
        # Validate structure
        assert "groups" in alert_config, "Alert config missing groups"
        assert len(alert_config["groups"]) > 0, "No alert groups defined"
        
        # Check for expected alert groups
        group_names = [group.get("name", "") for group in alert_config["groups"]]
        assert any("iris-api" in name.lower() for name in group_names), \
            "No iris-api alert group found"
        
        # Validate alert rules
        all_alerts = []
        for group in alert_config["groups"]:
            if "rules" in group:
                for rule in group["rules"]:
                    if "alert" in rule:
                        all_alerts.append(rule)
        
        assert len(all_alerts) > 0, "No alert rules defined"
        
        # Check for expected alerts
        expected_alerts = ["HighErrorRate", "HighResponseTime", "APIDown"]
        alert_names = [alert["alert"] for alert in all_alerts]
        
        for expected_alert in expected_alerts:
            assert expected_alert in alert_names, f"Missing alert: {expected_alert}"
        
        # Validate alert rule structure
        for alert in all_alerts:
            assert "expr" in alert, f"Alert {alert['alert']} missing expression"
            assert "for" in alert, f"Alert {alert['alert']} missing duration"
            assert "labels" in alert, f"Alert {alert['alert']} missing labels"
            assert "annotations" in alert, f"Alert {alert['alert']} missing annotations"
            
            # Check severity label
            assert "severity" in alert["labels"], f"Alert {alert['alert']} missing severity label"
            
            # Check annotations
            annotations = alert["annotations"]
            assert "summary" in annotations, f"Alert {alert['alert']} missing summary annotation"
            assert "description" in annotations, f"Alert {alert['alert']} missing description annotation"
    
    def test_grafana_dashboard_configuration(self):
        """Test Grafana dashboard configuration"""
        dashboard_dir = "monitoring/grafana/dashboards"
        
        if os.path.exists(dashboard_dir):
            dashboard_files = [f for f in os.listdir(dashboard_dir) if f.endswith('.json')]
            
            assert len(dashboard_files) > 0, "No Grafana dashboard files found"
            
            for dashboard_file in dashboard_files:
                dashboard_path = os.path.join(dashboard_dir, dashboard_file)
                
                with open(dashboard_path, 'r') as f:
                    dashboard_config = json.load(f)
                
                # Validate dashboard structure
                assert "dashboard" in dashboard_config or "title" in dashboard_config, \
                    f"Invalid dashboard structure in {dashboard_file}"
                
                # Check for panels
                dashboard_data = dashboard_config.get("dashboard", dashboard_config)
                if "panels" in dashboard_data:
                    panels = dashboard_data["panels"]
                    assert len(panels) > 0, f"No panels defined in dashboard {dashboard_file}"
                    
                    # Check panel structure
                    for panel in panels:
                        if "targets" in panel:
                            targets = panel["targets"]
                            for target in targets:
                                if "expr" in target:
                                    # Basic validation of Prometheus query
                                    expr = target["expr"]
                                    assert len(expr.strip()) > 0, \
                                        f"Empty Prometheus expression in {dashboard_file}"
    
    def test_metrics_endpoint_functionality(self):
        """Test metrics endpoint and Prometheus format"""
        # Start API server
        process = subprocess.Popen([
            "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8011"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            time.sleep(15)
            
            # Generate some metrics by making requests
            prediction_data = {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            }
            
            # Make various requests to generate metrics
            for _ in range(10):
                requests.post("http://localhost:8011/predict", json=prediction_data)
                requests.get("http://localhost:8011/health")
                time.sleep(0.1)
            
            # Test metrics endpoint
            response = requests.get("http://localhost:8011/metrics")
            assert response.status_code == 200, "Metrics endpoint not accessible"
            
            # Check content type
            content_type = response.headers.get("content-type", "")
            assert "text/plain" in content_type, f"Incorrect content type: {content_type}"
            
            metrics_text = response.text
            
            # Validate Prometheus format
            lines = metrics_text.split('\n')
            
            # Check for HELP and TYPE comments
            help_lines = [line for line in lines if line.startswith('# HELP')]
            type_lines = [line for line in lines if line.startswith('# TYPE')]
            
            assert len(help_lines) > 0, "No HELP lines found in metrics"
            assert len(type_lines) > 0, "No TYPE lines found in metrics"
            
            # Check for expected metrics
            expected_metrics = [
                "http_requests_total",
                "http_request_duration_seconds",
                "ml_predictions_total",
                "python_info"
            ]
            
            for metric in expected_metrics:
                assert metric in metrics_text, f"Missing metric: {metric}"
            
            # Validate metric format
            metric_lines = [line for line in lines if line and not line.startswith('#')]
            
            for line in metric_lines:
                if line.strip():
                    # Basic format validation: metric_name{labels} value [timestamp]
                    parts = line.split()
                    assert len(parts) >= 2, f"Invalid metric line format: {line}"
                    
                    metric_part = parts[0]
                    value_part = parts[1]
                    
                    # Check metric name format
                    if '{' in metric_part:
                        metric_name = metric_part.split('{')[0]
                    else:
                        metric_name = metric_part
                    
                    assert metric_name.replace('_', '').replace(':', '').isalnum(), \
                        f"Invalid metric name: {metric_name}"
                    
                    # Check value is numeric
                    try:
                        float(value_part)
                    except ValueError:
                        assert False, f"Invalid metric value: {value_part} in line: {line}"
            
        finally:
            process.terminate()
            process.wait(timeout=10)
    
    def test_monitoring_stack_with_docker_compose(self, docker_client):
        """Test monitoring stack deployment with Docker Compose"""
        # Check if monitoring compose file exists
        monitoring_compose_files = [
            "docker-compose.monitoring.yml",
            "monitoring/docker-compose.yml"
        ]
        
        compose_file = None
        for file_path in monitoring_compose_files:
            if os.path.exists(file_path):
                compose_file = file_path
                break
        
        if compose_file is None:
            # Create a basic monitoring compose file for testing
            compose_file = "docker-compose.monitoring.test.yml"
            monitoring_compose = {
                "version": "3.8",
                "services": {
                    "prometheus": {
                        "image": "prom/prometheus:latest",
                        "ports": ["9090:9090"],
                        "volumes": ["./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml"],
                        "command": [
                            "--config.file=/etc/prometheus/prometheus.yml",
                            "--storage.tsdb.path=/prometheus",
                            "--web.console.libraries=/etc/prometheus/console_libraries",
                            "--web.console.templates=/etc/prometheus/consoles"
                        ]
                    }
                }
            }
            
            with open(compose_file, 'w') as f:
                yaml.dump(monitoring_compose, f)
        
        try:
            # Validate compose file
            result = subprocess.run([
                "docker-compose", "-f", compose_file, "config"
            ], capture_output=True, text=True)
            
            assert result.returncode == 0, f"Invalid monitoring compose file: {result.stderr}"
            
            # Try to start monitoring stack (if Prometheus config exists)
            if os.path.exists("monitoring/prometheus.yml"):
                result = subprocess.run([
                    "docker-compose", "-f", compose_file, "up", "-d"
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    try:
                        # Wait for services to start
                        time.sleep(30)
                        
                        # Test Prometheus is accessible
                        try:
                            response = requests.get("http://localhost:9090/api/v1/status/config", timeout=10)
                            if response.status_code == 200:
                                config_data = response.json()
                                assert "status" in config_data
                                assert config_data["status"] == "success"
                        except requests.exceptions.RequestException:
                            print("Prometheus not accessible - this might be expected in CI environment")
                        
                    finally:
                        # Cleanup
                        subprocess.run([
                            "docker-compose", "-f", compose_file, "down", "-v"
                        ], capture_output=True, text=True)
        
        finally:
            # Cleanup test compose file
            if compose_file.endswith(".test.yml") and os.path.exists(compose_file):
                os.remove(compose_file)
    
    def test_alert_simulation(self):
        """Test alert conditions and simulation"""
        # Start API server
        process = subprocess.Popen([
            "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8012"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            time.sleep(15)
            
            # Test normal operation metrics
            prediction_data = {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            }
            
            # Generate normal traffic
            for _ in range(20):
                response = requests.post("http://localhost:8012/predict", json=prediction_data)
                assert response.status_code == 200
                time.sleep(0.1)
            
            # Get metrics after normal operation
            response = requests.get("http://localhost:8012/metrics")
            assert response.status_code == 200
            normal_metrics = response.text
            
            # Check that success metrics are being recorded
            assert "http_requests_total" in normal_metrics
            assert "ml_predictions_total" in normal_metrics
            
            # Simulate error conditions
            error_conditions = [
                {"sepal_length": -1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2},
                {"invalid": "data"},
                {}
            ]
            
            # Generate error traffic
            for error_data in error_conditions:
                for _ in range(5):
                    requests.post("http://localhost:8012/predict", json=error_data)
                    time.sleep(0.1)
            
            # Get metrics after error generation
            response = requests.get("http://localhost:8012/metrics")
            assert response.status_code == 200
            error_metrics = response.text
            
            # Verify error metrics are being recorded
            # Look for HTTP 422 status codes in metrics
            lines = error_metrics.split('\n')
            error_metric_found = False
            
            for line in lines:
                if 'http_requests_total' in line and '422' in line:
                    error_metric_found = True
                    break
            
            assert error_metric_found, "Error metrics not found after generating errors"
            
        finally:
            process.terminate()
            process.wait(timeout=10)
    
    def test_performance_monitoring(self):
        """Test performance monitoring and metrics"""
        # Start API server
        process = subprocess.Popen([
            "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8013"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            time.sleep(15)
            
            prediction_data = {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            }
            
            # Generate load to test performance monitoring
            def make_request():
                start_time = time.time()
                response = requests.post("http://localhost:8013/predict", json=prediction_data)
                end_time = time.time()
                return response.status_code, end_time - start_time
            
            # Concurrent requests to generate performance data
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request) for _ in range(50)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # Analyze performance
            successful_requests = [r for r in results if r[0] == 200]
            response_times = [r[1] for r in successful_requests]
            
            assert len(successful_requests) > 0, "No successful requests for performance monitoring"
            
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            # Get metrics to verify performance data is recorded
            response = requests.get("http://localhost:8013/metrics")
            assert response.status_code == 200
            metrics_text = response.text
            
            # Check for duration metrics
            assert "http_request_duration_seconds" in metrics_text, \
                "Request duration metrics not found"
            
            # Look for histogram buckets
            duration_buckets_found = False
            lines = metrics_text.split('\n')
            
            for line in lines:
                if 'http_request_duration_seconds_bucket' in line:
                    duration_buckets_found = True
                    break
            
            assert duration_buckets_found, "Duration histogram buckets not found"
            
            # Performance assertions
            assert avg_response_time < 2.0, f"Average response time too high: {avg_response_time}s"
            assert max_response_time < 5.0, f"Max response time too high: {max_response_time}s"
            
        finally:
            process.terminate()
            process.wait(timeout=10)
    
    def test_custom_business_metrics(self):
        """Test custom business metrics collection"""
        # Start API server
        process = subprocess.Popen([
            "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8014"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            time.sleep(15)
            
            # Make predictions for different classes
            test_cases = [
                # Setosa
                {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2},
                # Versicolor
                {"sepal_length": 6.2, "sepal_width": 2.9, "petal_length": 4.3, "petal_width": 1.3},
                # Virginica
                {"sepal_length": 6.3, "sepal_width": 3.3, "petal_length": 6.0, "petal_width": 2.5}
            ]
            
            # Generate predictions for each class
            for test_case in test_cases:
                for _ in range(10):
                    response = requests.post("http://localhost:8014/predict", json=test_case)
                    assert response.status_code == 200
                    time.sleep(0.1)
            
            # Get metrics
            response = requests.get("http://localhost:8014/metrics")
            assert response.status_code == 200
            metrics_text = response.text
            
            # Check for custom ML metrics
            expected_ml_metrics = [
                "ml_predictions_total",
                "ml_prediction_confidence"
            ]
            
            for metric in expected_ml_metrics:
                assert metric in metrics_text, f"Missing custom ML metric: {metric}"
            
            # Check for prediction class labels
            lines = metrics_text.split('\n')
            prediction_classes_found = set()
            
            for line in lines:
                if 'ml_predictions_total' in line and 'prediction=' in line:
                    # Extract prediction class from label
                    if 'prediction="setosa"' in line:
                        prediction_classes_found.add('setosa')
                    elif 'prediction="versicolor"' in line:
                        prediction_classes_found.add('versicolor')
                    elif 'prediction="virginica"' in line:
                        prediction_classes_found.add('virginica')
            
            # Should have metrics for at least some prediction classes
            assert len(prediction_classes_found) > 0, \
                "No prediction class metrics found"
            
        finally:
            process.terminate()
            process.wait(timeout=10)
    
    def test_log_monitoring_integration(self):
        """Test log monitoring and structured logging"""
        # Start API server
        process = subprocess.Popen([
            "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8015"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            time.sleep(15)
            
            # Make requests to generate logs
            prediction_data = {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            }
            
            for _ in range(5):
                response = requests.post("http://localhost:8015/predict", json=prediction_data)
                assert response.status_code == 200
                time.sleep(0.5)
            
            # Check if logs are being written to database
            if os.path.exists("logs.db"):
                import sqlite3
                
                conn = sqlite3.connect("logs.db")
                cursor = conn.cursor()
                
                # Check prediction logs
                cursor.execute("SELECT COUNT(*) FROM prediction_logs")
                log_count = cursor.fetchone()[0]
                
                assert log_count > 0, "No prediction logs found in database"
                
                # Check log structure
                cursor.execute("SELECT * FROM prediction_logs LIMIT 1")
                if cursor.fetchone():
                    columns = [description[0] for description in cursor.description]
                    expected_columns = ["timestamp", "request_data", "prediction"]
                    
                    for col in expected_columns:
                        assert col in columns, f"Missing log column: {col}"
                
                conn.close()
            
            # Check application logs (if available)
            logs = process.stdout.read().decode('utf-8') if process.stdout else ""
            if logs:
                # Look for structured log entries
                log_lines = logs.split('\n')
                structured_logs_found = False
                
                for line in log_lines:
                    if 'prediction' in line.lower() and ('info' in line.lower() or 'debug' in line.lower()):
                        structured_logs_found = True
                        break
                
                if structured_logs_found:
                    print("Structured logging appears to be working")
            
        finally:
            process.terminate()
            process.wait(timeout=10)


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "--tb=short"])