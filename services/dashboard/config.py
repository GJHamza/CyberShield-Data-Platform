"""
CyberShield Data Platform - Dashboard Configuration
Centralized configuration loaded dynamically from environment variables.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# API Connection Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "10"))

# Application Metadata
APP_NAME = "CyberShield SOC Dashboard"
APP_VERSION = "1.0.0"
