# mlflow/Dockerfile
FROM python:3.11-slim

# Install system dependencies, including curl for the healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Create a non-root user and group
RUN addgroup --system mlflow && adduser --system --ingroup mlflow mlflow

# Create directories for the database and artifacts and set ownership
RUN mkdir /db /mlruns && chown -R mlflow:mlflow /db /mlruns

# Switch to the non-root user
USER mlflow

# Install mlflow and its dependencies
RUN pip install mlflow[extras]

# Expose the port
EXPOSE 5001

# The command to run the server
CMD ["mlflow", "server", \
     "--backend-store-uri", "sqlite:////db/mlflow.db", \
     "--default-artifact-root", "/mlruns", \
     "--host", "0.0.0.0", \
     "--port", "5001"]
