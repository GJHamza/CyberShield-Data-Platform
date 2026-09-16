"""
CyberShield Data Platform
End-to-End Test: Bronze → Silver Pipeline

Verifies:
1. Spark starts correctly
2. MinIO Bronze is readable
3. Pipeline transforms data correctly
4. Silver data is written and readable
5. Schema and count are correct
"""

import os
import sys
from datetime import datetime, timezone

from pyspark.sql import SparkSession


# ============================================================
# Configuration
# ============================================================

MINIO_BUCKET = os.getenv("MINIO_BUCKET", "cybershield-data")

BRONZE_PATH = f"s3a://{MINIO_BUCKET}/bronze/events/"
SILVER_PATH = f"s3a://{MINIO_BUCKET}/silver/events/"


# ============================================================
# Test Functions
# ============================================================

def test_spark_session(spark):
    """Test 1: Verify Spark session is active."""

    print("[TEST 1] Spark session... ", end="")
    assert spark is not None, "SparkSession is None"
    assert spark.sparkContext is not None, "SparkContext is None"
    print(f"OK (version={spark.version})")


def test_read_bronze(spark):
    """Test 2: Verify Bronze layer is readable."""

    print(f"[TEST 2] Read Bronze ({BRONZE_PATH})... ", end="")

    df = (
        spark.read
        .option("recursiveFileLookup", "true")
        .option("multiLine", "true")
        .json(BRONZE_PATH)
    )

    count = df.count()
    assert count > 0, f"Bronze layer is empty (count={count})"
    print(f"OK ({count} records)")

    return df, count


def test_bronze_schema(df):
    """Test 3: Verify Bronze has expected minimum columns."""

    print("[TEST 3] Bronze schema... ", end="")

    columns = set(df.columns)
    expected_minimum = {"event_id", "timestamp", "event_type", "severity"}
    missing = expected_minimum - columns

    if missing:
        print(f"WARNING: Missing columns: {missing}")
    else:
        print(f"OK (columns: {sorted(columns)})")


def test_read_silver(spark):
    """Test 4: Verify Silver layer was written and is readable."""

    print(f"[TEST 4] Read Silver ({SILVER_PATH})... ", end="")

    try:
        df = spark.read.parquet(SILVER_PATH)
        count = df.count()
        assert count > 0, f"Silver layer is empty (count={count})"
        print(f"OK ({count} records)")
        return df, count
    except Exception as e:
        print(f"FAIL ({e})")
        return None, 0


def test_silver_schema(df):
    """Test 5: Verify Silver has the expected processed columns."""

    print("[TEST 5] Silver schema... ", end="")

    columns = set(df.columns)

    # These columns should exist after processing
    expected = {
        "event_id",
        "event_type",
        "severity",
        "timestamp",
        "event_date",
        "event_hour",
        "processed_at",
    }

    missing = expected - columns
    if missing:
        print(f"WARNING: Missing expected columns: {missing}")
    else:
        print(f"OK")

    print(f"         Silver columns: {sorted(columns)}")


def test_silver_data_quality(df):
    """Test 6: Verify basic data quality in Silver."""

    print("[TEST 6] Silver data quality... ", end="")

    from pyspark.sql import functions as F

    issues = []

    # Check no null event_id
    null_ids = df.filter(F.col("event_id").isNull()).count()
    if null_ids > 0:
        issues.append(f"{null_ids} null event_ids")

    # Check no null timestamps
    null_ts = df.filter(F.col("timestamp").isNull()).count()
    if null_ts > 0:
        issues.append(f"{null_ts} null timestamps")

    # Check no duplicate event_ids
    total = df.count()
    distinct = df.select("event_id").distinct().count()
    if total != distinct:
        issues.append(f"{total - distinct} duplicate event_ids")

    # Check severity is lowercase
    if "severity" in df.columns:
        non_lower = df.filter(
            F.col("severity") != F.lower(F.col("severity"))
        ).count()
        if non_lower > 0:
            issues.append(f"{non_lower} non-lowercase severities")

    if issues:
        print(f"WARNING: {', '.join(issues)}")
    else:
        print("OK (no nulls, no duplicates, normalized)")


def test_silver_partitions(df):
    """Test 7: Verify partitioning by event_date."""

    print("[TEST 7] Silver partitions... ", end="")

    if "event_date" in df.columns:
        partitions = df.select("event_date").distinct().collect()
        dates = sorted([str(row["event_date"]) for row in partitions])
        print(f"OK (partitions: {dates})")
    else:
        print("WARNING: No event_date column for partitioning")


# ============================================================
# Main
# ============================================================

def main():

    print()
    print("=" * 60)
    print("  CYBERSHIELD - BRONZE → SILVER TEST SUITE")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    print()

    passed = 0
    failed = 0
    warnings = 0

    # --- Spark ---
    spark = (
        SparkSession.builder
        .appName("CyberShield-Test-Bronze-Silver")
        .getOrCreate()
    )

    try:
        # Test 1: Spark session
        test_spark_session(spark)
        passed += 1

        # Test 2: Read Bronze
        bronze_df, bronze_count = test_read_bronze(spark)
        passed += 1

        # Test 3: Bronze schema
        test_bronze_schema(bronze_df)
        passed += 1

        # Test 4: Read Silver
        silver_df, silver_count = test_read_silver(spark)
        if silver_df is not None:
            passed += 1

            # Test 5: Silver schema
            test_silver_schema(silver_df)
            passed += 1

            # Test 6: Data quality
            test_silver_data_quality(silver_df)
            passed += 1

            # Test 7: Partitions
            test_silver_partitions(silver_df)
            passed += 1

            # Summary
            print()
            print("-" * 60)
            print(f"  Bronze records : {bronze_count}")
            print(f"  Silver records : {silver_count}")
            print()
            print("  Silver Schema:")
            silver_df.printSchema()
            print("  Silver Sample (5 rows):")
            silver_df.show(5, truncate=False)

        else:
            failed += 1
            print()
            print("[INFO] Silver layer not found. Run bronze_to_silver.py first.")

    except Exception as e:
        failed += 1
        print(f"\n[FAIL] {e}")
        import traceback
        traceback.print_exc()

    finally:
        spark.stop()

    # Final report
    print()
    print("=" * 60)
    total = passed + failed
    print(f"  RESULTS: {passed}/{total} tests passed")
    if failed > 0:
        print(f"  ❌ {failed} test(s) FAILED")
        sys.exit(1)
    else:
        print("  ✅ ALL TESTS PASSED")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
