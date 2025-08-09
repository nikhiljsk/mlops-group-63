# src/train.py

import mlflow
import mlflow.sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
)
from sklearn.model_selection import cross_val_score
import joblib
import os
import numpy as np
from datetime import datetime

from preprocess import load_data, preprocess_data


def evaluate_model_performance(model, X_train, X_test, y_train, y_test):
    """Calculate comprehensive metrics for model evaluation"""
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)

    # Calculate cross-validation scores for more robust evaluation
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="accuracy")

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, average="weighted"),
        "recall": recall_score(y_test, y_pred, average="weighted"),
        "f1_score": f1_score(y_test, y_pred, average="weighted"),
        "cv_mean": cv_scores.mean(),
        "cv_std": cv_scores.std(),
    }

    return metrics, y_pred, y_pred_proba


def train_and_log_model(model, X_train, X_test, y_train, y_test, model_name):
    """Train model and log comprehensive metrics to MLflow"""
    with mlflow.start_run(
        run_name=f"{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    ):
        # Train the model
        model.fit(X_train, y_train)

        # Get comprehensive evaluation metrics
        metrics, y_pred, y_pred_proba = evaluate_model_performance(
            model, X_train, X_test, y_train, y_test
        )

        # Log model parameters
        mlflow.log_param("model_type", model_name)
        mlflow.log_param("train_size", len(X_train))
        mlflow.log_param("test_size", len(X_test))
        mlflow.log_param("features", X_train.shape[1])

        # Log all metrics
        for metric_name, metric_value in metrics.items():
            mlflow.log_metric(metric_name, metric_value)

        # Log the model with signature for better registry integration
        signature = mlflow.models.infer_signature(X_test, y_pred_proba)
        mlflow.sklearn.log_model(
            model, artifact_path="model", signature=signature, input_example=X_test[:1]
        )

        # Log classification report as artifact
        report = classification_report(y_test, y_pred, output_dict=True)
        mlflow.log_dict(report, "classification_report.json")

        print(
            f"✅ {model_name} - Accuracy: {metrics['accuracy']:.4f}, F1: {metrics['f1_score']:.4f}"
        )
        return model, metrics


def register_best_model(model_name, run_id, model_metrics):
    """Register the best model in MLflow Model Registry"""
    try:
        # Create registered model if it doesn't exist
        try:
            mlflow.create_registered_model(model_name)
        except mlflow.exceptions.RestException:
            # Model already exists
            pass

        # Create model version
        model_version = mlflow.register_model(
            model_uri=f"runs:/{run_id}/model", name=model_name
        )

        # Add description with metrics
        description = f"Accuracy: {model_metrics['accuracy']:.4f}, F1: {model_metrics['f1_score']:.4f}"
        mlflow.update_model_version(
            name=model_name, version=model_version.version, description=description
        )

        print(f"✅ Model registered as {model_name} version {model_version.version}")
        return model_version
    except Exception as e:
        print(f"⚠️ Model registration failed: {e}")
        return None


if __name__ == "__main__":
    # Load and preprocess data
    df = load_data("data/iris.csv")
    X_train, X_test, y_train, y_test = preprocess_data(df)

    os.makedirs("artifacts", exist_ok=True)

    # Set up MLflow tracking - use local file store if server not available
    try:
        mlflow.set_tracking_uri("http://127.0.0.1:5000")
        # Test connection
        mlflow.get_experiment_by_name("test")
        print("✅ Connected to MLflow tracking server")
    except Exception:
        print("⚠️ MLflow server not available, using local file store")
        mlflow.set_tracking_uri("file:./mlruns")

    mlflow.set_experiment("Iris_Classifier")

    # Train Logistic Regression
    lr_model = LogisticRegression()
    lr_model, lr_metrics = train_and_log_model(
        lr_model, X_train, X_test, y_train, y_test, "LogisticRegression"
    )

    # Train Random Forest
    rf_model = RandomForestClassifier()
    rf_model, rf_metrics = train_and_log_model(
        rf_model, X_train, X_test, y_train, y_test, "RandomForest"
    )

    # Compare models and select the best one
    if rf_metrics["f1_score"] > lr_metrics["f1_score"]:
        best_model = rf_model
        best_metrics = rf_metrics
        best_model_name = "RandomForest"
        print(f"🏆 Best model: RandomForest (F1: {rf_metrics['f1_score']:.4f})")
    else:
        best_model = lr_model
        best_metrics = lr_metrics
        best_model_name = "LogisticRegression"
        print(f"🏆 Best model: LogisticRegression (F1: {lr_metrics['f1_score']:.4f})")

    # Save best model locally for fallback
    joblib.dump(best_model, "artifacts/best_model.pkl")
    print("✅ Best model saved to 'artifacts/best_model.pkl'")

    # Register best model in MLflow Model Registry
    current_run_id = mlflow.active_run().info.run_id if mlflow.active_run() else None
    if current_run_id:
        register_best_model("iris-classifier", current_run_id, best_metrics)
