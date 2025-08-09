# mlflow/Dockerfile
# SIMPLIFIED to run as root to resolve persistent permission issues.
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install mlflow and its dependencies
RUN pip install mlflow[extras]

# Create the data directory
RUN mkdir /mlflow_data

# Expose the port
EXPOSE 5001

# The command to run the server.
# This will run as root, which has permissions to write to the volume.
CMD ["mlflow", "server", \
     "--backend-store-uri", "sqlite:////mlflow_data/mlflow.db", \
     "--default-artifact-root", "/mlflow_data/artifacts", \
     "--host", "0.0.0.0", \
     "--port", "5001"]
