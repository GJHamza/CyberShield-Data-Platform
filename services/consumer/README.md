# 📥 CyberShield Kafka Consumer (`services/consumer/`)

## Rôle du Service
Le Consumer lit les événements publiés sur le topic Kafka `cyber-events`, valide leur conformité et les sauvegarde dans le Data Lake MinIO (couche Bronze).

## Validation des Données
Chaque événement doit obligatoirement contenir les 5 champs suivants :
1. `event_id` (non-null, chaîne non-vide)
2. `event_type` (non-null, chaîne non-vide)
3. `timestamp` (non-null, ISO format)
4. `source_ip` (non-null, chaîne non-vide)
5. `severity` (non-null, chaîne non-vide)

**Gestion des erreurs** : Les messages corrompus ou invalides sont enregistrés dans les logs (REJECTED) et ignorés. Le Consumer **ne s'arrête jamais** sur un événement invalide.

## Organisation MinIO Bronze
Les événements valides sont écrits au format JSON multi-lignes dans :
`s3a://cybershield-data/bronze/events/YYYY/MM/DD/evt-xxxxx.json`

## Variables d'Environnement
| Variable | Valeur par défaut | Description |
|---|---|---|
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Broker Kafka |
| `KAFKA_TOPIC` | `cyber-events` | Topic consommé |
| `MINIO_ENDPOINT` | `localhost:9000` | Endpoint MinIO |
| `MINIO_ROOT_USER` | `cybershield_admin` | Access key MinIO |
| `MINIO_ROOT_PASSWORD` | `CyberShieldMinio2026` | Secret key MinIO |
| `MINIO_BUCKET` | `cybershield-data` | Bucket de destination |

## Utilisation
```bash
python -m services.consumer.consumer
```
