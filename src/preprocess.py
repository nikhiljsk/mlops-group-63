# src/preprocess.py

import os

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


def load_data(file_path):
    return pd.read_csv(file_path)


def preprocess_data(df):
    X = df.drop("species", axis=1)
    y = df["species"]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Save the scaler for future use in prediction
    os.makedirs("artifacts", exist_ok=True)
    joblib.dump(scaler, "artifacts/scaler.pkl")

    return train_test_split(X_scaled, y, test_size=0.2, random_state=42)


if __name__ == "__main__":
    df = load_data("data/iris.csv")
    X_train, X_test, y_train, y_test = preprocess_data(df)

    # Optionally save splits if needed
    joblib.dump((X_train, X_test, y_train, y_test), "artifacts/train_test_split.pkl")
    print("✅ Data preprocessing completed and saved to 'artifacts/'")
