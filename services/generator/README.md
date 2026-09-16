# 🎲 CyberShield Event Generator (`services/generator/`)

## Rôle du Service
Le générateur d'événements produit des logs synthétiques d'événements de cybersécurité au format JSON. Il simule le trafic réseau et les incidents de sécurité SOC (Security Operations Center).

## Types d'Événements & Sévérités
- **Event Types** : `dns_anomaly`, `malware_detected`, `port_scan`, `brute_force`, `failed_login`, `http_attack`, `suspicious_connection`
- **Severities** : `low`, `medium`, `high`, `critical`
- **Protocols** : `TCP`, `UDP`, `HTTP`, `HTTPS`, `DNS`

## Structure d'un Événement
```json
{
    "event_id": "evt-774800-001",
    "timestamp": "2026-08-31T21:27:04.115143+00:00",
    "event_type": "malware_detected",
    "severity": "critical",
    "source_ip": "10.133.36.68",
    "destination_ip": "10.69.135.198",
    "protocol": "TCP",
    "source_port": 42337,
    "destination_port": 80
}
```

## Utilisation
```python
from services.generator.generator import generate_event

event = generate_event()
print(event)
```
