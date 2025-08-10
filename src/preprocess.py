"""Data preprocessing for Iris classification."""

import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


def load_data(file_path):
    """Load the Iris dataset"""
    return pd.read_csv(file_path)


def preprocess_data(df):
    """Preprocess the data and return train/test splits"""
    # Separate features and target
    X = df.drop("species", axis=1)
    y = df["species"]
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Save scaler for later use
    os.makedirs("artifacts", exist_ok=True)
    joblib.dump(scaler, "artifacts/scaler.pkl")
    
    # Split data
    return train_test_split(X_scaled, y, test_size=0.2, random_state=42)
