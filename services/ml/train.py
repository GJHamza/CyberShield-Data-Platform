"""
CyberShield Data Platform - ML Module
Training Pipeline: Loads events, preprocesses, extracts features, trains IsolationForest, and persists model.
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "../.."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from datetime import datetime, timezone

from services.ml.data_loader import load_security_events
from services.ml.preprocessing import preprocess_data
from services.ml.feature_engineering import extract_features
from services.ml.anomaly_detection import train_anomaly_model, save_model, predict_anomalies


def run_training(contamination=0.1, random_state=42, model_path=None):
    """
    Execute full training pipeline for CyberShield Anomaly Detection model.
    """
    print()
    print("=" * 60)
    print("  CYBERSHIELD ML - MODEL TRAINING PIPELINE")
    print(f"  Started at: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    # 1. Load Data
    print("\n[STEP 1/5] Loading security events from PostgreSQL...")
    raw_df = load_security_events()

    if raw_df is None or raw_df.empty:
        print("[FATAL] Training aborted: No security events found in PostgreSQL.")
        sys.exit(1)

    records_count = len(raw_df)
    print(f"[STEP 1/5] Total records loaded: {records_count}")

    # 2. Preprocess Data
    print("\n[STEP 2/5] Preprocessing security events data...")
    clean_df = preprocess_data(raw_df)
    print("[STEP 2/5] Preprocessing complete [OK]")

    # 3. Feature Engineering
    print("\n[STEP 3/5] Extracting numerical features...")
    features_df, feature_names = extract_features(clean_df)
    print(f"[STEP 3/5] Extracted {len(feature_names)} features: {feature_names}")

    # 4. Train IsolationForest
    print("\n[STEP 4/5] Training IsolationForest anomaly detection model...")
    model = train_anomaly_model(
        features_df,
        contamination=contamination,
        random_state=random_state,
    )

    # Calculate initial anomaly count on training set for summary
    preds_df = predict_anomalies(model, features_df)
    anomalies_count = preds_df["is_anomaly"].sum()

    # 5. Save Model
    print("\n[STEP 5/5] Persisting trained model to disk...")
    saved_path = save_model(model, filepath=model_path)

    # Summary
    print()
    print("=" * 60)
    print("  TRAINING PIPELINE COMPLETE [SUCCESS]")
    print("=" * 60)
    print(f"  Records Processed : {records_count}")
    print(f"  Features Extracted: {len(feature_names)}")
    print(f"  Model Type        : IsolationForest (n_trees=100, contamination={contamination})")
    print(f"  Detected Anomalies: {anomalies_count} ({anomalies_count/records_count*100:.1f}%)")
    print(f"  Model Saved To    : {saved_path}")
    print("=" * 60)
    print()

    return model, saved_path


if __name__ == "__main__":
    run_training()
