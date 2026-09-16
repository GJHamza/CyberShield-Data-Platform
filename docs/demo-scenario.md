# CyberShield Data Platform — PFE Demo Scenario

This document provides a step-by-step, reproducible demonstration scenario for presenting **CyberShield Data Platform** during an academic thesis defense (PFE) or technical jury presentation.

---

## 1. Objective

The objective of this live demonstration is to showcase the end-to-end telemetry lifecycle of the CyberShield Data Platform:
1. Ingesting synthetic cybersecurity event logs into Apache Kafka.
2. Storing raw events in a S3 Data Lake (MinIO Bronze Layer).
3. Transforming JSON logs into columnar Parquet files via Apache Spark (MinIO Silver Layer).
4. Loading structured records idempotently into PostgreSQL.
5. Computing Machine Learning Risk Scores and detecting behavioral anomalies using an unsupervised IsolationForest model.
6. Serving enriched telemetry via a REST API (FastAPI).
7. Visualizing live threat intelligence on an interactive SOC Dashboard (Streamlit).

---

## 2. Architecture Flow

```
Generator ──> Producer ──> Kafka (cyber-events) ──> Consumer ──> MinIO Bronze (JSON)
                                                                      │
                                                                 Spark ETL
                                                                      │
                                                                      ▼
PostgreSQL (security_event_ml) <── ML Engine <── PostgreSQL <── MinIO Silver (Parquet)
              │                                  (security_events)
              └───────────────┬────────────────────────┘
                              │
                              ▼
                        FastAPI (:8000)
                              │ HTTP / REST
                              ▼
                    SOC Dashboard (:8501)
```

---

## 3. Prerequisites

Before starting the live demonstration, ensure the following tools are ready:
- **Docker Desktop** installed and running.
- **Python 3.11+** virtual environment activated (`.venv`).
- Terminal window open at the project root (`CyberShield-Data-Platform/`).
- Web browser ready with open tabs for Swagger UI (`http://localhost:8000/docs`) and Streamlit Dashboard (`http://localhost:8501`).

---

## 4. Step 1 — Start Infrastructure

Launch all 6 microservices in detached mode using Docker Compose:

```bash
docker compose up -d
```

---

## 5. Step 2 — Verify Services

Check that all microservice containers are running cleanly and healthy:

```bash
docker compose ps
```

**Expected Container Statuses**:
- `cyber-postgres`: `Up` (healthy)
- `cyber-kafka`: `Up`
- `cyber-minio`: `Up`
- `cyber-spark`: `Up`
- `cyber-api`: `Up`
- `cyber-dashboard`: `Up` (healthy)

---

## 6. Step 3 — Generate Security Events

Generate a batch of 20 synthetic cybersecurity events (e.g. port scans, brute force attacks, malware detections) and publish them to Apache Kafka:

```bash
python -c "from services.producer.producer import main; main(max_events=20, interval_seconds=0.1)"
```

**What happens**: The generator creates randomized private IP addresses, attack categories, severities, and target ports, while the producer serializes them into JSON and sends them to the `cyber-events` Kafka topic.

---

## 7. Step 4 — Kafka

Consume the 20 newly generated events from the Kafka stream:

```bash
python -c "from services.consumer.consumer import main; main(max_messages=20)"
```

**What happens**: The consumer group `cybershield-bronze-consumer` reads the events from Kafka, performs mandatory field validation (`event_id`, `event_type`, `timestamp`, `source_ip`, `severity`), and forwards valid events to MinIO.

---

## 8. Step 5 — Bronze Layer

Verify that raw JSON objects are stored in the MinIO S3 Bronze Data Lake (`cybershield-data/bronze/events/`):

```bash
python -c "from minio import Minio; client = Minio('localhost:9000', access_key='cybershield_admin', secret_key='CyberShieldMinio2026', secure=False); print('Total Bronze Objects in MinIO:', len(list(client.list_objects('cybershield-data', prefix='bronze/', recursive=True))))"
```

---

## 9. Step 6 — Bronze → Silver

Execute the Apache Spark ETL job to transform raw multiline JSON files from MinIO Bronze into structured, Snappy-compressed Parquet files in MinIO Silver:

```bash
docker exec cyber-spark /opt/spark/bin/spark-submit --conf spark.hadoop.fs.s3a.access.key=cybershield_admin --conf spark.hadoop.fs.s3a.secret.key=CyberShieldMinio2026 /opt/spark/work-dir/services/processing/bronze_to_silver.py
```

**Key Operations Performed by Spark**:
- Normalizes column names to `snake_case`.
- Parses timestamps and extracts `event_date` and `event_hour`.
- Filters corrupt records (`_corrupt_record`).
- Deduplicates on `event_id`.
- Writes Parquet files partitioned by `event_date` to `s3a://cybershield-data/silver/events/`.

---

## 10. Step 7 — Silver → PostgreSQL

Execute the Spark database loading job to ingest Silver Parquet records into PostgreSQL:

```bash
docker exec cyber-spark /opt/spark/bin/spark-submit --conf spark.hadoop.fs.s3a.access.key=cybershield_admin --conf spark.hadoop.fs.s3a.secret.key=CyberShieldMinio2026 /opt/spark/work-dir/services/processing/silver_to_postgres.py
```

Verify that the records are populated in the PostgreSQL `security_events` table:

```bash
docker exec cyber-postgres psql -U cyber_admin -d cyber_platform -c "SELECT count(*) FROM security_events;"
```

---

## 11. Step 8 — Machine Learning

Execute the Machine Learning inference and scoring pipeline:

```bash
python services/ml/predict.py
```

**ML Pipeline Operations**:
1. **Data Loading**: Loads records from PostgreSQL `security_events`.
2. **Preprocessing**: Normalizes categories and handles missing values.
3. **Feature Engineering**: Extracts 12 numerical features (`severity_encoded`, `event_type_encoded`, `protocol_encoded`, `source_port`, `destination_port`, `privileged_source_port`, `privileged_destination_port`, `port_difference`, `source_ip_frequency`, `destination_ip_frequency`, `event_hour`, `day_of_week`).
4. **Risk Scoring**: Computes deterministic 0–100 risk scores and assigns risk levels (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
5. **Anomaly Detection**: Loads the pre-trained `IsolationForest` model (`isolation_forest.joblib`) to calculate `anomaly_score` and `is_anomaly`.
6. **Idempotent Upsert**: Saves results into `security_event_ml` using SQL `ON CONFLICT (event_id) DO UPDATE SET...`.

Verify ML records in PostgreSQL:

```bash
docker exec cyber-postgres psql -U cyber_admin -d cyber_platform -c "SELECT count(*) FROM security_event_ml;"
```

---

## 12. Step 9 — FastAPI

Open the browser or issue HTTP requests to demonstrate the REST API endpoints:

- **API Welcome Root**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Key Endpoints to Highlight to the Jury:
- `GET /api/v1/health` : Demonstrates active PostgreSQL database connectivity.
- `GET /api/v1/events` : Shows paginated security events with multi-column filtering.
- `GET /api/v1/alerts` : Displays ML alerts joining raw events with ML scores.
- `GET /api/v1/statistics/overview` : Returns aggregated SOC metrics (`total_events`, `total_anomalies`, `anomaly_rate`, `critical_events`).

---

## 13. Step 10 — SOC Dashboard

Open the Streamlit SOC Dashboard in your browser: [http://localhost:8501](http://localhost:8501)

### Key Elements to Present to the Jury:
1. **Header & Health Badges**: Highlight the live status badges (`MONITORING: ACTIVE`, `API: HEALTHY`, `DATABASE: CONNECTED`).
2. **KPI Metrics Bar**: Show Total Events, Critical Events, Total Anomalies, Anomaly Rate %, and Avg Risk Score.
3. **Visual Analytics Charts**:
   - Donut chart of **Events by Severity**.
   - Donut chart of **ML Risk Level Distribution**.
   - Horizontal bar chart of **Event Types & Attack Vectors**.
   - Donut chart of **Anomaly Detection Breakdown**.
   - Timeline chart of **Security Event Velocity**.
   - Bar chart of **Top Source IPs**.
4. **Alert Center**: Show filtered alerts, anomaly tags, and risk level badges.
5. **Security Events Table**: Demonstrate live column filtering, pagination, and the **Event Details Inspector** modal.
6. **Auto-Refresh**: Toggle auto-refresh between 10s, 30s, 60s, and OFF to show live UI updating.

---

## 14. Step 11 — End-to-End Verification

Run this quick command snippet to demonstrate total data consistency across all layers:

```bash
python -c "
import urllib.request, json
res = urllib.request.urlopen('http://localhost:8000/api/v1/statistics/overview')
data = json.loads(res.read())
print('=== CYBERSHIELD LIVE SYSTEM SUMMARY ===')
print(f'Total Events in Warehouse : {data[\"total_events\"]}')
print(f'Total Anomalies (ML)     : {data[\"total_anomalies\"]}')
print(f'Anomaly Rate             : {data[\"anomaly_rate\"]}%')
print(f'Critical Risk Events     : {data[\"critical_events\"]}')
print('=======================================')
"
```

---

## 15. Expected Results

The table below reflects the validated metrics captured during our live system validation run:

| Architectural Layer | Validated Benchmark Count |
|---|:---:|
| **Kafka Events Stream** | 121 events |
| **MinIO Bronze Layer (JSON Objects)** | 121 files |
| **MinIO Silver Layer (Parquet Rows)** | 101 rows |
| **PostgreSQL `security_events`** | 101 records |
| **PostgreSQL `security_event_ml`** | 101 records |
| **Duplicate Records** | **0** |
| **ML Anomalies Detected** | **13** (`12.87%` rate) |
| **Critical Risk Events** | **49** |
| **FastAPI Health Status** | `HTTP 200 OK` (Healthy & Connected) |
| **SOC Dashboard Status** | `HTTP 200 OK` (Operational) |

*Note: In a new demonstration environment, counts will reflect the specific number of generated test events.*

---

## 16. Demo Tips for Jury Presentation

### Recommended Order of Presentation
1. **Introduction & Architecture Diagram**: Open with `docs/images/global-architecture.png` to explain the 7-layer architecture.
2. **Live Data Injection**: Run the Producer & Consumer commands to generate and stream 20 events.
3. **ETL Execution**: Run Spark Bronze-to-Silver and Silver-to-PostgreSQL scripts to demonstrate data transformation.
4. **Machine Learning Execution**: Run `predict.py` to demonstrate Risk Scoring and IsolationForest anomaly inference.
5. **API & Dashboard Demonstration**: Show Swagger UI (`:8000/docs`) and navigate through the Streamlit SOC Dashboard (`:8501`).

### Pre-Presentation Checklist
- [ ] Run `docker compose up -d` 5 minutes before the presentation to let Postgres initialize cleanly.
- [ ] Verify that `docker compose ps` shows all 6 containers as `Up` / `healthy`.
- [ ] Ensure `.venv` is activated.
- [ ] Test HTTP access to `http://localhost:8000/api/v1/health` and `http://localhost:8501`.

### What to Avoid
- Do NOT perform live docker container deletion during the presentation.
- Do NOT modify credentials or `.env` during the presentation.
- Do NOT use non-synthetic or real network attack tools (the demonstration relies strictly on the built-in synthetic generator).

---

## 17. Troubleshooting

### Problem 1: Spark S3A `403 Forbidden` error when accessing MinIO
- **Cause**: Spark's configuration parser in `spark-defaults.conf` does not interpolate `${VAR_NAME}` environment variables natively.
- **Verification**: Run `docker logs cyber-spark` and check for `AmazonS3Exception: 403 Forbidden`.
- **Solution**: Pass explicit S3A credentials on `spark-submit`:
  ```bash
  --conf spark.hadoop.fs.s3a.access.key=cybershield_admin --conf spark.hadoop.fs.s3a.secret.key=CyberShieldMinio2026
  ```

### Problem 2: FastAPI returns `HTTP 503 Service Unavailable` on startup
- **Cause**: PostgreSQL container (`cyber-postgres`) is still completing its initialization scripts.
- **Verification**: Run `docker compose ps` to check if `cyber-postgres` is marked as `(healthy)`.
- **Solution**: Wait 5–10 seconds for PostgreSQL initialization to finish before requesting API endpoints.

### Problem 3: Streamlit Dashboard displays `API Connection Error`
- **Cause**: The `cyber-api` container is stopped or unreachable at `http://localhost:8000`.
- **Verification**: Run `curl http://localhost:8000/api/v1/health`.
- **Solution**: Restart the API container with `docker compose restart api`.
