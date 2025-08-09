#!/usr/bin/env python3
"""
Advanced Deployment Manager for Iris Classification API
Handles multi-environment deployments with configuration management
"""

import os
import sys
import yaml
import json
import subprocess
import argparse
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('deploy/logs/deployment.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'  # No Color

class DeploymentManager:
    """Advanced deployment manager with multi-environment support"""
    
    def __init__(self, config_path: str = "deploy/config/environments.yml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.docker_hub_username = os.getenv('DOCKER_HUB_USERNAME', 'your-username')
        
        # Ensure log directory exists
        os.makedirs('deploy/logs', exist_ok=True)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load deployment configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration file: {e}")
            sys.exit(1)
    
    def _print_status(self, message: str, color: str = Colors.GREEN):
        """Print colored status message"""
        print(f"{color}✅ {message}{Colors.NC}")
        logger.info(message)
    
    def _print_info(self, message: str):
        """Print info message"""
        print(f"{Colors.BLUE}ℹ️  {message}{Colors.NC}")
        logger.info(message)
    
    def _print_warning(self, message: str):
        """Print warning message"""
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.NC}")
        logger.warning(message)
    
    def _print_error(self, message: str):
        """Print error message"""
        print(f"{Colors.RED}❌ {message}{Colors.NC}")
        logger.error(message)
    
    def _run_command(self, command: str, check: bool = True) -> subprocess.CompletedProcess:
        """Run shell command with logging"""
        logger.info(f"Executing: {command}")
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                check=check
            )
            if result.stdout:
                logger.debug(f"STDOUT: {result.stdout}")
            if result.stderr:
                logger.debug(f"STDERR: {result.stderr}")
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {command}")
            logger.error(f"Error: {e.stderr}")
            raise
    
    def list_environments(self):
        """List available deployment environments"""
        print(f"\n{Colors.CYAN}📋 Available Deployment Environments{Colors.NC}")
        print("=" * 50)
        
        for env_name, env_config in self.config['environments'].items():
            print(f"\n{Colors.WHITE}{env_name.upper()}{Colors.NC}")
            print(f"  Name: {env_config['name']}")
            print(f"  Description: {env_config['description']}")
            print(f"  Port: {env_config['docker']['port']}")
            print(f"  Container: {env_config['docker']['container_name']}")
            print(f"  Monitoring: {'✅' if env_config.get('monitoring', {}).get('prometheus', False) else '❌'}")
    
    def validate_environment(self, environment: str) -> Dict[str, Any]:
        """Validate and return environment configuration"""
        if environment not in self.config['environments']:
            self._print_error(f"Environment '{environment}' not found")
            self._print_info("Available environments:")
            for env in self.config['environments'].keys():
                print(f"  - {env}")
            sys.exit(1)
        
        return self.config['environments'][environment]
    
    def check_prerequisites(self) -> bool:
        """Check deployment prerequisites"""
        self._print_info("Checking deployment prerequisites...")
        
        # Check Docker
        try:
            result = self._run_command("docker --version")
            self._print_status("Docker is available")
        except subprocess.CalledProcessError:
            self._print_error("Docker is not installed or not accessible")
            return False
        
        # Check Docker daemon
        try:
            self._run_command("docker info")
            self._print_status("Docker daemon is running")
        except subprocess.CalledProcessError:
            self._print_error("Docker daemon is not running")
            return False
        
        # Check Docker Compose
        try:
            self._run_command("docker-compose --version")
            self._print_status("Docker Compose is available")
        except subprocess.CalledProcessError:
            self._print_warning("Docker Compose not found, using docker compose")
        
        return True
    
    def pull_image(self, environment: str, env_config: Dict[str, Any]) -> bool:
        """Pull Docker image for deployment"""
        image_tag = env_config['docker']['image_tag']
        image_name = f"{self.docker_hub_username}/{self.config['global']['image_name']}:{image_tag}"
        
        self._print_info(f"Pulling Docker image: {image_name}")
        
        try:
            self._run_command(f"docker pull {image_name}")
            self._print_status(f"Successfully pulled image: {image_name}")
            return True
        except subprocess.CalledProcessError:
            self._print_error(f"Failed to pull image: {image_name}")
            return False
    
    def stop_existing_container(self, container_name: str):
        """Stop and remove existing container"""
        self._print_info(f"Checking for existing container: {container_name}")
        
        # Check if container exists
        result = self._run_command(
            f"docker ps -a --format 'table {{{{.Names}}}}' | grep -q '^{container_name}$'",
            check=False
        )
        
        if result.returncode == 0:
            self._print_info(f"Stopping existing container: {container_name}")
            self._run_command(f"docker stop {container_name}", check=False)
            
            self._print_info(f"Removing existing container: {container_name}")
            self._run_command(f"docker rm {container_name}", check=False)
            
            self._print_status("Existing container removed")
        else:
            self._print_info("No existing container found")
    
    def create_volumes(self, env_config: Dict[str, Any]):
        """Create necessary directories and volumes"""
        self._print_info("Creating necessary directories...")
        
        volumes = env_config.get('volumes', [])
        for volume in volumes:
            if ':' in volume:
                host_path = volume.split(':')[0]
                if host_path.startswith('./') or host_path.startswith('/'):
                    # Create host directory
                    os.makedirs(host_path, exist_ok=True)
                    self._print_info(f"Created directory: {host_path}")
    
    def generate_docker_run_command(self, environment: str, env_config: Dict[str, Any]) -> str:
        """Generate Docker run command from configuration"""
        image_tag = env_config['docker']['image_tag']
        image_name = f"{self.docker_hub_username}/{self.config['global']['image_name']}:{image_tag}"
        
        cmd_parts = [
            "docker run -d",
            f"--name {env_config['docker']['container_name']}",
            f"--restart {env_config['docker']['restart_policy']}",
            f"-p {env_config['docker']['port']}:8000"
        ]
        
        # Add environment variables
        for key, value in env_config['environment_vars'].items():
            cmd_parts.append(f"-e {key}={value}")
        
        # Add volumes
        for volume in env_config.get('volumes', []):
            cmd_parts.append(f"-v {volume}")
        
        # Add resource limits
        if 'resources' in env_config:
            if 'memory' in env_config['resources']:
                cmd_parts.append(f"--memory={env_config['resources']['memory']}")
            if 'cpus' in env_config['resources']:
                cmd_parts.append(f"--cpus={env_config['resources']['cpus']}")
        
        # Add security settings
        if 'security' in env_config:
            if 'user' in env_config['security']:
                cmd_parts.append(f"--user {env_config['security']['user']}")
            if env_config['security'].get('read_only', False):
                cmd_parts.append("--read-only")
            if env_config['security'].get('no_new_privileges', False):
                cmd_parts.append("--security-opt no-new-privileges")
        
        # Add network
        network_name = self.config['global']['network_name']
        cmd_parts.append(f"--network {network_name}")
        
        # Add image name
        cmd_parts.append(image_name)
        
        return " \\\n  ".join(cmd_parts)
    
    def deploy_container(self, environment: str, env_config: Dict[str, Any]) -> bool:
        """Deploy the container"""
        container_name = env_config['docker']['container_name']
        
        self._print_info(f"Deploying container: {container_name}")
        
        # Generate and execute Docker run command
        docker_cmd = self.generate_docker_run_command(environment, env_config)
        
        try:
            self._run_command(docker_cmd)
            self._print_status(f"Container {container_name} started successfully")
            return True
        except subprocess.CalledProcessError:
            self._print_error(f"Failed to start container: {container_name}")
            return False
    
    def wait_for_health(self, env_config: Dict[str, Any], timeout: int = 300) -> bool:
        """Wait for container to become healthy"""
        port = env_config['docker']['port']
        health_url = f"http://localhost:{port}/health"
        container_name = env_config['docker']['container_name']
        
        self._print_info(f"Waiting for container to become healthy...")
        self._print_info(f"Health check URL: {health_url}")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(health_url, timeout=10)
                if response.status_code == 200:
                    health_data = response.json()
                    if health_data.get('status') in ['healthy', 'degraded']:
                        self._print_status("Container is healthy!")
                        return True
            except requests.exceptions.RequestException:
                pass
            
            # Check if container is still running
            result = self._run_command(
                f"docker ps --filter name={container_name} --format '{{{{.Names}}}}'",
                check=False
            )
            
            if container_name not in result.stdout:
                self._print_error("Container stopped unexpectedly")
                # Show container logs
                self._run_command(f"docker logs {container_name}", check=False)
                return False
            
            time.sleep(10)
            print(".", end="", flush=True)
        
        print()  # New line after dots
        self._print_error(f"Health check timeout after {timeout} seconds")
        return False
    
    def run_post_deployment_tests(self, env_config: Dict[str, Any]) -> bool:
        """Run post-deployment tests"""
        port = env_config['docker']['port']
        base_url = f"http://localhost:{port}"
        
        self._print_info("Running post-deployment tests...")
        
        tests = [
            {
                'name': 'Health Check',
                'url': f"{base_url}/health",
                'method': 'GET',
                'expected_status': 200
            },
            {
                'name': 'Model Info',
                'url': f"{base_url}/model/info",
                'method': 'GET',
                'expected_status': 200
            },
            {
                'name': 'Prediction Test',
                'url': f"{base_url}/predict",
                'method': 'POST',
                'data': {
                    'sepal_length': 5.1,
                    'sepal_width': 3.5,
                    'petal_length': 1.4,
                    'petal_width': 0.2
                },
                'expected_status': 200
            },
            {
                'name': 'Metrics Endpoint',
                'url': f"{base_url}/metrics",
                'method': 'GET',
                'expected_status': 200
            }
        ]
        
        all_passed = True
        for test in tests:
            try:
                if test['method'] == 'GET':
                    response = requests.get(test['url'], timeout=10)
                elif test['method'] == 'POST':
                    response = requests.post(test['url'], json=test['data'], timeout=10)
                
                if response.status_code == test['expected_status']:
                    self._print_status(f"✅ {test['name']} - PASSED")
                else:
                    self._print_error(f"❌ {test['name']} - FAILED (Status: {response.status_code})")
                    all_passed = False
                    
            except requests.exceptions.RequestException as e:
                self._print_error(f"❌ {test['name']} - FAILED (Error: {e})")
                all_passed = False
        
        return all_passed
    
    def generate_deployment_summary(self, environment: str, env_config: Dict[str, Any]):
        """Generate deployment summary"""
        container_name = env_config['docker']['container_name']
        port = env_config['docker']['port']
        image_tag = env_config['docker']['image_tag']
        
        print(f"\n{Colors.GREEN}🎉 Deployment Summary{Colors.NC}")
        print("=" * 50)
        print(f"Environment: {Colors.WHITE}{environment.upper()}{Colors.NC}")
        print(f"Container: {container_name}")
        print(f"Image Tag: {image_tag}")
        print(f"Port: {port}")
        print(f"Status: {Colors.GREEN}✅ DEPLOYED{Colors.NC}")
        print(f"Deployed At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n{Colors.CYAN}📍 Available Endpoints:{Colors.NC}")
        print(f"  🌐 API Base:     http://localhost:{port}")
        print(f"  🏥 Health:       http://localhost:{port}/health")
        print(f"  📊 Prediction:   http://localhost:{port}/predict")
        print(f"  📈 Metrics:      http://localhost:{port}/metrics")
        print(f"  📚 API Docs:     http://localhost:{port}/docs")
        
        print(f"\n{Colors.CYAN}🛠️  Management Commands:{Colors.NC}")
        print(f"  View logs:       docker logs {container_name}")
        print(f"  Stop container:  docker stop {container_name}")
        print(f"  Start container: docker start {container_name}")
        print(f"  Remove:          docker stop {container_name} && docker rm {container_name}")
    
    def deploy(self, environment: str, skip_tests: bool = False, force: bool = False) -> bool:
        """Main deployment function"""
        print(f"\n{Colors.PURPLE}🚀 Starting Deployment to {environment.upper()}{Colors.NC}")
        print("=" * 60)
        
        # Validate environment
        env_config = self.validate_environment(environment)
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
        
        # Confirmation prompt (unless forced)
        if not force:
            container_name = env_config['docker']['container_name']
            port = env_config['docker']['port']
            
            print(f"\n{Colors.YELLOW}⚠️  Deployment Configuration:{Colors.NC}")
            print(f"  Environment: {environment}")
            print(f"  Container: {container_name}")
            print(f"  Port: {port}")
            print(f"  Image: {self.docker_hub_username}/{self.config['global']['image_name']}:{env_config['docker']['image_tag']}")
            
            response = input(f"\nProceed with deployment? (y/N): ")
            if response.lower() != 'y':
                self._print_info("Deployment cancelled")
                return False
        
        try:
            # Pull image
            if not self.pull_image(environment, env_config):
                return False
            
            # Stop existing container
            self.stop_existing_container(env_config['docker']['container_name'])
            
            # Create volumes
            self.create_volumes(env_config)
            
            # Deploy container
            if not self.deploy_container(environment, env_config):
                return False
            
            # Wait for health
            if not self.wait_for_health(env_config):
                return False
            
            # Run tests
            if not skip_tests:
                if not self.run_post_deployment_tests(env_config):
                    self._print_warning("Some post-deployment tests failed")
            
            # Generate summary
            self.generate_deployment_summary(environment, env_config)
            
            return True
            
        except Exception as e:
            self._print_error(f"Deployment failed: {e}")
            logger.exception("Deployment failed with exception")
            return False

def main():
    """Main function with CLI interface"""
    parser = argparse.ArgumentParser(description="Advanced Deployment Manager for Iris Classification API")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List environments command
    list_parser = subparsers.add_parser('list', help='List available environments')
    
    # Deploy command
    deploy_parser = subparsers.add_parser('deploy', help='Deploy to environment')
    deploy_parser.add_argument('environment', help='Target environment (development, staging, production)')
    deploy_parser.add_argument('--skip-tests', action='store_true', help='Skip post-deployment tests')
    deploy_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    deploy_parser.add_argument('--config', default='deploy/config/environments.yml', help='Configuration file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize deployment manager
    config_path = getattr(args, 'config', 'deploy/config/environments.yml')
    manager = DeploymentManager(config_path)
    
    if args.command == 'list':
        manager.list_environments()
    
    elif args.command == 'deploy':
        success = manager.deploy(
            environment=args.environment,
            skip_tests=args.skip_tests,
            force=args.force
        )
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()