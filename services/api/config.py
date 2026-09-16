"""
CyberShield Data Platform - API Configuration
Loads environment variables safely using python-dotenv.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "cyber_platform")
POSTGRES_USER = os.getenv("POSTGRES_USER", "cyber_admin")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "CyberShield2026")

# API Configuration
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")
PROJECT_NAME = "CyberShield Security API"
PROJECT_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")


def get_database_url():
    """Construct PostgreSQL SQLAlchemy Connection String."""
    return f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
