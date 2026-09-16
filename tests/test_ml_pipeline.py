"""
CyberShield Data Platform
End-to-End Test Suite: Machine Learning Pipeline (services/ml/)

Verifies:
1. ML Dependencies (pandas, numpy, sklearn, joblib, sqlalchemy)
2. PostgreSQL connection
3. Data loader functionality & column validation
4. Preprocessing robustness (handling nulls, formatting strings, port casting)
5. Feature engineering (12 numerical features extracted)
6. Risk scoring range (0-100) and classification (LOW, MEDIUM, HIGH, CRITICAL)
7. IsolationForest model training, saving, loading
8. Inference pipeline & PostgreSQL security_event_ml database write
9. Uniqueness of event_id in security_event_ml
10. Pipeline idempotency (N1 == N2 on re-run)
"""

import os
import sys
from datetime import datetime, timezone

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import pandas as pd
import numpy as np

from services.ml.data_loader import load_security_events, get_engine
from services.ml.preprocessing import preprocess_data
from services.ml.feature_engineering import extract_features, FEATURE_COLUMNS
from services.ml.risk_scoring import compute_risk_scores, classify_risk_level
from services.ml.anomaly_detection import (
    train_anomaly_model,
    save_model,
    load_model,
    predict_anomalies,
)
from services.ml.predict import run_prediction


# ============================================================
# Test Cases
# ============================================================

def test_1_dependencies():
    """Test 1: Verify all ML dependencies are installed."""
    print("[TEST 01] ML Dependencies availability... ", end="")
    import pandas
    import numpy
    import sklearn
    import joblib
    import sqlalchemy
    import psycopg2
    print("OK")


def test_2_postgres_connection():
    """Test 2: Verify PostgreSQL connection using SQLAlchemy."""
    print("[TEST 02] PostgreSQL SQLAlchemy connection... ", end="")
    engine = get_engine()
    with engine.connect() as conn:
        assert conn is not None, "Failed to connect to PostgreSQL"
    print("OK")


def test_3_data_loader_events():
    """Test 3: Verify loading security_events from PostgreSQL."""
    print("[TEST 03] Data Loader - load_security_events()... ", end="")
    df = load_security_events()
    assert df is not None, "Loaded DataFrame is None"
    assert not df.empty, "Loaded DataFrame is empty"
    print(f"OK ({len(df)} records loaded)")
    return df


def test_4_data_loader_columns(df):
    """Test 4: Verify expected columns in loaded DataFrame."""
    print("[TEST 04] Data Loader - required columns... ", end="")
    expected = {"event_id", "timestamp", "event_type", "severity", "source_ip", "destination_ip"}
    missing = expected - set(df.columns)
    assert not missing, f"Missing columns: {missing}"
    print("OK")


def test_5_preprocessing_basic(raw_df):
    """Test 5: Verify preprocessing clean data."""
    print("[TEST 05] Preprocessing - basic cleaning... ", end="")
    clean_df = preprocess_data(raw_df)
    assert len(clean_df) == len(raw_df), "Row count changed after preprocessing"
    assert clean_df["severity"].isin(["low", "medium", "high", "critical", "unknown"]).all(), "Invalid severity values"
    print("OK")
    return clean_df


def test_6_preprocessing_null_handling():
    """Test 6: Verify preprocessing handles null values robustly."""
    print("[TEST 06] Preprocessing - null value imputation... ", end="")
    dirty_df = pd.DataFrame([{
        "event_id": "evt-null-test",
        "event_type": None,
        "severity": None,
        "timestamp": None,
        "source_port": None,
        "destination_port": None,
    }])
    clean_df = preprocess_data(dirty_df)
    assert clean_df["event_type"].iloc[0] == "unknown"
    assert clean_df["severity"].iloc[0] == "unknown"
    assert clean_df["source_port"].iloc[0] == 0
    assert clean_df["destination_port"].iloc[0] == 0
    assert clean_df["timestamp"].iloc[0] is not None
    print("OK")


def test_7_feature_engineering_extraction(clean_df):
    """Test 7: Verify feature engineering extracts all expected features."""
    print("[TEST 07] Feature Engineering - extraction... ", end="")
    features_df, feature_names = extract_features(clean_df)
    assert list(feature_names) == FEATURE_COLUMNS, "Feature column names mismatch"
    assert features_df.shape[1] == len(FEATURE_COLUMNS), "Feature count mismatch"
    print(f"OK ({len(FEATURE_COLUMNS)} features)")
    return features_df


def test_8_feature_engineering_numeric_types(features_df):
    """Test 8: Verify feature matrix contains only numeric non-null values."""
    print("[TEST 08] Feature Engineering - numeric types & non-null... ", end="")
    assert not features_df.isnull().any().any(), "Features contain null values"
    for col in features_df.columns:
        assert np.issubdtype(features_df[col].dtype, np.number), f"Non-numeric column: {col}"
    print("OK")


def test_9_risk_scoring_range(clean_df):
    """Test 9: Verify risk scores are bounded between 0 and 100."""
    print("[TEST 09] Risk Scoring - 0 to 100 range... ", end="")
    risk_df = compute_risk_scores(clean_df)
    scores = risk_df["risk_score"]
    assert (scores >= 0.0).all() and (scores <= 100.0).all(), "Scores out of 0-100 range"
    print(f"OK (Min={scores.min()}, Max={scores.max()})")
    return risk_df


def test_10_risk_scoring_levels(risk_df):
    """Test 10: Verify risk level classifications."""
    print("[TEST 10] Risk Scoring - level classifications... ", end="")
    valid_levels = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert set(risk_df["risk_level"]).issubset(valid_levels), "Invalid risk level found"
    
    # Test classifier function edge cases
    assert classify_risk_level(10) == "LOW"
    assert classify_risk_level(30) == "MEDIUM"
    assert classify_risk_level(60) == "HIGH"
    assert classify_risk_level(85) == "CRITICAL"
    print("OK")


def test_11_model_training(features_df):
    """Test 11: Verify IsolationForest model training."""
    print("[TEST 11] Anomaly Detection - model training... ", end="")
    model = train_anomaly_model(features_df)
    assert model is not None, "Model is None"
    print("OK")
    return model


def test_12_model_persistence(model):
    """Test 12: Verify model saving and loading via joblib."""
    print("[TEST 12] Anomaly Detection - joblib persistence... ", end="")
    test_path = os.path.join(current_dir, "test_model.joblib")
    try:
        save_model(model, filepath=test_path)
        assert os.path.exists(test_path), "Model file not created"
        loaded_model = load_model(filepath=test_path)
        assert loaded_model is not None, "Failed to load model"
        print("OK")
    finally:
        if os.path.exists(test_path):
            os.remove(test_path)


def test_13_prediction_pipeline():
    """Test 13: Verify predict.py run_prediction execution."""
    print("[TEST 13] ML Prediction Pipeline run_prediction()... ", end="")
    results_df, count = run_prediction()
    assert results_df is not None and not results_df.empty, "Results DataFrame empty"
    assert count > 0, "Zero records upserted"
    print(f"OK ({count} records processed & saved)")
    return count


def test_14_postgres_ml_table(expected_count):
    """Test 14: Verify security_event_ml table contents & event_id uniqueness."""
    print("[TEST 14] PostgreSQL security_event_ml validation... ", end="")
    engine = get_engine()
    ml_df = pd.read_sql_query("SELECT * FROM security_event_ml", engine)
    
    pg_count = len(ml_df)
    distinct_ids = ml_df["event_id"].nunique()

    assert pg_count == expected_count, f"Count mismatch! Expected {expected_count}, got {pg_count}"
    assert distinct_ids == pg_count, f"Duplicates found! Total={pg_count}, Distinct={distinct_ids}"
    assert not ml_df["event_id"].isnull().any(), "Null event_ids found"
    assert set(ml_df["risk_level"]).issubset({"LOW", "MEDIUM", "HIGH", "CRITICAL"}), "Invalid risk levels in PG"
    print(f"OK (PG count={pg_count}, distinct={distinct_ids}, duplicates=0)")


def test_15_idempotency_check(initial_count):
    """Test 15: Verify pipeline idempotency (re-running predict does not duplicate rows)."""
    print("[TEST 15] Pipeline Idempotency Check (re-running predict)... ", end="")
    
    # Re-run prediction
    run_prediction()
    
    engine = get_engine()
    ml_df = pd.read_sql_query("SELECT * FROM security_event_ml", engine)
    n2 = len(ml_df)
    distinct_ids = ml_df["event_id"].nunique()

    assert n2 == initial_count, f"Idempotency failed! Initial count={initial_count}, post re-run count={n2}"
    assert distinct_ids == n2, f"Duplicates introduced on re-run! Total={n2}, Distinct={distinct_ids}"
    print(f"OK (N1={initial_count}, N2={n2}, duplicates=0)")


# ============================================================
# Main Test Runner
# ============================================================

def main():
    print()
    print("=" * 60)
    print("  CYBERSHIELD - MACHINE LEARNING PIPELINE TEST SUITE")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    print()

    passed = 0
    failed = 0

    tests = [
        ("Test 01", test_1_dependencies),
        ("Test 02", test_2_postgres_connection),
    ]

    try:
        test_1_dependencies()
        passed += 1

        test_2_postgres_connection()
        passed += 1

        raw_df = test_3_data_loader_events()
        passed += 1

        test_4_data_loader_columns(raw_df)
        passed += 1

        clean_df = test_5_preprocessing_basic(raw_df)
        passed += 1

        test_6_preprocessing_null_handling()
        passed += 1

        features_df = test_7_feature_engineering_extraction(clean_df)
        passed += 1

        test_8_feature_engineering_numeric_types(features_df)
        passed += 1

        risk_df = test_9_risk_scoring_range(clean_df)
        passed += 1

        test_10_risk_scoring_levels(risk_df)
        passed += 1

        model = test_11_model_training(features_df)
        passed += 1

        test_12_model_persistence(model)
        passed += 1

        count = test_13_prediction_pipeline()
        passed += 1

        test_14_postgres_ml_table(count)
        passed += 1

        test_15_idempotency_check(count)
        passed += 1

    except Exception as e:
        failed += 1
        print(f"\n[FAIL] Test Error: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 60)
    total = passed + failed
    print(f"  RESULTS: {passed}/{total} tests passed")
    if failed > 0:
        print(f"  [FAIL] {failed} test(s) FAILED")
        sys.exit(1)
    else:
        print("  [SUCCESS] ALL 15 ML TESTS PASSED")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
