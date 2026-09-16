"""
CyberShield Data Platform
End-to-End Test: Silver → PostgreSQL Pipeline

Verifies:
1. PostgreSQL is accessible via JDBC
2. security_events table exists
3. Silver layer is readable from Spark
4. Row count consistency between Silver and PostgreSQL
5. event_id non-NULL and unique (no duplicates)
6. Valid timestamps
7. Pipeline idempotency (re-running does not duplicate records)
"""

import os
import sys
from datetime import datetime, timezone

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


# ============================================================
# Configuration
# ============================================================

MINIO_BUCKET = os.getenv("MINIO_BUCKET", "cybershield-data")
SILVER_PATH = f"s3a://{MINIO_BUCKET}/silver/events/"

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "cyber_platform")
POSTGRES_USER = os.getenv("POSTGRES_USER", "cyber_admin")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "CyberShield2026")

JDBC_URL = f"jdbc:postgresql://{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
JDBC_PROPERTIES = {
    "user": POSTGRES_USER,
    "password": POSTGRES_PASSWORD,
    "driver": "org.postgresql.Driver",
}

TARGET_TABLE = "security_events"


# ============================================================
# Tests
# ============================================================

def test_spark_session(spark):
    """Test 1: Verify Spark Session is active."""
    print("[TEST 1] Spark session... ", end="")
    assert spark is not None and spark.sparkContext is not None, "SparkSession inactive"
    print(f"OK (version={spark.version})")


def test_postgres_connection(spark):
    """Test 2: Verify PostgreSQL JDBC connectivity."""
    print(f"[TEST 2] PostgreSQL connection ({JDBC_URL})... ", end="")
    jvm = spark.sparkContext._gateway.jvm
    conn = jvm.java.sql.DriverManager.getConnection(JDBC_URL, POSTGRES_USER, POSTGRES_PASSWORD)
    assert conn is not None, "Failed to establish JDBC connection"
    conn.close()
    print("OK")


def test_table_exists(spark):
    """Test 3: Verify security_events table exists."""
    print(f"[TEST 3] Table '{TARGET_TABLE}' existence... ", end="")
    df = spark.read.jdbc(url=JDBC_URL, table=TARGET_TABLE, properties=JDBC_PROPERTIES)
    assert df is not None, f"Table {TARGET_TABLE} not readable"
    print("OK")
    return df


def test_read_silver(spark):
    """Test 4: Verify Silver layer is readable."""
    print(f"[TEST 4] Read Silver ({SILVER_PATH})... ", end="")
    silver_df = spark.read.parquet(SILVER_PATH)
    count = silver_df.count()
    assert count > 0, f"Silver layer is empty (count={count})"
    print(f"OK ({count} records)")
    return silver_df, count


def test_postgres_data_quality(pg_df, silver_count):
    """Test 5: Verify PostgreSQL record counts and null/duplicate checks."""
    print("[TEST 5] PostgreSQL data quality & consistency... ", end="")

    pg_count = pg_df.count()
    distinct_ids = pg_df.select("event_id").distinct().count()
    null_ids = pg_df.filter(F.col("event_id").isNull()).count()
    null_ts = pg_df.filter(F.col("timestamp").isNull()).count()

    issues = []
    if pg_count != silver_count:
        issues.append(f"Row count mismatch (Silver={silver_count}, PG={pg_count})")
    if distinct_ids != pg_count:
        issues.append(f"Duplicates found ({pg_count - distinct_ids})")
    if null_ids > 0:
        issues.append(f"Null event_ids found ({null_ids})")
    if null_ts > 0:
        issues.append(f"Null timestamps found ({null_ts})")

    assert not issues, f"Quality issues: {', '.join(issues)}"
    print(f"OK (PG records={pg_count}, distinct={distinct_ids}, null_ids={null_ids}, null_ts={null_ts})")


def test_idempotency(spark, silver_count):
    """Test 6: Verify re-running pipeline does not duplicate rows in PostgreSQL."""
    print("[TEST 6] Pipeline idempotency check... ", end="")
    
    # Add root and services/processing to sys.path if not present
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(current_dir, "../.."))
    for p in [current_dir, root_dir]:
        if p not in sys.path:
            sys.path.insert(0, p)

    try:
        from silver_to_postgres import prepare_for_postgres, load_to_postgres
    except ImportError:
        from services.processing.silver_to_postgres import prepare_for_postgres, load_to_postgres

    # Read Silver data and re-run load logic
    silver_df = spark.read.parquet(SILVER_PATH)
    prepared_df = prepare_for_postgres(silver_df)
    load_to_postgres(spark, prepared_df)

    # Read back PG count
    pg_df = spark.read.jdbc(url=JDBC_URL, table=TARGET_TABLE, properties=JDBC_PROPERTIES)
    n2 = pg_df.count()

    assert n2 == silver_count, f"Idempotency check failed! Expected {silver_count} rows, got {n2}"
    print(f"OK (Initial={silver_count}, Re-run={n2})")


# ============================================================
# Main Test Runner
# ============================================================

def main():
    print()
    print("=" * 60)
    print("  CYBERSHIELD - SILVER → POSTGRESQL TEST SUITE")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    print()

    passed = 0
    failed = 0

    spark = (
        SparkSession.builder
        .appName("CyberShield-Test-Silver-Postgres")
        .getOrCreate()
    )

    try:
        test_spark_session(spark)
        passed += 1

        test_postgres_connection(spark)
        passed += 1

        silver_df, silver_count = test_read_silver(spark)
        passed += 1

        pg_df = test_table_exists(spark)
        passed += 1

        test_postgres_data_quality(pg_df, silver_count)
        passed += 1

        test_idempotency(spark, silver_count)
        passed += 1

    except Exception as e:
        failed += 1
        print(f"\n[FAIL] {e}")
        import traceback
        traceback.print_exc()
    finally:
        spark.stop()

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
