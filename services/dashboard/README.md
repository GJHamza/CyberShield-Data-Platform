# 🛡️ CyberShield SOC Dashboard (`services/dashboard/`)

## 📌 Overview
The **CyberShield SOC Dashboard** is a real-time defensive Security Operations Center web interface built with **Streamlit** and **Plotly**. It visualizes cybersecurity events, Machine Learning risk scores, and anomaly detections exposed by the **CyberShield REST API** (`cyber-api`).

---

## 🏗️ Architecture

```
 Generator ──► Producer ──► Kafka ──► Consumer ──► MinIO Bronze
                                                      │
                                                      ▼
                                            Spark Processing (Silver)
                                                      │
                                                      ▼
                                              MinIO Silver (Parquet)
                                                      │
                                                      ▼
                                          PostgreSQL (security_events)
                                                      │
                                                      ▼
                                         Machine Learning Engine
                                         (Risk Scoring + IsolationForest)
                                                      │
                                                      ▼
                                          PostgreSQL (security_event_ml)
                                                      │
                                                      ▼
                                           FastAPI Backend (cyber-api)
                                           http://cyber-api:8000
                                                      │ HTTP/REST
                                                      ▼
                                           Streamlit SOC Dashboard
                                           http://localhost:8501
```

---

## 🚀 Key Features

1. **Header & Status Indicators**: Real-time badges for `API Status`, `Database Status`, `Monitoring Status` (`ACTIVE` / `PAUSED`), `Version`, and `Last Updated UTC`.
2. **SOC KPI Cards**: Real-time aggregated metrics (`Total Events`, `Critical Events`, `Anomalies Detected`, `Anomaly Rate %`, `Average Risk Score`).
3. **Threat Intelligence & Visual Analytics**:
   - **Severity Distribution**: Donut chart of events by severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
   - **Risk Level Distribution**: Donut chart of ML risk level classifications.
   - **Event Types & Attack Vectors**: Horizontal bar chart of attack categories.
   - **Anomaly Breakdown**: Donut chart comparing Normal Events vs ML Anomalies.
   - **Event Velocity Timeline**: Area line chart of event frequency over time.
   - **Top Source IPs**: Horizontal bar chart of Top 5 active Source IP addresses.
   - **Recent Security Activity**: Compact table of recent telemetry.
4. **Alert Center (🚨)**: Prioritized alert table with Risk Level, Risk Score, Anomaly indicators, and advanced filters (`Risk Level`, `Anomaly Status`, `Min/Max Risk Score`).
5. **Security Events Table (📋)**: Complete event exploration table with dynamic filters (`Severity`, `Event Type`, `Protocol`, `Source IP`, `Event Date`) and pagination.
6. **Deep Event Inspector (🔍)**: Two-column detail card displaying raw event metadata and Machine Learning predictions for any selected `event_id`.
7. **SOC Monitoring & Auto-Refresh**: Configurable non-blocking auto-refresh (`OFF`, `10s`, `30s`, `60s`).

---

## 🔧 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `API_URL` | `http://localhost:8000` | Target FastAPI backend URL (`http://cyber-api:8000` inside Docker). |
| `HTTP_TIMEOUT` | `10` | Timeout in seconds for HTTP requests to FastAPI. |

---

## ⚙️ Running Locally

```bash
# 1. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Run Streamlit Dashboard
streamlit run services/dashboard/app.py --server.port 8501
```
Access in browser: **`http://localhost:8501`**

---

## 🐳 Docker Deployment

```bash
# Build and start container with Docker Compose
docker compose up -d dashboard

# View container logs
docker logs -f cyber-dashboard
```

---

## 🧪 Testing

```bash
# Execute validation test suite
python tests/test_api.py
```
