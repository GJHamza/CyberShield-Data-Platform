"""
CyberShield Data Platform
Automated API Test Suite for FastAPI Backend (services/api/)

Covers 15 automated test cases:
1. Health endpoint (GET /api/v1/health)
2. Database connectivity check
3. List events (GET /api/v1/events)
4. Events pagination (page_size=5)
5. Severity filtering (severity=critical)
6. Event_type filtering (event_type=malware_detected)
7. Event detail (GET /api/v1/events/{event_id})
8. Non-existent event handling (HTTP 404)
9. List alerts (GET /api/v1/alerts)
10. Alert risk_level filtering (risk_level=CRITICAL)
11. Alert anomaly filtering (is_anomaly=true)
12. Overview statistics (GET /api/v1/statistics/overview)
13. Severity distribution (GET /api/v1/statistics/severity)
14. Event types distribution (GET /api/v1/statistics/event-types)
15. Risk levels distribution (GET /api/v1/statistics/risk-levels)
"""

import os
import sys
from datetime import datetime, timezone

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from fastapi.testclient import TestClient
from services.api.main import app

client = TestClient(app)


def test_1_health_endpoint():
    """Test 1: GET /api/v1/health"""
    print("[TEST 01] Health endpoint (GET /api/v1/health)... ", end="")
    response = client.get("/api/v1/health")
    assert response.status_code == 200, f"Expected HTTP 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "cybershield-api"
    print("OK")


def test_2_database_connectivity():
    """Test 2: Database connectivity check in health payload."""
    print("[TEST 02] Database connectivity check... ", end="")
    response = client.get("/api/v1/health")
    data = response.json()
    assert data["database"] == "connected"
    print("OK")


def test_3_list_events():
    """Test 3: GET /api/v1/events"""
    print("[TEST 03] List events (GET /api/v1/events)... ", end="")
    response = client.get("/api/v1/events")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data and "items" in data
    assert data["total"] > 0
    print(f"OK ({data['total']} total events)")


def test_4_events_pagination():
    """Test 4: GET /api/v1/events?page=1&page_size=5"""
    print("[TEST 04] Events pagination (page_size=5)... ", end="")
    response = client.get("/api/v1/events?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["page_size"] == 5
    print("OK")


def test_5_events_severity_filter():
    """Test 5: GET /api/v1/events?severity=critical"""
    print("[TEST 05] Severity filtering (severity=critical)... ", end="")
    response = client.get("/api/v1/events?severity=critical")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["severity"].lower() == "critical"
    print(f"OK ({data['total']} critical events)")


def test_6_events_type_filter():
    """Test 6: GET /api/v1/events?event_type=malware_detected"""
    print("[TEST 06] Event_type filtering (event_type=malware_detected)... ", end="")
    response = client.get("/api/v1/events?event_type=malware_detected")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["event_type"].lower() == "malware_detected"
    print(f"OK ({data['total']} malware_detected events)")


def test_7_get_event_detail():
    """Test 7: GET /api/v1/events/{event_id}"""
    print("[TEST 07] Event detail lookup (GET /api/v1/events/{event_id})... ", end="")
    # First get a valid event_id from events list
    list_resp = client.get("/api/v1/events?page_size=1")
    event_id = list_resp.json()["items"][0]["event_id"]

    detail_resp = client.get(f"/api/v1/events/{event_id}")
    assert detail_resp.status_code == 200
    data = detail_resp.json()
    assert data["event_id"] == event_id
    assert "ml_result" in data
    print("OK")


def test_8_non_existent_event_404():
    """Test 8: GET /api/v1/events/evt-non-existent-9999 -> HTTP 404"""
    print("[TEST 08] Non-existent event 404 error handling... ", end="")
    response = client.get("/api/v1/events/evt-non-existent-9999")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    print("OK")


def test_9_list_alerts():
    """Test 9: GET /api/v1/alerts"""
    print("[TEST 09] List alerts (GET /api/v1/alerts)... ", end="")
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data and "items" in data
    assert data["total"] > 0
    print(f"OK ({data['total']} alerts)")


def test_10_alerts_risk_level_filter():
    """Test 10: GET /api/v1/alerts?risk_level=CRITICAL"""
    print("[TEST 10] Alert risk_level filtering (risk_level=CRITICAL)... ", end="")
    response = client.get("/api/v1/alerts?risk_level=CRITICAL")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["risk_level"] == "CRITICAL"
    print(f"OK ({data['total']} CRITICAL alerts)")


def test_11_alerts_anomaly_filter():
    """Test 11: GET /api/v1/alerts?is_anomaly=true"""
    print("[TEST 11] Alert anomaly filtering (is_anomaly=true)... ", end="")
    response = client.get("/api/v1/alerts?is_anomaly=true")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["is_anomaly"] is True
    print(f"OK ({data['total']} anomalies)")


def test_12_overview_statistics():
    """Test 12: GET /api/v1/statistics/overview"""
    print("[TEST 12] Overview statistics (GET /api/v1/statistics/overview)... ", end="")
    response = client.get("/api/v1/statistics/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["total_events"] > 0
    assert "anomaly_rate" in data
    assert "average_risk_score" in data
    print("OK")


def test_13_severity_statistics():
    """Test 13: GET /api/v1/statistics/severity"""
    print("[TEST 13] Severity distribution (GET /api/v1/statistics/severity)... ", end="")
    response = client.get("/api/v1/statistics/severity")
    assert response.status_code == 200
    data = response.json()
    assert data["metric"] == "severity"
    assert len(data["items"]) > 0
    print("OK")


def test_14_event_types_statistics():
    """Test 14: GET /api/v1/statistics/event-types"""
    print("[TEST 14] Event types distribution (GET /api/v1/statistics/event-types)... ", end="")
    response = client.get("/api/v1/statistics/event-types")
    assert response.status_code == 200
    data = response.json()
    assert data["metric"] == "event_type"
    assert len(data["items"]) > 0
    print("OK")


def test_15_risk_levels_statistics():
    """Test 15: GET /api/v1/statistics/risk-levels"""
    print("[TEST 15] Risk levels distribution (GET /api/v1/statistics/risk-levels)... ", end="")
    response = client.get("/api/v1/statistics/risk-levels")
    assert response.status_code == 200
    data = response.json()
    assert data["metric"] == "risk_level"
    assert len(data["items"]) > 0
    print("OK")


def main():
    print()
    print("=" * 60)
    print("  CYBERSHIELD - FASTAPI BACKEND TEST SUITE")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    print()

    passed = 0
    failed = 0

    tests = [
        test_1_health_endpoint,
        test_2_database_connectivity,
        test_3_list_events,
        test_4_events_pagination,
        test_5_events_severity_filter,
        test_6_events_type_filter,
        test_7_get_event_detail,
        test_8_non_existent_event_404,
        test_9_list_alerts,
        test_10_alerts_risk_level_filter,
        test_11_alerts_anomaly_filter,
        test_12_overview_statistics,
        test_13_severity_statistics,
        test_14_event_types_statistics,
        test_15_risk_levels_statistics,
    ]

    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"[FAIL] {e}")

    print()
    print("=" * 60)
    total = passed + failed
    print(f"  RESULTS: {passed}/{total} tests passed")
    if failed > 0:
        print(f"  [FAIL] {failed} test(s) FAILED")
        sys.exit(1)
    else:
        print("  [SUCCESS] ALL 15 API TESTS PASSED")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
