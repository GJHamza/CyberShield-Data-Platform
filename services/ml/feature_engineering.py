"""
CyberShield Data Platform - ML Module
Feature Engineering: Extracts security-relevant numerical features for ML models.
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "../.."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import pandas as pd
import numpy as np

SEVERITY_MAP = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
    "unknown": 0,
}

PROTOCOL_MAP = {
    "TCP": 1,
    "UDP": 2,
    "HTTP": 3,
    "HTTPS": 4,
    "DNS": 5,
    "UNKNOWN": 0,
}

EVENT_TYPE_MAP = {
    "port_scan": 1,
    "brute_force": 2,
    "failed_login": 3,
    "malware_detected": 4,
    "dns_anomaly": 5,
    "suspicious_connection": 6,
    "http_attack": 7,
    "unauthorized_access": 8,
    "data_exfiltration": 9,
    "suspicious_login": 10,
    "unknown": 0,
}

FEATURE_COLUMNS = [
    "severity_encoded",
    "event_type_encoded",
    "protocol_encoded",
    "source_port",
    "destination_port",
    "privileged_source_port",
    "privileged_destination_port",
    "port_difference",
    "source_ip_frequency",
    "destination_ip_frequency",
    "event_hour",
    "day_of_week",
]


def extract_features(df):
    """
    Extract security-focused numerical features from preprocessed DataFrame.
    
    Args:
        df (pd.DataFrame): Preprocessed security events DataFrame.
        
    Returns:
        tuple: (features_df, feature_names)
            - features_df: DataFrame containing only numerical features ready for ML.
            - feature_names: List of feature column names.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=FEATURE_COLUMNS), FEATURE_COLUMNS

    features = pd.DataFrame(index=df.index)

    # 1. Severity Encoding
    features["severity_encoded"] = (
        df["severity"].str.lower().map(SEVERITY_MAP).fillna(0).astype(int)
    )

    # 2. Event Type Encoding
    features["event_type_encoded"] = (
        df["event_type"].str.lower().map(EVENT_TYPE_MAP).fillna(0).astype(int)
    )

    # 3. Protocol Encoding
    features["protocol_encoded"] = (
        df["protocol"].str.upper().map(PROTOCOL_MAP).fillna(0).astype(int)
    )

    # 4. Ports
    features["source_port"] = df["source_port"].fillna(0).astype(int)
    features["destination_port"] = df["destination_port"].fillna(0).astype(int)

    # 5. Privileged Ports (< 1024)
    features["privileged_source_port"] = (features["source_port"] < 1024).astype(int)
    features["privileged_destination_port"] = (features["destination_port"] < 1024).astype(int)

    # 6. Port Difference
    features["port_difference"] = (features["destination_port"] - features["source_port"]).abs()

    # 7. IP Frequencies (Count occurrences of source & destination IPs)
    if "source_ip" in df.columns:
        src_counts = df["source_ip"].value_counts()
        features["source_ip_frequency"] = df["source_ip"].map(src_counts).fillna(1).astype(int)
    else:
        features["source_ip_frequency"] = 1

    if "destination_ip" in df.columns:
        dst_counts = df["destination_ip"].value_counts()
        features["destination_ip_frequency"] = df["destination_ip"].map(dst_counts).fillna(1).astype(int)
    else:
        features["destination_ip_frequency"] = 1

    # 8. Time Features
    if "timestamp" in df.columns and pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        features["event_hour"] = df["timestamp"].dt.hour.fillna(0).astype(int)
        features["day_of_week"] = df["timestamp"].dt.dayofweek.fillna(0).astype(int)
    elif "event_hour" in df.columns:
        features["event_hour"] = df["event_hour"].fillna(0).astype(int)
        features["day_of_week"] = 0
    else:
        features["event_hour"] = 0
        features["day_of_week"] = 0

    # Ensure column order matches FEATURE_COLUMNS
    features = features[FEATURE_COLUMNS]

    return features, FEATURE_COLUMNS


if __name__ == "__main__":
    from services.ml.data_loader import load_security_events
    from services.ml.preprocessing import preprocess_data

    raw_df = load_security_events(limit=5)
    clean_df = preprocess_data(raw_df)
    features_df, feature_cols = extract_features(clean_df)

    print("\nExtracted Features:")
    print(features_df.to_string())
