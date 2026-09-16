"""
CyberShield Data Platform - ML Module
Data Loader: Loads security events from PostgreSQL into Pandas DataFrame.
"""

import os

from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine

load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "cyber_platform")
POSTGRES_USER = os.getenv("POSTGRES_USER", "cyber_admin")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "CyberShield2026")


def get_database_url():
    """Construct PostgreSQL SQLAlchemy connection URL."""
    return f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"


def get_engine():
    """Create and return an SQLAlchemy Engine."""
    db_url = get_database_url()
    return create_engine(db_url)


def load_security_events(limit=None, engine=None):
    """
    Load security events from PostgreSQL into a Pandas DataFrame.
    
    Args:
        limit (int, optional): Max number of records to load.
        engine (Engine, optional): Pre-created SQLAlchemy engine.
        
    Returns:
        pd.DataFrame: Loaded security events.
    """
    if engine is None:
        engine = get_engine()

    query = "SELECT * FROM security_events ORDER BY timestamp DESC"
    if limit and isinstance(limit, int) and limit > 0:
        query += f" LIMIT {limit}"

    try:
        df = pd.read_sql_query(query, engine)
    except Exception as e:
        print(f"[ERROR] Failed to load security_events from PostgreSQL ({POSTGRES_HOST}:{POSTGRES_PORT}): {e}")
        raise

    # Validation
    if df.empty:
        print("[WARNING] Loaded DataFrame from security_events is empty!")
        return df

    required_cols = {"event_id", "timestamp", "event_type", "severity"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in security_events DataFrame: {missing}")

    print(f"[DATA LOADER] Loaded {len(df)} records from PostgreSQL security_events ({POSTGRES_HOST}:{POSTGRES_PORT})")
    return df


if __name__ == "__main__":
    df = load_security_events(limit=5)
    print("\nSample Data:")
    print(df[["event_id", "event_type", "severity", "timestamp", "source_ip"]].to_string())
