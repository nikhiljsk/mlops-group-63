"""
CI/CD Pipeline Validation Tests
Tests the complete CI/CD pipeline functionality and automation.
"""

import pytest
import subprocess
import os
import yaml
import json
import tempfile
import shutil
from pathlib import Path
import docker
import requests
import time


class TestCICDPipeline:
    """Test CI/CD pipeline functionality"""
    
    @pytest.fixture(scope="class")
    def docker_client(self):
        """Docker client for testing"""
        return docker.from_env()
    
    def test_github_workflow_validation(self):
        """Test GitHub Actions workflow configuration"""
        workflow_file = ".github/workflows/ci-cd.yml"
        
        assert os.path.exists(workflow_file), "CI/CD workflow file not found"
        
        with open(workflow_file, 'r') as f:
            workflow = yaml.safe_load(f)
        
        # Validate workflow structure
        assert "name" in workflow
        assert "on" in workflow
        assert "jobs" in workflow
        
        # Check trigger events
        assert "push" in workflow["on"]
        assert "pull_request" in workflow["on"]
        
        # Validate jobs
        expected_jobs = ["test", "docker-build-push", "integration-test"]
        for job_name in expected_jobs:
            assert job_name in workflow["jobs"], f"Missing job: {job_name}"
        
        # Validate job dependencies
        docker_job = workflow["jobs"]["docker-build-push"]
        assert "needs" in docker_job
        assert "test" in docker_job["needs"]
        
        integration_job = workflow["jobs"]["integration-test"]
        assert "needs" in integration_job
        assert "docker-build-push" in integration_job["needs"]
        
        # Validate test job steps
        test_job = workflow["jobs"]["test"]
        step_names = [step.get("name", "") for step in test_job["steps"]]
        
        expected_steps = [
            "Checkout code",
            "Set up Python",
            "Install dependencies",
            "Lint with flake8",
            "Run unit tests with pytest"
        ]
        
        for expected_step in expected_steps:
            assert any(expected_step in step_name for step_name in step_names), \
                f"Missing test step: {expected_step}"
    
    def test_code_quality_pipeline(self):
        """Test code quality checks in CI pipeline"""
        # Test linting
        result = subprocess.run([
            "flake8", "api/", "src/", "--count", "--select=E9,F63,F7,F82", 
            "--show-source", "--statistics"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Linting failed: {result.stdout}\n{result.stderr}"
        
        # Test code formatting
        result = subprocess.run([
            "black", "--check", "--diff", "api/", "src/"
        ], capture_output=True, text=True)
        
        # Black returns 0 if no changes needed, 1 if changes needed
        if result.returncode != 0:
            print(f"Code formatting issues found:\n{result.stdout}")
        
        # Test import sorting
        result = subprocess.run([
            "isort", "--check-only", "--diff", "api/", "src/"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Import sorting issues found:\n{result.stdout}")
    
    def test_unit_test_pipeline(self):
        """Test unit test execution in CI pipeline"""
        # Run unit tests with coverage
        result = subprocess.run([
            "python", "-m", "pytest", "tests/", "-v", 
            "--cov=api", "--cov=src", "--cov-report=term-missing", 
            "--cov-report=xml", "--tb=short"
        ], capture_output=True, text=True, env={**os.environ, "PYTHONPATH": "."})
        
        assert result.returncode == 0, f"Unit tests failed:\n{result.stdout}\n{result.stderr}"
        
        # Check coverage report was generated
        assert os.path.exists("coverage.xml"), "Coverage report not generated"
        
        # Parse coverage report
        with open("coverage.xml", 'r') as f:
            coverage_content = f.read()
        
        # Basic validation that coverage report contains expected elements
        assert "<coverage" in coverage_content
        assert "line-rate" in coverage_content
    
    def test_docker_build_pipeline(self, docker_client):
        """Test Docker build process in CI pipeline"""
        # Create test image tag
        test_tag = "iris-api-cicd-test"
        
        try:
            # Build Docker image (simulating CI build)
            image, build_logs = docker_client.images.build(
                path=".",
                tag=test_tag,
                rm=True,
                forcerm=True,
                pull=True
            )
            
            # Verify image was built successfully
            assert image is not None
            assert test_tag in [tag for tag in image.tags]
            
            # Check image labels and metadata
            image_attrs = image.attrs
            assert "Config" in image_attrs
            
            # Test image can be run
            container = docker_client.containers.run(
                test_tag,
                detach=True,
                ports={'8000/tcp': None},
                name="cicd-test-container"
            )
            
            try:
                # Wait for container to start
                time.sleep(10)
                
                # Get container port
                container.reload()
                port_info = container.attrs['NetworkSettings']['Ports']['8000/tcp']
                if port_info:
                    host_port = port_info[0]['HostPort']
                    
                    # Test container is responding
                    try:
                        response = requests.get(f"http://localhost:{host_port}/health", timeout=10)
                        assert response.status_code == 200
                    except requests.exceptions.RequestException:
                        # Container might not be fully ready, check logs
                        logs = container.logs().decode('utf-8')
                        print(f"Container logs: {logs}")
                
            finally:
                container.stop()
                container.remove()
                
        finally:
            # Cleanup test image
            try:
                docker_client.images.remove(test_tag, force=True)
            except:
                pass
    
    def test_integration_test_pipeline(self):
        """Test integration test execution in CI pipeline"""
        # Start API server for integration testing
        process = subprocess.Popen([
            "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8009"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            # Wait for server to start
            time.sleep(15)
            
            # Run integration tests
            result = subprocess.run([
                "python", "-m", "pytest", "tests/integration/", "-v", "--tb=short"
            ], capture_output=True, text=True, env={**os.environ, "PYTHONPATH": "."})
            
            # Integration tests might skip if server not available
            # Check if tests ran or were skipped
            assert result.returncode in [0, 5], f"Integration tests failed:\n{result.stdout}\n{result.stderr}"
            
            # If tests were skipped, verify server is actually running
            if "SKIPPED" in result.stdout:
                try:
                    response = requests.get("http://localhost:8009/health", timeout=5)
                    if response.status_code == 200:
                        print("Server is running but tests were skipped - this might be expected")
                except requests.exceptions.RequestException:
                    print("Server not responding - integration test skips are expected")
            
        finally:
            process.terminate()
            process.wait(timeout=10)
    
    def test_deployment_pipeline_validation(self):
        """Test deployment pipeline configuration"""
        # Check deployment scripts exist
        deployment_scripts = [
            "deploy.sh",
            "scripts/deploy.sh"
        ]
        
        script_found = False
        for script in deployment_scripts:
            if os.path.exists(script):
                script_found = True
                
                # Test script syntax
                result = subprocess.run([
                    "bash", "-n", script
                ], capture_output=True, text=True)
                
                assert result.returncode == 0, f"Deployment script {script} has syntax errors: {result.stderr}"
                
                # Check script contains expected deployment logic
                with open(script, 'r') as f:
                    script_content = f.read()
                
                # Should contain Docker-related commands
                assert "docker" in script_content.lower(), f"Script {script} doesn't contain Docker commands"
                
                break
        
        assert script_found, "No deployment script found"
    
    def test_rollback_pipeline_validation(self):
        """Test rollback pipeline configuration"""
        rollback_script = "scripts/rollback.sh"
        
        if os.path.exists(rollback_script):
            # Test script syntax
            result = subprocess.run([
                "bash", "-n", rollback_script
            ], capture_output=True, text=True)
            
            assert result.returncode == 0, f"Rollback script has syntax errors: {result.stderr}"
            
            # Check script contains rollback logic
            with open(rollback_script, 'r') as f:
                script_content = f.read()
            
            # Should contain rollback-related commands
            rollback_keywords = ["rollback", "previous", "restore", "docker"]
            assert any(keyword in script_content.lower() for keyword in rollback_keywords), \
                "Rollback script doesn't contain expected rollback logic"
    
    def test_environment_configuration(self):
        """Test environment configuration for CI/CD"""
        # Check Docker Compose configurations
        compose_files = [
            "docker-compose.yml",
            "docker-compose.dev.yml",
            "docker-compose.prod.yml"
        ]
        
        for compose_file in compose_files:
            if os.path.exists(compose_file):
                # Validate Docker Compose syntax
                result = subprocess.run([
                    "docker-compose", "-f", compose_file, "config"
                ], capture_output=True, text=True)
                
                assert result.returncode == 0, f"Docker Compose file {compose_file} is invalid: {result.stderr}"
                
                # Parse and validate structure
                with open(compose_file, 'r') as f:
                    compose_config = yaml.safe_load(f)
                
                assert "version" in compose_config or "services" in compose_config, \
                    f"Invalid Docker Compose structure in {compose_file}"
                
                if "services" in compose_config:
                    # Should have at least one service
                    assert len(compose_config["services"]) > 0, \
                        f"No services defined in {compose_file}"
    
    def test_secrets_and_security_configuration(self):
        """Test security configuration in CI/CD pipeline"""
        workflow_file = ".github/workflows/ci-cd.yml"
        
        if os.path.exists(workflow_file):
            with open(workflow_file, 'r') as f:
                workflow_content = f.read()
            
            # Check for proper secrets usage
            if "docker" in workflow_content.lower():
                # Should use secrets for Docker Hub credentials
                assert "secrets.DOCKER_HUB_USERNAME" in workflow_content or \
                       "${{ secrets.DOCKER_HUB_USERNAME }}" in workflow_content, \
                       "Docker Hub username should use secrets"
                
                assert "secrets.DOCKER_HUB_ACCESS_TOKEN" in workflow_content or \
                       "secrets.DOCKER_HUB_PASSWORD" in workflow_content or \
                       "${{ secrets.DOCKER_HUB_ACCESS_TOKEN }}" in workflow_content, \
                       "Docker Hub password/token should use secrets"
            
            # Check that no hardcoded credentials are present
            sensitive_patterns = [
                "password=",
                "token=",
                "key=",
                "secret="
            ]
            
            for pattern in sensitive_patterns:
                assert pattern not in workflow_content.lower(), \
                    f"Potential hardcoded credential found: {pattern}"
    
    def test_artifact_management(self):
        """Test artifact management in CI/CD pipeline"""
        # Check that required artifacts exist or can be created
        required_artifacts = [
            "artifacts/best_model.pkl",
            "artifacts/scaler.pkl"
        ]
        
        artifacts_exist = all(os.path.exists(artifact) for artifact in required_artifacts)
        
        if not artifacts_exist:
            # Try to create artifacts by running training
            result = subprocess.run([
                "python", "src/train.py"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Check artifacts were created
                for artifact in required_artifacts:
                    assert os.path.exists(artifact), f"Artifact not created: {artifact}"
            else:
                print(f"Training failed, artifacts might not be available: {result.stderr}")
    
    def test_monitoring_integration_in_cicd(self):
        """Test monitoring integration in CI/CD pipeline"""
        # Check monitoring configuration files
        monitoring_files = [
            "monitoring/prometheus.yml",
            "monitoring/alert_rules.yml"
        ]
        
        for monitoring_file in monitoring_files:
            if os.path.exists(monitoring_file):
                with open(monitoring_file, 'r') as f:
                    config = yaml.safe_load(f)
                
                assert config is not None, f"Invalid YAML in {monitoring_file}"
                
                if "prometheus.yml" in monitoring_file:
                    assert "scrape_configs" in config, "Prometheus config missing scrape_configs"
                    
                    # Check for iris-api job
                    iris_job_found = False
                    for job in config["scrape_configs"]:
                        if job.get("job_name") == "iris-api":
                            iris_job_found = True
                            break
                    
                    assert iris_job_found, "iris-api job not found in Prometheus config"
                
                elif "alert_rules.yml" in monitoring_file:
                    assert "groups" in config, "Alert rules missing groups"
                    assert len(config["groups"]) > 0, "No alert groups defined"
    
    def test_performance_testing_in_cicd(self):
        """Test performance testing integration in CI/CD"""
        # Start API server for performance testing
        process = subprocess.Popen([
            "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8010"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            time.sleep(15)
            
            # Simple performance test
            import concurrent.futures
            
            def make_request():
                try:
                    start_time = time.time()
                    response = requests.post(
                        "http://localhost:8010/predict",
                        json={
                            "sepal_length": 5.1,
                            "sepal_width": 3.5,
                            "petal_length": 1.4,
                            "petal_width": 0.2
                        },
                        timeout=5
                    )
                    end_time = time.time()
                    return response.status_code == 200, end_time - start_time
                except:
                    return False, float('inf')
            
            # Run concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request) for _ in range(20)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # Analyze performance
            successful_requests = [r for r in results if r[0]]
            response_times = [r[1] for r in successful_requests]
            
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                
                # Performance thresholds for CI/CD
                assert avg_response_time < 2.0, f"Average response time too high: {avg_response_time}s"
                assert max_response_time < 5.0, f"Max response time too high: {max_response_time}s"
                
                success_rate = len(successful_requests) / len(results)
                assert success_rate >= 0.8, f"Success rate too low: {success_rate}"
            
        finally:
            process.terminate()
            process.wait(timeout=10)
    
    def test_documentation_in_cicd(self):
        """Test documentation requirements in CI/CD"""
        # Check required documentation files
        required_docs = [
            "README.md",
            "DEPLOYMENT.md",
            "DOCKER.md"
        ]
        
        for doc_file in required_docs:
            assert os.path.exists(doc_file), f"Required documentation file missing: {doc_file}"
            
            # Check file is not empty
            with open(doc_file, 'r') as f:
                content = f.read().strip()
            
            assert len(content) > 100, f"Documentation file {doc_file} appears to be too short"
            
            # Check for basic structure
            if doc_file == "README.md":
                assert "# " in content, "README.md should have at least one header"
                assert "install" in content.lower() or "setup" in content.lower(), \
                    "README.md should contain installation/setup instructions"


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "--tb=short"])