#!/usr/bin/env python3
"""
Script to create dummy model files for container deployment
"""
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import numpy as np
import os

def create_dummy_models():
    """Create dummy model files if they don't exist"""
    print('Creating model files for container...')
    
    # Ensure artifacts directory exists
    os.makedirs('./artifacts', exist_ok=True)
    
    # Create dummy model and scaler
    model = LogisticRegression(random_state=42)
    scaler = StandardScaler()
    
    # Generate dummy training data
    X = np.random.RandomState(42).rand(100, 4)
    y = np.random.RandomState(42).choice(['setosa', 'versicolor', 'virginica'], 100)
    
    # Fit the models
    X_scaled = scaler.fit_transform(X)
    model.fit(X_scaled, y)
    
    # Save the models
    joblib.dump(model, './artifacts/best_model.pkl')
    joblib.dump(scaler, './artifacts/scaler.pkl')
    
    print('✅ Model files created successfully')
    print(f'   - Model: ./artifacts/best_model.pkl')
    print(f'   - Scaler: ./artifacts/scaler.pkl')

if __name__ == '__main__':
    create_dummy_models()