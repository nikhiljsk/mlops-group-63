#!/usr/bin/env python3
"""
Create dummy model files for testing in CI/CD environment.
This ensures tests can run without requiring actual model training.
"""

import os
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


def create_dummy_models():
    """Create minimal dummy models for testing"""
    print("Creating dummy models for testing...")
    
    # Create artifacts directory
    os.makedirs("artifacts", exist_ok=True)
    
    # Create dummy data
    X_dummy = np.array([[5.1, 3.5, 1.4, 0.2], [6.2, 2.9, 4.3, 1.3], [6.5, 3.0, 5.2, 2.0]])
    y_dummy = np.array([0, 1, 2])  # setosa, versicolor, virginica
    
    # Create and train a simple model
    model = LogisticRegression(random_state=42)
    model.fit(X_dummy, y_dummy)
    
    # Create and fit scaler
    scaler = StandardScaler()
    scaler.fit(X_dummy)
    
    # Save dummy models
    joblib.dump(model, "artifacts/best_model.pkl")
    joblib.dump(scaler, "artifacts/scaler.pkl")
    
    print("✅ Dummy models created:")
    print("  - artifacts/best_model.pkl")
    print("  - artifacts/scaler.pkl")


if __name__ == "__main__":
    create_dummy_models()