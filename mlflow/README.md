# MLflow Server for Render

This directory contains the MLflow server setup optimized for Render deployment.

## Components

- `Dockerfile` - Container definition for MLflow server
- `mlflow_server.py` - Flask wrapper that provides `/health` endpoint and proxies to MLflow

## Features

- **Health Check Endpoint**: `/health` for Render's health monitoring
- **PostgreSQL Backend**: Uses Render's managed PostgreSQL for experiment tracking
- **Artifact Storage**: Stores artifacts in container (ephemeral on free tier)
- **Auto-proxy**: All MLflow UI and API requests are proxied through the wrapper

## Environment Variables

- `MLFLOW_BACKEND_STORE_URI` - Database connection (set by Render from PostgreSQL service)
- `MLFLOW_DEFAULT_ARTIFACT_ROOT` - Artifact storage location
- `PORT` - Port for the service (set by Render)

## Deployment

This service is automatically deployed by Render when you push to your repository. The `render.yaml` configuration handles the deployment.

## Access

Once deployed, you can access:
- MLflow UI: `https://mlflow-server-[your-id].onrender.com`
- Health Check: `https://mlflow-server-[your-id].onrender.com/health`
- API: `https://mlflow-server-[your-id].onrender.com/api/2.0/mlflow/...`

## Local Testing

To test locally:

```bash
cd mlflow
docker build -t mlflow-server .
docker run -p 5001:5001 -e MLFLOW_BACKEND_STORE_URI=sqlite:///mlflow.db mlflow-server
```

Then visit http://localhost:5001/health to verify it's working.