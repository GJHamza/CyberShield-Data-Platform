import random
from datetime import datetime, timezone
from ipaddress import IPv4Address


EVENT_TYPES = [
    "port_scan",
    "brute_force",
    "failed_login",
    "malware_detected",
    "dns_anomaly",
    "suspicious_connection",
    "http_attack",
]

SEVERITIES = [
    "low",
    "medium",
    "high",
    "critical",
]

PROTOCOLS = [
    "TCP",
    "UDP",
    "HTTP",
    "HTTPS",
    "DNS",
]


def generate_ip():
    """Generate a random private IPv4 address."""
    return str(
        IPv4Address(
            random.randint(
                int(IPv4Address("10.0.0.1")),
                int(IPv4Address("10.255.255.254")),
            )
        )
    )


def generate_event():
    """Generate a random cybersecurity event."""

    event = {
        "event_id": f"evt-{random.randint(100000, 999999)}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": random.choice(EVENT_TYPES),
        "severity": random.choice(SEVERITIES),
        "source_ip": generate_ip(),
        "destination_ip": generate_ip(),
        "protocol": random.choice(PROTOCOLS),
        "source_port": random.randint(1024, 65535),
        "destination_port": random.choice([
            22,
            53,
            80,
            443,
            445,
            3389,
        ]),
    }

    return event


if __name__ == "__main__":
    for _ in range(5):
        print(generate_event())