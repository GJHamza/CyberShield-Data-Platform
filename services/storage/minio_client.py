import io
import json
import os

from dotenv import load_dotenv
from minio import Minio


load_dotenv()


MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "cybershield-data")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"


def create_minio_client():
    """Create and return a MinIO client."""

    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ROOT_USER,
        secret_key=MINIO_ROOT_PASSWORD,
        secure=MINIO_SECURE,
    )


def ensure_bucket(client):
    """Create the bucket if it does not exist."""

    if not client.bucket_exists(MINIO_BUCKET):
        client.make_bucket(MINIO_BUCKET)
        print(f"Bucket created: {MINIO_BUCKET}")
    else:
        print(f"Bucket already exists: {MINIO_BUCKET}")


def save_event(client, event):
    """
    Save a cybersecurity event as JSON in the Bronze layer.
    """

    event_id = event["event_id"]
    timestamp = event["timestamp"]

    date_part = timestamp[:10]
    year, month, day = date_part.split("-")

    object_name = (
        f"bronze/events/"
        f"{year}/{month}/{day}/"
        f"{event_id}.json"
    )

    event_json = json.dumps(
        event,
        indent=4,
        ensure_ascii=False,
    ).encode("utf-8")

    data_stream = io.BytesIO(event_json)

    client.put_object(
        bucket_name=MINIO_BUCKET,
        object_name=object_name,
        data=data_stream,
        length=len(event_json),
        content_type="application/json",
    )

    return object_name


if __name__ == "__main__":
    client = create_minio_client()

    ensure_bucket(client)

    print("MinIO connection successful!")
    print(f"Endpoint: {MINIO_ENDPOINT}")
    print(f"Bucket: {MINIO_BUCKET}") 