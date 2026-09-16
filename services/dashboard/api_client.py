"""
CyberShield Data Platform - API Client
Robust HTTP client for interacting with the CyberShield FastAPI REST backend.
"""

from typing import Any, Dict, Optional, Tuple
import requests

from services.dashboard.config import API_URL, HTTP_TIMEOUT


class CyberShieldAPIClient:
    """HTTP Client for communicating with the FastAPI REST API."""

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[int] = None):
        self.base_url = (base_url or API_URL).rstrip("/")
        self.timeout = timeout or HTTP_TIMEOUT
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "CyberShield-Dashboard/1.0",
        })

    def _request_get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Centralized HTTP GET request handler with error handling.

        Returns:
            Tuple[Optional[dict], Optional[str]]: (data, error_message)
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Clean query parameters: remove None or empty strings
        clean_params = {}
        if params:
            for key, val in params.items():
                if val is not None and val != "":
                    clean_params[key] = val

        try:
            response = self.session.get(url, params=clean_params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data, None
        except requests.exceptions.ConnectionError:
            return None, "Unable to connect to CyberShield API service."
        except requests.exceptions.Timeout:
            return None, "CyberShield API request timed out."
        except requests.exceptions.HTTPError as http_err:
            status_code = response.status_code if response is not None else "Unknown"
            if status_code == 404:
                return None, "Requested resource not found."
            elif status_code == 503:
                return None, "CyberShield API service or database is unavailable."
            return None, f"HTTP error {status_code} occurred while fetching data."
        except requests.exceptions.RequestException:
            return None, "An unexpected HTTP error occurred while communicating with the API."
        except ValueError:
            return None, "Received invalid JSON payload from CyberShield API."

    def health(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """GET /api/v1/health - Check API health and DB status."""
        return self._request_get("/api/v1/health")

    def get_events(
        self,
        page: int = 1,
        page_size: int = 20,
        severity: Optional[str] = None,
        event_type: Optional[str] = None,
        source_ip: Optional[str] = None,
        protocol: Optional[str] = None,
        event_date: Optional[str] = None,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """GET /api/v1/events - Retrieve paginated security events with filters."""
        params = {
            "page": page,
            "page_size": page_size,
            "severity": severity,
            "event_type": event_type,
            "source_ip": source_ip,
            "protocol": protocol,
            "event_date": event_date,
        }
        return self._request_get("/api/v1/events", params=params)

    def get_event(self, event_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """GET /api/v1/events/{event_id} - Retrieve single security event detail with ML results."""
        return self._request_get(f"/api/v1/events/{event_id}")

    def get_alerts(
        self,
        page: int = 1,
        page_size: int = 20,
        risk_level: Optional[str] = None,
        is_anomaly: Optional[bool] = None,
        min_risk_score: Optional[float] = None,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """GET /api/v1/alerts - Retrieve paginated ML alerts and anomalies."""
        params = {
            "page": page,
            "page_size": page_size,
            "risk_level": risk_level,
            "is_anomaly": is_anomaly,
            "min_risk_score": min_risk_score,
        }
        return self._request_get("/api/v1/alerts", params=params)

    def get_overview(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """GET /api/v1/statistics/overview - Retrieve aggregated SOC statistics."""
        return self._request_get("/api/v1/statistics/overview")

    def get_severity_statistics(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """GET /api/v1/statistics/severity - Retrieve severity distribution."""
        return self._request_get("/api/v1/statistics/severity")

    def get_event_type_statistics(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """GET /api/v1/statistics/event-types - Retrieve event type distribution."""
        return self._request_get("/api/v1/statistics/event-types")

    def get_risk_level_statistics(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """GET /api/v1/statistics/risk-levels - Retrieve ML risk level distribution."""
        return self._request_get("/api/v1/statistics/risk-levels")
