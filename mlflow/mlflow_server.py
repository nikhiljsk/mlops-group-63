#!/usr/bin/env python3
"""
MLflow server wrapper with health endpoint for Render deployment
"""
import os
import subprocess
import threading
import time
from flask import Flask, jsonify
import requests

app = Flask(__name__)

# Global variable to track MLflow server status
mlflow_process = None
mlflow_ready = False

def start_mlflow_server():
    """Start MLflow server in background"""
    global mlflow_process, mlflow_ready
    
    # Get environment variables
    backend_store_uri = os.getenv('MLFLOW_BACKEND_STORE_URI', 'sqlite:///mlflow/backend/mlflow.db')
    artifact_root = os.getenv('MLFLOW_DEFAULT_ARTIFACT_ROOT', '/mlflow/artifacts')
    
    # Start MLflow server
    cmd = [
        'mlflow', 'server',
        '--host', '0.0.0.0',
        '--port', '5000',  # Internal MLflow port
        '--backend-store-uri', backend_store_uri,
        '--default-artifact-root', artifact_root,
        '--serve-artifacts'
    ]
    
    print(f"Starting MLflow server with command: {' '.join(cmd)}")
    mlflow_process = subprocess.Popen(cmd)
    
    # Wait for MLflow to be ready
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get('http://localhost:5000/api/2.0/mlflow/experiments/list', timeout=5)
            if response.status_code == 200:
                mlflow_ready = True
                print("MLflow server is ready!")
                break
        except:
            pass
        time.sleep(1)
    
    if not mlflow_ready:
        print("MLflow server failed to start properly")

@app.route('/health')
def health():
    """Health check endpoint for Render"""
    if mlflow_ready:
        try:
            # Check if MLflow is still responding
            response = requests.get('http://localhost:5000/api/2.0/mlflow/experiments/list', timeout=5)
            if response.status_code == 200:
                return jsonify({
                    'status': 'healthy',
                    'mlflow_status': 'running',
                    'backend_store': os.getenv('MLFLOW_BACKEND_STORE_URI', 'sqlite'),
                    'artifact_root': os.getenv('MLFLOW_DEFAULT_ARTIFACT_ROOT', '/mlflow/artifacts')
                }), 200
        except:
            pass
    
    return jsonify({
        'status': 'unhealthy',
        'mlflow_status': 'not ready'
    }), 503

@app.route('/')
def root():
    """Root endpoint - redirect to MLflow UI"""
    if mlflow_ready:
        return '''
        <h1>MLflow Server</h1>
        <p>MLflow server is running!</p>
        <p><a href="http://localhost:5000">Access MLflow UI (internal)</a></p>
        <p><a href="/health">Health Check</a></p>
        '''
    else:
        return '<h1>MLflow Server Starting...</h1><p>Please wait while MLflow initializes.</p>'

# Proxy all other requests to MLflow
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_to_mlflow(path):
    """Proxy requests to MLflow server"""
    if not mlflow_ready:
        return jsonify({'error': 'MLflow server not ready'}), 503
    
    try:
        import requests
        from flask import request
        
        # Forward the request to MLflow
        url = f'http://localhost:5000/{path}'
        
        if request.method == 'GET':
            response = requests.get(url, params=request.args, timeout=30)
        elif request.method == 'POST':
            response = requests.post(url, json=request.get_json(), params=request.args, timeout=30)
        elif request.method == 'PUT':
            response = requests.put(url, json=request.get_json(), params=request.args, timeout=30)
        elif request.method == 'DELETE':
            response = requests.delete(url, params=request.args, timeout=30)
        
        return response.content, response.status_code, response.headers.items()
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Start MLflow server in background thread
    mlflow_thread = threading.Thread(target=start_mlflow_server, daemon=True)
    mlflow_thread.start()
    
    # Start Flask wrapper on port 5001 (Render's expected port)
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)