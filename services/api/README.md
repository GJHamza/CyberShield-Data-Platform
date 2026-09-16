# 🚀 CyberShield API REST Backend (`services/api/`)

## 📌 Présentation
Le module **API REST Backend** de CyberShield Data Platform est construit avec **FastAPI** et **SQLAlchemy**. Il fournit des endpoints hautement performants, sécurisés et documentés pour interroger les événements de cybersécurité (`security_events`) et les prédictions du modèle Machine Learning (`security_event_ml`).

---

## 🏗️ Architecture & Flux Global

```
 Kafka
   │
   ▼
 MinIO Bronze
   │
   ▼
 Spark Processing (Bronze → Silver)
   │
   ▼
 MinIO Silver (Parquet Snappy)
   │
   ▼
 PostgreSQL (cyber_platform)
   ├── security_events (61 enregistrements)
   └── security_event_ml (61 prédictions, Risk Scores & Anomalies)
          │
          ▼
     FastAPI Backend (cyber-api :8000)
          │
          ├── /docs (Swagger UI Interactif)
          ├── /api/v1/health
          ├── /api/v1/events
          ├── /api/v1/alerts
          └── /api/v1/statistics/*
          │
          ▼
  Streamlit SOC Dashboard (Phase suivante)
```

---

## 📁 Structure des Fichiers

| Fichier | Rôle |
|---|---|
| [`requirements.txt`](file:///c:/Users/Hamza/OneDrive/Desktop/CyberShield-Data-Platform/services/api/requirements.txt) | Dépendances de l'API (`fastapi`, `uvicorn`, `pydantic`, `sqlalchemy`, `psycopg2-binary`, `httpx`). |
| [`config.py`](file:///c:/Users/Hamza/OneDrive/Desktop/CyberShield-Data-Platform/services/api/config.py) | Configuration dynamique par variables d'environnement (`os.getenv`). |
| [`database.py`](file:///c:/Users/Hamza/OneDrive/Desktop/CyberShield-Data-Platform/services/api/database.py) | Pool de connexions SQLAlchemy et gestion des sessions (`get_db`). |
| [`models.py`](file:///c:/Users/Hamza/OneDrive/Desktop/CyberShield-Data-Platform/services/api/models.py) | Mappings ORM pour `security_events` et `security_event_ml`. |
| [`schemas.py`](file:///c:/Users/Hamza/OneDrive/Desktop/CyberShield-Data-Platform/services/api/schemas.py) | Schémas Pydantic valides pour les requêtes et réponses JSON. |
| [`crud.py`](file:///c:/Users/Hamza/OneDrive/Desktop/CyberShield-Data-Platform/services/api/crud.py) | Logique métier d'accès aux données (filtrage, pagination, agrégation). |
| [`routes/health.py`](file:///c:/Users/Hamza/OneDrive/Desktop/CyberShield-Data-Platform/services/api/routes/health.py) | Endpoint de santé de l'API (`GET /api/v1/health`). |
| [`routes/events.py`](file:///c:/Users/Hamza/OneDrive/Desktop/CyberShield-Data-Platform/services/api/routes/events.py) | Endpoints d'exploration d'événements (`GET /api/v1/events`, `GET /api/v1/events/{id}`). |
| [`routes/alerts.py`](file:///c:/Users/Hamza/OneDrive/Desktop/CyberShield-Data-Platform/services/api/routes/alerts.py) | Endpoints d'alertes ML et d'anomalies (`GET /api/v1/alerts`). |
| [`routes/statistics.py`](file:///c:/Users/Hamza/OneDrive/Desktop/CyberShield-Data-Platform/services/api/routes/statistics.py) | Endpoints de métriques globales et distributions (`GET /api/v1/statistics/*`). |
| [`main.py`](file:///c:/Users/Hamza/OneDrive/Desktop/CyberShield-Data-Platform/services/api/main.py) | Application principale FastAPI avec middlewares CORS et handlers d'exceptions. |
| [`Dockerfile`](file:///c:/Users/Hamza/OneDrive/Desktop/CyberShield-Data-Platform/services/api/Dockerfile) | Conteneurisation Docker de l'API. |

---

## 🔌 Endpoints de l'API

### 1. Health & Status
- **`GET /api/v1/health`** : Vérifie l'état de l'API et la connectivité effective à PostgreSQL (`HTTP 200` si connecté, `HTTP 503` sinon).

### 2. Événements de Sécurité (`security_events`)
- **`GET /api/v1/events`** : Liste paginée des événements avec filtres (`page`, `page_size`, `severity`, `event_type`, `source_ip`, `protocol`, `event_date`).
- **`GET /api/v1/events/{event_id}`** : Détail d'un événement avec jointure complète des prédictions ML associées.

### 3. Alertes & Anomalies ML (`security_event_ml`)
- **`GET /api/v1/alerts`** : Liste paginée des alertes filtrable par `risk_level` (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), `is_anomaly` (`true`/`false`), ou `min_risk_score`.

### 4. Statistiques & Analytics
- **`GET /api/v1/statistics/overview`** : Métriques agrégées (`total_events`, `total_anomalies`, `anomaly_rate`, `critical_events`, `average_risk_score`, etc.).
- **`GET /api/v1/statistics/severity`** : Répartition par sévérité.
- **`GET /api/v1/statistics/event-types`** : Répartition par type d'événement.
- **`GET /api/v1/statistics/risk-levels`** : Répartition par niveau de risque ML.

---

## 🚀 Commandes de Lancement & Validation

### Lancement Local (PowerShell)
```bash
.\.venv\Scripts\python.exe -m uvicorn services.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Lancement Docker
```bash
docker compose up -d api
```

### Accès aux interfaces Swagger / ReDoc
- **Swagger UI** : `http://localhost:8000/docs`
- **ReDoc** : `http://localhost:8000/redoc`

### Exécution des Tests Automatisés (15/15 PASS)
```bash
.\.venv\Scripts\python.exe tests/test_api.py
```
