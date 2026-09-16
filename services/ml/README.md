# 🤖 CyberShield Machine Learning Module (`services/ml/`)

## 📌 Présentation & Objectifs
Le module **Machine Learning** de CyberShield Data Platform assure l'analyse comportementale avancée, le calcul de **Risk Scoring** explicable (0-100) et la détection d'anomalies non supervisée via **IsolationForest** sur les événements de cybersécurité stockés dans PostgreSQL.

---

## 🏗️ Architecture & Flux de Données

```
 PostgreSQL (security_events)
            │
            ▼
   Data Loader (data_loader.py)
            │
            ▼
   Preprocessing (preprocessing.py)
            │
            ▼
   Feature Engineering (feature_engineering.py)
            │
            ├──► Risk Scoring (risk_scoring.py)
            │       │
            │       ▼
            │   Risk Score (0-100) & Risk Level (LOW, MEDIUM, HIGH, CRITICAL)
            │
            └──► IsolationForest Model (anomaly_detection.py)
                    │
                    ▼
                Anomaly Detection (anomaly_score & is_anomaly)
                    │
                    ▼
          PostgreSQL (security_event_ml)
```

---

## 📁 Structure des Fichiers

| Fichier | Rôle |
|---|---|
| [`requirements.txt`](file:///c:/Users/Hamza/OneDrive/Desktop/CyberShield-Data-Platform/services/ml/requirements.txt) | Dépendances ML (`pandas`, `scikit-learn`, `joblib`, `sqlalchemy`, `psycopg2-binary`). |
| [`data_loader.py`](file:///c:/Users/Hamza/OneDrive/Desktop/CyberShield-Data-Platform/services/ml/data_loader.py) | Connexion PostgreSQL & chargement des événements dans un Pandas DataFrame. |
| [`preprocessing.py`](file:///c:/Users/Hamza/OneDrive/Desktop/CyberShield-Data-Platform/services/ml/preprocessing.py) | Nettoyage, normalisation des chaînes, typage et imputation des valeurs nulles. |
| [`feature_engineering.py`](file:///c:/Users/Hamza/OneDrive/Desktop/CyberShield-Data-Platform/services/ml/feature_engineering.py) | Extraction de 12 features numériques (fréquences IP, ports privilégiés, temporelles, encodages). |
| [`risk_scoring.py`](file:///c:/Users/Hamza/OneDrive/Desktop/CyberShield-Data-Platform/services/ml/risk_scoring.py) | Algorithme déterministe de scoring (0-100) et classification (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`). |
| [`anomaly_detection.py`](file:///c:/Users/Hamza/OneDrive/Desktop/CyberShield-Data-Platform/services/ml/anomaly_detection.py) | Détection d'anomalies non supervisée avec `IsolationForest` & persistance `joblib`. |
| [`train.py`](file:///c:/Users/Hamza/OneDrive/Desktop/CyberShield-Data-Platform/services/ml/train.py) | Script d'entraînement complet et de sauvegarde du modèle dans `models/isolation_forest.joblib`. |
| [`predict.py`](file:///c:/Users/Hamza/OneDrive/Desktop/CyberShield-Data-Platform/services/ml/predict.py) | Pipeline d'inférence globale et écriture idempotente dans PostgreSQL (`security_event_ml`). |
| [`models/`](file:///c:/Users/Hamza/OneDrive/Desktop/CyberShield-Data-Platform/services/ml/models/) | Dossier de persistance du modèle sérialisé (`isolation_forest.joblib`). |

---

## 🎯 Scoring & Détection d'Anomalies

### 1. Risk Scoring (0 à 100)
Combinaison déterministe de la sévérité (`low`: 15, `medium`: 35, `high`: 65, `critical`: 90), du type d'événement (ex: `malware_detected` +15), et des ports sensibles (SSH 22, SMB 445, RDP 3389, etc. +10).

- **0–24** : `LOW`
- **25–49** : `MEDIUM`
- **50–74** : `HIGH`
- **75–100** : `CRITICAL`

### 2. Anomaly Detection (IsolationForest)
Le modèle statistique `scikit-learn.ensemble.IsolationForest` évalue les déviations statistiques sur la matrice de features 12D et produit :
- `anomaly_score` : score continu (plus la valeur est élevée, plus l'événement est déviant).
- `is_anomaly` : booléen (`True` si l'événement est statistiquement anormal).

---

## 🗄️ Table PostgreSQL (`security_event_ml`)

```sql
CREATE TABLE IF NOT EXISTS security_event_ml (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(50) UNIQUE NOT NULL REFERENCES security_events(event_id) ON DELETE CASCADE,
    risk_score DOUBLE PRECISION NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    anomaly_score DOUBLE PRECISION NOT NULL,
    is_anomaly BOOLEAN NOT NULL,
    model_version VARCHAR(50) DEFAULT 'v1.0.0',
    processed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

---

## ⚡ Idempotence & Performance
- L'inférence utilise SQL `ON CONFLICT (event_id) DO UPDATE` : ré-exécuter `predict.py` met à jour les scores existants et ne crée **jamais de doublons** (`duplicates = 0`).

---

## 🚀 Commandes d'Exécution

```bash
# 1. Entraînement du modèle ML
python services/ml/train.py

# 2. Exécution de la prédiction & Sauvegarde PostgreSQL
python services/ml/predict.py

# 3. Exécution des tests automatisés (15 tests)
python tests/test_ml_pipeline.py
```
