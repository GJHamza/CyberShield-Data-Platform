import json
import os
import sys
from dotenv import load_dotenv
from kafka import KafkaConsumer
from kafka.errors import KafkaError

from services.storage.minio_client import (
    create_minio_client,
    ensure_bucket,
    save_event,
)

load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "cyber-events")

MANDATORY_FIELDS = ["event_id", "event_type", "timestamp", "source_ip", "severity"]


def safe_deserialize(value_bytes):
    """Safely deserialize raw bytes into a Python object/dict."""
    if value_bytes is None:
        return None
    try:
        return json.loads(value_bytes.decode("utf-8"))
    except Exception as e:
        return {
            "_corrupt_payload": True,
            "error": str(e),
            "raw": str(value_bytes),
        }


def validate_event(event):
    """
    Validate that an event contains all mandatory fields and values are non-empty.
    Returns (is_valid, reason).
    """
    if not isinstance(event, dict):
        return False, "Payload is not a valid JSON object/dict"

    if event.get("_corrupt_payload"):
        return False, f"JSON Deserialization error: {event.get('error')}"

    for field in MANDATORY_FIELDS:
        if field not in event:
            return False, f"Missing mandatory field: '{field}'"
        val = event[field]
        if val is None:
            return False, f"Null value for mandatory field: '{field}'"
        if isinstance(val, str) and not val.strip():
            return False, f"Empty string value for mandatory field: '{field}'"

    return True, None


def create_consumer(bootstrap_servers=None, group_id="cybershield-bronze-consumer"):
    """Create and return a KafkaConsumer instance."""
    servers = bootstrap_servers or KAFKA_BOOTSTRAP_SERVERS
    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=servers,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            group_id=group_id,
            value_deserializer=safe_deserialize,
        )
        return consumer
    except Exception as e:
        print(f"[ERROR] Failed to create KafkaConsumer ({servers}): {e}")
        raise


def main(max_messages=None, timeout_ms=None):
    """
    Main loop to consume, validate, and store events in MinIO Bronze.
    """
    print("=" * 60)
    print("  CYBERSHIELD KAFKA CONSUMER")
    print("=" * 60)
    print(f"Kafka Servers : {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"Topic         : {KAFKA_TOPIC}")
    print(f"Data Lake     : MinIO (Bronze Layer)")
    print("=" * 60)

    # 1. MinIO Init
    try:
        minio_client = create_minio_client()
        ensure_bucket(minio_client)
    except Exception as e:
        print(f"[FATAL] Could not initialize MinIO client: {e}")
        sys.exit(1)

    # 2. Kafka Init
    try:
        consumer = create_consumer()
    except Exception:
        sys.exit(1)

    print("\nWaiting for cybersecurity events...\n")

    processed_count = 0
    saved_count = 0
    rejected_count = 0

    try:
        for message in consumer:
            processed_count += 1
            event = message.value

            # Validate message
            is_valid, reason = validate_event(event)

            if not is_valid:
                print(
                    f"[REJECTED] "
                    f"Topic={message.topic} | "
                    f"Partition={message.partition} | "
                    f"Offset={message.offset} | "
                    f"Reason={reason}"
                )
                rejected_count += 1
                if max_messages and processed_count >= max_messages:
                    break
                continue

            # Save valid event to MinIO Bronze
            try:
                object_name = save_event(minio_client, event)
                saved_count += 1
                print(
                    f"[SAVED] "
                    f"event_id={event['event_id']} | "
                    f"type={event['event_type']} | "
                    f"severity={event['severity']} | "
                    f"MinIO={object_name}"
                )
            except Exception as e:
                print(f"[ERROR] Failed to save event {event.get('event_id')} to MinIO: {e}")
                rejected_count += 1

            if max_messages and processed_count >= max_messages:
                print(f"\n[INFO] Reached max_messages limit ({max_messages}). Stopping.")
                break

    except KeyboardInterrupt:
        print("\n[INFO] Consumer stopped by user (Ctrl+C).")
    finally:
        try:
            consumer.close()
            print("\n" + "=" * 60)
            print("  CONSUMER SUMMARY")
            print("=" * 60)
            print(f"Total processed : {processed_count}")
            print(f"Valid & Saved   : {saved_count}")
            print(f"Rejected        : {rejected_count}")
            print("=" * 60)
        except Exception as e:
            print(f"[WARNING] Exception closing consumer: {e}")

    return saved_count, rejected_count


if __name__ == "__main__":
    main()