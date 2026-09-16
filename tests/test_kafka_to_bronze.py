"""
CyberShield Data Platform
End-to-End Test: Kafka → MinIO Bronze Pipeline

Verifies:
1. Kafka broker connectivity
2. Topic 'cyber-events' existence
3. Producer publishes events to Kafka
4. Consumer consumes events from Kafka
5. Events are saved to MinIO Bronze layer
6. Saved JSON files are valid and contain all mandatory fields
7. event_id matches between Kafka and MinIO
"""

import json
import os
import sys
import uuid
from datetime import datetime, timezone

import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from services.generator.generator import generate_event
from services.producer.producer import create_producer, send_event
from services.consumer.consumer import create_consumer, validate_event
from services.storage.minio_client import create_minio_client, ensure_bucket, save_event

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "cyber-events")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "cybershield-data")
NUM_TEST_EVENTS = 10


def test_kafka_connection():
    """Test 1: Verify Kafka broker connection."""
    print("[TEST 1] Kafka broker connectivity... ", end="")
    try:
        producer = create_producer()
        producer.close(timeout=2)
        print(f"OK ({KAFKA_BOOTSTRAP_SERVERS})")
        return True
    except Exception as e:
        print(f"FAIL ({e})")
        return False


def test_topic_exists():
    """Test 2: Verify Kafka topic exists."""
    print(f"[TEST 2] Kafka topic '{KAFKA_TOPIC}' existence... ", end="")
    from kafka.admin import KafkaAdminClient
    try:
        admin = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        topics = admin.list_topics()
        admin.close()
        assert KAFKA_TOPIC in topics, f"Topic '{KAFKA_TOPIC}' not found in {topics}"
        print("OK")
        return True
    except Exception as e:
        print(f"FAIL ({e})")
        return False


def test_producer_publish():
    """Test 3: Produce N distinct test events."""
    print(f"[TEST 3] Producing {NUM_TEST_EVENTS} test events... ", end="")
    producer = create_producer()
    test_events = []
    unique_tag = f"test-{uuid.uuid4().hex[:6]}"

    for i in range(NUM_TEST_EVENTS):
        event = generate_event()
        event["event_id"] = f"evt-{unique_tag}-{i+1:03d}"
        metadata = send_event(producer, event)
        assert metadata is not None, f"Failed to send event {event['event_id']}"
        test_events.append(event)

    producer.flush()
    producer.close(timeout=5)
    print(f"OK ({len(test_events)} events sent)")
    return test_events


def test_consumer_and_minio(expected_events):
    """Test 4-8: Consume events, check MinIO objects, validate JSON content."""
    print(f"[TEST 4-8] Consuming events & verifying MinIO Bronze storage... ")

    minio_client = create_minio_client()
    ensure_bucket(minio_client)

    expected_ids = {e["event_id"]: e for e in expected_events}
    consumer = create_consumer(group_id=f"test-group-{uuid.uuid4().hex[:6]}")

    found_ids = set()

    try:
        # Poll consumer for expected events
        for message in consumer:
            event = message.value
            is_valid, reason = validate_event(event)
            if not is_valid:
                continue

            event_id = event.get("event_id")
            if event_id in expected_ids:
                # Save to MinIO Bronze
                object_name = save_event(minio_client, event)

                # Verify object exists in MinIO
                stat = minio_client.stat_object(MINIO_BUCKET, object_name)
                assert stat is not None, f"Object {object_name} not found in MinIO"

                # Read back JSON from MinIO
                response = minio_client.get_object(MINIO_BUCKET, object_name)
                minio_data = json.loads(response.read().decode("utf-8"))
                response.close()
                response.release_conn()

                # Validate content
                assert minio_data["event_id"] == event_id, "event_id mismatch between Kafka and MinIO"
                assert minio_data["event_type"] == expected_ids[event_id]["event_type"]
                assert minio_data["source_ip"] == expected_ids[event_id]["source_ip"]
                assert minio_data["severity"] == expected_ids[event_id]["severity"]

                found_ids.add(event_id)
                print(f"  [OK] Validated {event_id} -> MinIO object: {object_name}")

            if len(found_ids) == len(expected_events):
                break

    finally:
        consumer.close()

    assert len(found_ids) == len(expected_events), (
        f"Mismatch in consumed events! Expected {len(expected_events)}, found {len(found_ids)}"
    )
    print(f"[TEST 4-8] All {len(found_ids)} test events consumed, validated, and stored in MinIO Bronze! OK")


def main():
    print()
    print("=" * 60)
    print("  CYBERSHIELD - KAFKA -> MINIO BRONZE E2E TEST SUITE")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    print()

    passed = 0
    failed = 0

    try:
        if test_kafka_connection():
            passed += 1
        else:
            failed += 1

        if test_topic_exists():
            passed += 1
        else:
            failed += 1

        test_events = test_producer_publish()
        passed += 1

        test_consumer_and_minio(test_events)
        passed += 5

    except Exception as e:
        failed += 1
        print(f"\n[FAIL] E2E Test Suite Error: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 60)
    total = passed + failed
    print(f"  RESULTS: {passed}/{total} assertions passed")
    if failed > 0:
        print(f"  [FAIL] {failed} assertion(s) FAILED")
        sys.exit(1)
    else:
        print("  [SUCCESS] ALL E2E TESTS PASSED")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
