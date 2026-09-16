"""
CyberShield Data Platform - ML Module
Anomaly Detection: Unsupervised anomaly detection using Scikit-Learn IsolationForest.
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "../.."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
DEFAULT_MODEL_PATH = os.path.join(MODEL_DIR, "isolation_forest.joblib")


def train_anomaly_model(X, contamination=0.1, random_state=42, n_estimators=100):
    """
    Train an IsolationForest model on numerical features X.
    
    Args:
        X (pd.DataFrame or np.ndarray): Feature matrix.
        contamination (float): Expected fraction of anomalies in dataset.
        random_state (int): Random seed for reproducibility.
        n_estimators (int): Number of trees in forest.
        
    Returns:
        IsolationForest: Trained Scikit-Learn model instance.
    """
    if X is None or len(X) == 0:
        raise ValueError("Cannot train IsolationForest model on empty feature matrix X")

    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(X)
    print(f"[ANOMALY MODEL] IsolationForest trained on {len(X)} samples with {X.shape[1]} features")
    return model


def save_model(model, filepath=None):
    """Save trained IsolationForest model to disk via joblib."""
    target_path = filepath or DEFAULT_MODEL_PATH
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    joblib.dump(model, target_path)
    print(f"[ANOMALY MODEL] Model saved to {target_path}")
    return target_path


def load_model(filepath=None):
    """Load IsolationForest model from disk via joblib."""
    target_path = filepath or DEFAULT_MODEL_PATH
    if not os.path.exists(target_path):
        raise FileNotFoundError(f"Model file not found at {target_path}. Train model first.")
    model = joblib.load(target_path)
    print(f"[ANOMALY MODEL] Loaded model from {target_path}")
    return model


def predict_anomalies(model, X):
    """
    Predict anomalies for feature matrix X.
    
    Args:
        model: Trained IsolationForest model.
        X (pd.DataFrame or np.ndarray): Feature matrix.
        
    Returns:
        pd.DataFrame: DataFrame containing:
            - anomaly_score (float): Inverted decision function (higher = more anomalous).
            - is_anomaly (bool): True if predicted as anomaly (-1 in IsolationForest), False otherwise.
    """
    if X is None or len(X) == 0:
        return pd.DataFrame(columns=["anomaly_score", "is_anomaly"])

    raw_scores = model.decision_function(X)
    preds = model.predict(X)  # -1 for anomaly, 1 for normal

    # Invert decision function so higher positive values indicate higher anomaly likelihood
    anomaly_scores = np.round(-raw_scores, 4)
    is_anomalies = (preds == -1)

    result_df = pd.DataFrame({
        "anomaly_score": anomaly_scores,
        "is_anomaly": is_anomalies,
    }, index=getattr(X, "index", None))

    return result_df


if __name__ == "__main__":
    from services.ml.data_loader import load_security_events
    from services.ml.preprocessing import preprocess_data
    from services.ml.feature_engineering import extract_features

    raw_df = load_security_events(limit=20)
    clean_df = preprocess_data(raw_df)
    features_df, _ = extract_features(clean_df)

    model = train_anomaly_model(features_df)
    save_model(model)
    loaded_model = load_model()

    anomalies_df = predict_anomalies(loaded_model, features_df)
    print("\nAnomaly Detection Results Sample:")
    print(anomalies_df.head().to_string())
