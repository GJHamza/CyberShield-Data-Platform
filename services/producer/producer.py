import json
import os
import sys
import time
from dotenv import load_dotenv
from kafka import KafkaProducer
from kafka.errors import KafkaError

from services.generator.generator import generate_event

load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "cyber-events")


def create_producer(bootstrap_servers=None):
    """Create and return a KafkaProducer instance."""
    servers = bootstrap_servers or KAFKA_BOOTSTRAP_SERVERS
    try:
        producer = KafkaProducer(
            bootstrap_servers=servers,
            value_serializer=lambda value: json.dumps(value, ensure_ascii=False).encode("utf-8"),
            retries=3,
            acks="all",
        )
        return producer
    except Exception as e:
        print(f"[ERROR] Failed to create KafkaProducer ({servers}): {e}")
        raise


def send_event(producer, event, topic=None):
    """
    Send a single cybersecurity event to Kafka.
    Returns record metadata or None on error.
    """
    target_topic = topic or KAFKA_TOPIC
    try:
        future = producer.send(target_topic, value=event)
        metadata = future.get(timeout=10)
        print(
            f"[SENT] "
            f"event_id={event.get('event_id', 'N/A')} | "
            f"type={event.get('event_type', 'N/A')} | "
            f"severity={event.get('severity', 'N/A')} | "
            f"partition={metadata.partition} | "
            f"offset={metadata.offset}"
        )
        return metadata
    except KafkaError as ke:
        print(f"[ERROR] Kafka error sending event {event.get('event_id')}: {ke}")
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected error sending event {event.get('event_id')}: {e}")
        return None


def main(max_events=None, interval_seconds=2):
    """
    Main loop to generate and produce events continuously or up to max_events.
    """
    print("=" * 60)
    print("  CYBERSHIELD KAFKA PRODUCER")
    print("=" * 60)
    print(f"Kafka Servers : {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"Topic         : {KAFKA_TOPIC}")
    print("=" * 60)
    print("Generating cybersecurity events...\n")

    try:
        producer = create_producer()
    except Exception:
        sys.exit(1)

    sent_count = 0

    try:
        while True:
            event = generate_event()
            metadata = send_event(producer, event)

            if metadata:
                sent_count += 1

            if max_events and sent_count >= max_events:
                print(f"\n[INFO] Reached max_events limit ({max_events}). Stopping.")
                break

            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print("\n[INFO] Producer stopped by user (Ctrl+C).")
    finally:
        try:
            print("[INFO] Flushing and closing Kafka producer...")
            producer.flush()
            producer.close(timeout=5)
            print(f"[INFO] Producer closed cleanly. Total sent: {sent_count}")
        except Exception as e:
            print(f"[WARNING] Exception closing producer: {e}")


if __name__ == "__main__":
    main()