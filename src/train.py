"""Train Iris classification models with MLflow tracking."""

import os
import joblib
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score

from preprocess import load_data, preprocess_data


def train_and_evaluate_model(model, X_train, X_test, y_train, y_test, model_name):
    """Train model and log metrics to MLflow"""
    with mlflow.start_run(run_name=model_name):
        # Train the model
        model.fit(X_train, y_train)
        
        # Make predictions and calculate metrics
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average="weighted")
        
        # Log parameters and metrics
        mlflow.log_param("model_type", model_name)
        mlflow.log_param("train_size", len(X_train))
        mlflow.log_param("test_size", len(X_test))
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("f1_score", f1)
        
        # Log the model
        mlflow.sklearn.log_model(model, "model")
        
        print(f"✅ {model_name} - Accuracy: {accuracy:.4f}, F1: {f1:.4f}")
        return model, {"accuracy": accuracy, "f1_score": f1}


if __name__ == "__main__":
    print("🚀 Starting model training...")
    
    # Load and preprocess data
    df = load_data("data/iris.csv")
    X_train, X_test, y_train, y_test = preprocess_data(df)
    
    # Create artifacts directory
    os.makedirs("artifacts", exist_ok=True)
    
    # Set up MLflow
    mlflow.set_tracking_uri("file:./mlruns")
    mlflow.set_experiment("Iris_Classification")
    
    # Train models
    lr_model, lr_metrics = train_and_evaluate_model(
        LogisticRegression(random_state=42), 
        X_train, X_test, y_train, y_test, 
        "LogisticRegression"
    )
    
    rf_model, rf_metrics = train_and_evaluate_model(
        RandomForestClassifier(random_state=42), 
        X_train, X_test, y_train, y_test, 
        "RandomForest"
    )
    
    # Select best model
    if rf_metrics["f1_score"] > lr_metrics["f1_score"]:
        best_model = rf_model
        best_name = "RandomForest"
        print(f"🏆 Best model: RandomForest (F1: {rf_metrics['f1_score']:.4f})")
    else:
        best_model = lr_model
        best_name = "LogisticRegression"
        print(f"🏆 Best model: LogisticRegression (F1: {lr_metrics['f1_score']:.4f})")
    
    # Save best model
    joblib.dump(best_model, "artifacts/best_model.pkl")
    print("✅ Best model saved to 'artifacts/best_model.pkl'")
    print("🎉 Training completed!")
