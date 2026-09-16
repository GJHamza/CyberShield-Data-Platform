"""
CyberShield Data Platform - ML Module
Inference Pipeline: Runs Preprocessing, Feature Engineering, Risk Scoring, and Anomaly Detection,
then saves results idempotently to PostgreSQL security_event_ml.
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "../.."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from datetime import datetime, timezone
import pandas as pd
from sqlalchemy import text

from services.ml.data_loader import load_security_events, get_engine
from services.ml.preprocessing import preprocess_data
from services.ml.feature_engineering import extract_features
from services.ml.risk_scoring import compute_risk_scores
from services.ml.anomaly_detection import load_model, predict_anomalies, train_anomaly_model, save_model

MODEL_VERSION = "v1.0.0"


def run_prediction(model_path=None, auto_train=True):
    """
    Execute full inference pipeline and save ML predictions to PostgreSQL.
    
    Args:
        model_path (str, optional): Path to joblib model file.
        auto_train (bool): If True and model file is missing, train a new model automatically.
        
    Returns:
        tuple: (results_df, inserted_updated_count)
    """
    print()
    print("=" * 60)
    print("  CYBERSHIELD ML - INFERENCE & SCORING PIPELINE")
    print(f"  Started at: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    # 1. Load Security Events
    print("\n[STEP 1/6] Loading security events from PostgreSQL...")
    raw_df = load_security_events()

    if raw_df is None or raw_df.empty:
        print("[WARNING] Prediction aborted: No security events found in PostgreSQL.")
        return pd.DataFrame(), 0

    records_count = len(raw_df)
    print(f"[STEP 1/6] Total events to process: {records_count}")

    # 2. Preprocess Data
    print("\n[STEP 2/6] Preprocessing data...")
    clean_df = preprocess_data(raw_df)
    print("[STEP 2/6] Preprocessing complete [OK]")

    # 3. Extract Features
    print("\n[STEP 3/6] Extracting features...")
    features_df, _ = extract_features(clean_df)
    print("[STEP 3/6] Feature extraction complete [OK]")

    # 4. Compute Risk Scores
    print("\n[STEP 4/6] Computing Risk Scores & Risk Levels...")
    risk_df = compute_risk_scores(clean_df)
    print("[STEP 4/6] Risk Scoring complete [OK]")

    # 5. Anomaly Detection
    print("\n[STEP 5/6] Running Anomaly Detection...")
    try:
        model = load_model(model_path)
    except FileNotFoundError:
        if auto_train:
            print("[INFO] Trained model not found. Automatically training a new model...")
            model = train_anomaly_model(features_df)
            save_model(model, filepath=model_path)
        else:
            raise

    anomalies_df = predict_anomalies(model, features_df)
    print("[STEP 5/6] Anomaly Detection complete [OK]")

    # Combine Results
    results_df = pd.DataFrame({
        "event_id": clean_df["event_id"],
        "risk_score": risk_df["risk_score"],
        "risk_level": risk_df["risk_level"],
        "anomaly_score": anomalies_df["anomaly_score"],
        "is_anomaly": anomalies_df["is_anomaly"],
        "model_version": MODEL_VERSION,
    })

    # 6. Save to PostgreSQL (Idempotent Upsert)
    print("\n[STEP 6/6] Saving ML predictions to PostgreSQL security_event_ml...")
    upsert_count = save_ml_results_to_postgres(results_df)
    print(f"[STEP 6/6] Idempotent upsert complete ({upsert_count} records updated/inserted) [OK]")

    # Display Breakdown Summary
    print()
    print("=" * 60)
    print("  INFERENCE PIPELINE COMPLETE [SUCCESS]")
    print("=" * 60)
    print(f"  Processed Events    : {records_count}")
    print(f"  Upserted to PG      : {upsert_count}")
    print(f"  Anomalies Detected  : {results_df['is_anomaly'].sum()} ({results_df['is_anomaly'].mean()*100:.1f}%)")
    print(f"  Risk Level Breakdown:")
    for level, count in results_df["risk_level"].value_counts().items():
        print(f"    - {level:<10}: {count}")
    print("=" * 60)
    print()

    return results_df, upsert_count


def save_ml_results_to_postgres(df):
    """
    Save ML prediction results to PostgreSQL security_event_ml using ON CONFLICT DO UPDATE.
    Guarantees idempotency (no duplicates).
    """
    if df is None or df.empty:
        return 0

    engine = get_engine()

    upsert_sql = text("""
        INSERT INTO security_event_ml (
            event_id, risk_score, risk_level, anomaly_score, is_anomaly, model_version, processed_at
        )
        VALUES (
            :event_id, :risk_score, :risk_level, :anomaly_score, :is_anomaly, :model_version, CURRENT_TIMESTAMP
        )
        ON CONFLICT (event_id) DO UPDATE SET
            risk_score = EXCLUDED.risk_score,
            risk_level = EXCLUDED.risk_level,
            anomaly_score = EXCLUDED.anomaly_score,
            is_anomaly = EXCLUDED.is_anomaly,
            model_version = EXCLUDED.model_version,
            processed_at = CURRENT_TIMESTAMP
    """)

    records = df.to_dict(orient="records")

    with engine.begin() as conn:
        for record in records:
            conn.execute(upsert_sql, {
                "event_id": str(record["event_id"]),
                "risk_score": float(record["risk_score"]),
                "risk_level": str(record["risk_level"]),
                "anomaly_score": float(record["anomaly_score"]),
                "is_anomaly": bool(record["is_anomaly"]),
                "model_version": str(record["model_version"]),
            })

    return len(records)


if __name__ == "__main__":
    run_prediction()
