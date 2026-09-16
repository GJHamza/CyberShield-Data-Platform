# 📤 CyberShield Kafka Producer (`services/producer/`)

## Rôle du Service
Le Producer génère et publie en temps réel des événements de cybersécurité vers le topic Kafka `cyber-events`.

## Variables d'Environnement
| Variable | Valeur par défaut | Description |
|---|---|---|
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` (Host) / `kafka:9092` (Docker) | Adresse du broker Kafka |
| `KAFKA_TOPIC` | `cyber-events` | Topic de destination |

## Utilisation

### Exécution standard (boucle continue)
```bash
python -m services.producer.producer
```

### Exécution avec limites (pour tests)
```python
from services.producer.producer import main

main(max_events=10, interval_seconds=1.0)
```

## Gestion des Erreurs & Sécurité
- Sérialisation automatique JSON (`utf-8`).
- Retry automatique (`retries=3`) et acquittement complet (`acks='all'`).
- Fermeture propre (`flush()` & `close()`) lors de l'interruption (Ctrl+C).
