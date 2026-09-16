"""
CyberShield Data Platform - ML Module
Preprocessing: Cleans, imputes, and formats security events data for ML pipelines.
"""

import pandas as pd
import numpy as np


def preprocess_data(df):
    """
    Clean and preprocess raw security events DataFrame.
    
    Args:
        df (pd.DataFrame): Raw security events DataFrame.
        
    Returns:
        pd.DataFrame: Preprocessed DataFrame.
    """
    if df is None or df.empty:
        return df

    df_clean = df.copy()

    # --- 1. Clean String & Categorical Columns ---
    string_cols = ["event_id", "event_type", "severity", "protocol", "source_ip", "destination_ip"]
    for col in string_cols:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna("unknown").astype(str).str.strip()

    # Normalize values
    if "severity" in df_clean.columns:
        df_clean["severity"] = df_clean["severity"].str.lower()
    if "event_type" in df_clean.columns:
        df_clean["event_type"] = df_clean["event_type"].str.lower()
    if "protocol" in df_clean.columns:
        df_clean["protocol"] = df_clean["protocol"].str.upper()

    # --- 2. Datetime Handling ---
    if "timestamp" in df_clean.columns:
        df_clean["timestamp"] = pd.to_datetime(df_clean["timestamp"], errors="coerce", utc=True)
        # Fill any unparsable timestamp with current UTC time
        now = pd.Timestamp.now(tz="UTC")
        df_clean["timestamp"] = df_clean["timestamp"].fillna(now)

    # --- 3. Numeric Columns & Ports ---
    port_cols = ["source_port", "destination_port"]
    for col in port_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce").fillna(0).astype(int)

    if "event_hour" in df_clean.columns:
        df_clean["event_hour"] = pd.to_numeric(df_clean["event_hour"], errors="coerce")
        # If event_hour is null, derive from timestamp
        if "timestamp" in df_clean.columns:
            df_clean["event_hour"] = df_clean["event_hour"].fillna(df_clean["timestamp"].dt.hour)
        df_clean["event_hour"] = df_clean["event_hour"].fillna(0).astype(int)

    return df_clean


if __name__ == "__main__":
    import os, sys
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)

    from services.ml.data_loader import load_security_events
    raw_df = load_security_events(limit=5)
    clean_df = preprocess_data(raw_df)
    print("\nPreprocessed Data Info:")
    print(clean_df.info())
