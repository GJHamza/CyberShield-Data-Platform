"""
CyberShield Data Platform
Bronze → Silver Pipeline

Reads raw cybersecurity events from MinIO Bronze (JSON),
cleans, normalizes, validates, and writes to MinIO Silver (Parquet).
"""

import os
import sys
from datetime import datetime, timezone

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import TimestampType


# ============================================================
# Configuration
# ============================================================

MINIO_BUCKET = os.getenv("MINIO_BUCKET", "cybershield-data")

BRONZE_PATH = f"s3a://{MINIO_BUCKET}/bronze/events/"
SILVER_PATH = f"s3a://{MINIO_BUCKET}/silver/events/"

VALID_SEVERITIES = {"low", "medium", "high", "critical"}
VALID_EVENT_TYPES = {
    "port_scan",
    "brute_force",
    "failed_login",
    "malware_detected",
    "dns_anomaly",
    "suspicious_connection",
    "http_attack",
    "unauthorized_access",
    "data_exfiltration",
    "suspicious_login",
}


# ============================================================
# SparkSession
# ============================================================

def create_spark_session():
    """Create a SparkSession configured for CyberShield."""
    return (
        SparkSession.builder
        .appName("CyberShield-Bronze-To-Silver")
        .getOrCreate()
    )


# ============================================================
# Read Bronze
# ============================================================

def read_bronze(spark):
    """Read raw JSON events from MinIO Bronze layer."""

    print(f"\n[BRONZE] Reading from: {BRONZE_PATH}")

    df = (
        spark.read
        .option("recursiveFileLookup", "true")
        .option("multiLine", "true")
        .json(BRONZE_PATH)
    )

    count = df.count()
    print(f"[BRONZE] Records read: {count}")
    print(f"[BRONZE] Columns: {df.columns}")

    return df


# ============================================================
# Normalize Column Names
# ============================================================

def normalize_column_names(df):
    """
    Normalize all column names to snake_case.
    Handles: 'Event ID' → 'event_id', 'EventType' → 'event_type',
             'event-id' → 'event_id'
    """

    import re

    new_columns = []
    for col_name in df.columns:
        # Skip internal Spark columns
        if col_name.startswith("_"):
            continue

        # Insert underscore before uppercase letters (camelCase → camel_case)
        normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", col_name)
        # Replace hyphens and spaces with underscores
        normalized = re.sub(r"[-\s]+", "_", normalized)
        # Lowercase everything
        normalized = normalized.lower()
        # Remove leading/trailing underscores
        normalized = normalized.strip("_")

        new_columns.append((col_name, normalized))

    for old_name, new_name in new_columns:
        df = df.withColumnRenamed(old_name, new_name)

    # Drop internal corrupt record column if present
    if "_corrupt_record" in df.columns:
        corrupt_count = df.filter(F.col("_corrupt_record").isNotNull()).count()
        if corrupt_count > 0:
            print(f"[CLEAN] Warning: {corrupt_count} corrupt records found and will be dropped")
        df = df.filter(F.col("_corrupt_record").isNull()).drop("_corrupt_record")

    return df


# ============================================================
# Clean & Normalize Data
# ============================================================

def clean_and_normalize(df):
    """
    Clean and normalize cybersecurity event data.
    - Trim whitespace from string columns
    - Normalize severity and event_type to lowercase
    - Parse timestamp to TimestampType
    - Add derived columns: event_date, event_hour
    - Add technical column: processed_at
    """

    # --- Trim all string columns ---
    for field in df.schema.fields:
        if str(field.dataType) == "StringType":
            df = df.withColumn(field.name, F.trim(F.col(field.name)))

    # --- Normalize severity ---
    if "severity" in df.columns:
        df = df.withColumn("severity", F.lower(F.trim(F.col("severity"))))
    else:
        df = df.withColumn("severity", F.lit("unknown"))

    # --- Normalize event_type ---
    if "event_type" in df.columns:
        df = df.withColumn("event_type", F.lower(F.trim(F.col("event_type"))))
    else:
        df = df.withColumn("event_type", F.lit("unknown"))

    # --- Normalize protocol ---
    if "protocol" in df.columns:
        df = df.withColumn("protocol", F.upper(F.trim(F.col("protocol"))))

    # --- Parse timestamp ---
    if "timestamp" in df.columns:
        # Try ISO 8601 parsing (handles timezone offsets)
        df = df.withColumn(
            "timestamp_parsed",
            F.to_timestamp(F.col("timestamp"))
        )

        # Derive event_date and event_hour from parsed timestamp
        df = df.withColumn(
            "event_date",
            F.to_date(F.col("timestamp_parsed"))
        )
        df = df.withColumn(
            "event_hour",
            F.hour(F.col("timestamp_parsed"))
        )

        # Replace original timestamp with parsed version
        df = df.drop("timestamp").withColumnRenamed("timestamp_parsed", "timestamp")
    else:
        # If no timestamp column exists, use current time
        now = datetime.now(timezone.utc).isoformat()
        df = df.withColumn("timestamp", F.to_timestamp(F.lit(now)))
        df = df.withColumn("event_date", F.to_date(F.col("timestamp")))
        df = df.withColumn("event_hour", F.hour(F.col("timestamp")))

    # --- Add processed_at ---
    df = df.withColumn(
        "processed_at",
        F.current_timestamp()
    )

    return df


# ============================================================
# Validate Data
# ============================================================

def validate(df):
    """
    Validate data quality. Flag invalid records and remove duplicates.
    Returns (valid_df, invalid_df, quality_stats).
    """

    total_count = df.count()

    # --- Check for nulls ---
    null_event_id = df.filter(F.col("event_id").isNull()).count() if "event_id" in df.columns else total_count
    null_timestamp = df.filter(F.col("timestamp").isNull()).count() if "timestamp" in df.columns else total_count

    # --- Mark validity ---
    # An event is valid if it has a non-null event_id and a parsable timestamp
    conditions = []
    if "event_id" in df.columns:
        conditions.append(F.col("event_id").isNotNull())
    if "timestamp" in df.columns:
        conditions.append(F.col("timestamp").isNotNull())

    if conditions:
        validity_condition = conditions[0]
        for cond in conditions[1:]:
            validity_condition = validity_condition & cond
        df = df.withColumn("is_valid", validity_condition)
    else:
        df = df.withColumn("is_valid", F.lit(False))

    valid_df = df.filter(F.col("is_valid") == True)
    invalid_df = df.filter(F.col("is_valid") == False)

    invalid_count = invalid_df.count()

    # --- Remove duplicates on event_id ---
    before_dedup = valid_df.count()
    if "event_id" in valid_df.columns:
        valid_df = valid_df.dropDuplicates(["event_id"])
    after_dedup = valid_df.count()
    duplicates = before_dedup - after_dedup

    # --- Quality stats ---
    quality_stats = {
        "total_input": total_count,
        "valid_records": after_dedup,
        "invalid_records": invalid_count,
        "duplicates_removed": duplicates,
        "null_event_id": null_event_id,
        "null_timestamp": null_timestamp,
    }

    return valid_df, invalid_df, quality_stats


# ============================================================
# Data Quality Report
# ============================================================

def print_quality_report(stats):
    """Print a clear data quality report."""

    print()
    print("=" * 50)
    print("  CYBERSHIELD BRONZE → SILVER - QUALITY REPORT")
    print("=" * 50)
    print(f"  Input records        : {stats['total_input']}")
    print(f"  Valid records        : {stats['valid_records']}")
    print(f"  Invalid records      : {stats['invalid_records']}")
    print(f"  Duplicates removed   : {stats['duplicates_removed']}")
    print(f"  Null event_id        : {stats['null_event_id']}")
    print(f"  Null timestamp       : {stats['null_timestamp']}")
    print("=" * 50)

    # Compute data quality score
    if stats["total_input"] > 0:
        score = (stats["valid_records"] / stats["total_input"]) * 100
        print(f"  Data Quality Score   : {score:.1f}%")
    else:
        print("  Data Quality Score   : N/A (no input)")
    print("=" * 50)
    print()


# ============================================================
# Write Silver
# ============================================================

def write_silver(df):
    """
    Write cleaned data to MinIO Silver layer as Parquet,
    partitioned by event_date.
    """

    # Drop the is_valid flag before writing (all remaining records are valid)
    if "is_valid" in df.columns:
        df = df.drop("is_valid")

    # Ensure consistent column ordering
    desired_order = [
        "event_id",
        "event_type",
        "severity",
        "timestamp",
        "event_date",
        "event_hour",
        "source_ip",
        "destination_ip",
        "protocol",
        "source_port",
        "destination_port",
        "processed_at",
    ]

    # Keep only columns that exist, in the desired order,
    # then append any extra columns at the end
    existing_ordered = [c for c in desired_order if c in df.columns]
    extra_cols = [c for c in df.columns if c not in desired_order]
    final_order = existing_ordered + extra_cols

    df = df.select(*final_order)

    print(f"\n[SILVER] Writing to: {SILVER_PATH}")
    print(f"[SILVER] Partitioning by: event_date")
    print(f"[SILVER] Format: Parquet (snappy)")
    print(f"[SILVER] Records to write: {df.count()}")

    df.write.mode("overwrite").partitionBy("event_date").parquet(SILVER_PATH)

    print("[SILVER] Write complete ✓")

    return df


# ============================================================
# Verify Silver
# ============================================================

def verify_silver(spark):
    """Re-read Silver data to verify it was written correctly."""

    print(f"\n[VERIFY] Reading back Silver from: {SILVER_PATH}")

    silver_df = spark.read.parquet(SILVER_PATH)

    count = silver_df.count()
    print(f"[VERIFY] Silver records: {count}")

    print("\n[VERIFY] Silver schema:")
    silver_df.printSchema()

    print("\n[VERIFY] Silver sample (5 rows):")
    silver_df.show(5, truncate=False)

    # Show partitions
    if "event_date" in silver_df.columns:
        print("\n[VERIFY] Partitions (event_date):")
        silver_df.select("event_date").distinct().orderBy("event_date").show(truncate=False)

    return silver_df


# ============================================================
# Main Pipeline
# ============================================================

def main():
    """Execute the Bronze → Silver pipeline."""

    print()
    print("=" * 60)
    print("  CYBERSHIELD DATA PLATFORM")
    print("  Pipeline: BRONZE → SILVER")
    print(f"  Started at: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    # 1. Create Spark session
    spark = create_spark_session()

    try:
        # 2. Read Bronze
        bronze_df = read_bronze(spark)

        if bronze_df.count() == 0:
            print("\n[ERROR] No data found in Bronze layer. Aborting.")
            sys.exit(1)

        print("\n[BRONZE] Schema:")
        bronze_df.printSchema()

        # 3. Normalize column names
        print("\n[PIPELINE] Step 1/4: Normalizing column names...")
        df = normalize_column_names(bronze_df)

        # 4. Clean and normalize data
        print("[PIPELINE] Step 2/4: Cleaning and normalizing data...")
        df = clean_and_normalize(df)

        # 5. Validate
        print("[PIPELINE] Step 3/4: Validating data quality...")
        valid_df, invalid_df, quality_stats = validate(df)

        # 6. Print quality report
        print_quality_report(quality_stats)

        if quality_stats["valid_records"] == 0:
            print("[ERROR] No valid records after validation. Aborting.")
            sys.exit(1)

        # 7. Write Silver
        print("[PIPELINE] Step 4/4: Writing Silver layer...")
        write_silver(valid_df)

        # 8. Verify
        verify_silver(spark)

        print()
        print("=" * 60)
        print("  PIPELINE COMPLETE ✓")
        print(f"  Finished at: {datetime.now(timezone.utc).isoformat()}")
        print(f"  Bronze records: {quality_stats['total_input']}")
        print(f"  Silver records: {quality_stats['valid_records']}")
        print("=" * 60)
        print()

    except Exception as e:
        print(f"\n[FATAL] Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
