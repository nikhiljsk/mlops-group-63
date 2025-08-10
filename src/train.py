"""Train Iris classification models with MLflow tracking."""

import os
import joblib
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
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
    
    # Define models to train
    models = [
        (LogisticRegression(random_state=42), "LogisticRegression"),
        (RandomForestClassifier(random_state=42), "RandomForest"),
        (SVC(random_state=42), "SVM"),
        (KNeighborsClassifier(), "KNN"),
        (GaussianNB(), "NaiveBayes")
    ]
    
    # Train all models
    model_results = []
    for model, name in models:
        trained_model, metrics = train_and_evaluate_model(
            model, X_train, X_test, y_train, y_test, name
        )
        model_results.append((trained_model, metrics, name))
    
    # Select best model based on F1 score
    best_model, best_metrics, best_name = max(model_results, key=lambda x: x[1]["f1_score"])
    print(f"🏆 Best model: {best_name} (F1: {best_metrics['f1_score']:.4f})")
    
    # Save best model
    joblib.dump(best_model, "artifacts/best_model.pkl")
    print("✅ Best model saved to 'artifacts/best_model.pkl'")
    print("🎉 Training completed!")
