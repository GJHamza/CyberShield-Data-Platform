"""
CyberShield Data Platform - ML Module
Risk Scoring: Computes an interpretable 0-100 risk score and categorizes risk levels.
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "../.."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import pandas as pd
import numpy as np

# Base severity weights (0-100 scale)
SEVERITY_WEIGHTS = {
    "low": 15.0,
    "medium": 35.0,
    "high": 65.0,
    "critical": 90.0,
    "unknown": 20.0,
}

# Event type vulnerability modifier (+ points)
EVENT_TYPE_MODIFIERS = {
    "malware_detected": 15.0,
    "data_exfiltration": 20.0,
    "unauthorized_access": 15.0,
    "brute_force": 10.0,
    "http_attack": 10.0,
    "failed_login": 5.0,
    "suspicious_connection": 5.0,
    "dns_anomaly": 5.0,
    "port_scan": 5.0,
    "unknown": 0.0,
}

# Sensitive/High-risk destination ports
SENSITIVE_PORTS = {22, 23, 445, 3389, 389, 1433, 3306, 5432}


def classify_risk_level(score):
    """
    Classify a risk score (0-100) into risk levels:
    - 0 to 24  : LOW
    - 25 to 49 : MEDIUM
    - 50 to 74 : HIGH
    - 75 to 100: CRITICAL
    """
    if score < 25.0:
        return "LOW"
    elif score < 50.0:
        return "MEDIUM"
    elif score < 75.0:
        return "HIGH"
    else:
        return "CRITICAL"


def compute_risk_scores(df):
    """
    Compute deterministic risk scores (0-100) and risk levels for a security events DataFrame.
    
    Args:
        df (pd.DataFrame): Preprocessed security events DataFrame.
        
    Returns:
        pd.DataFrame: DataFrame containing risk_score (float) and risk_level (str).
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=["risk_score", "risk_level"])

    scores = []

    for _, row in df.iterrows():
        sev = str(row.get("severity", "unknown")).lower()
        evt_type = str(row.get("event_type", "unknown")).lower()
        dst_port = int(row.get("destination_port", 0) or 0)

        # 1. Base Score from Severity
        score = SEVERITY_WEIGHTS.get(sev, 20.0)

        # 2. Add Event Type Modifier
        score += EVENT_TYPE_MODIFIERS.get(evt_type, 0.0)

        # 3. Add Sensitive Destination Port Bonus (+10)
        if dst_port in SENSITIVE_PORTS:
            score += 10.0

        # 4. Clamp between 0.0 and 100.0
        clamped_score = float(np.clip(score, 0.0, 100.0))
        scores.append(clamped_score)

    result_df = pd.DataFrame(index=df.index)
    result_df["risk_score"] = scores
    result_df["risk_level"] = [classify_risk_level(s) for s in scores]

    return result_df


if __name__ == "__main__":
    from services.ml.data_loader import load_security_events
    from services.ml.preprocessing import preprocess_data

    raw_df = load_security_events(limit=5)
    clean_df = preprocess_data(raw_df)
    risk_df = compute_risk_scores(clean_df)

    combined = pd.concat([clean_df[["event_id", "event_type", "severity", "destination_port"]], risk_df], axis=1)
    print("\nRisk Scoring Results:")
    print(combined.to_string())
