"""
CyberShield Data Platform
Silver → PostgreSQL Pipeline

Reads cleaned Parquet events from MinIO Silver,
loads them into PostgreSQL security_events table via JDBC.
Uses staging table + ON CONFLICT for idempotent upserts.
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
STAGING_TABLE = "security_events_staging"


# ============================================================
# SparkSession
# ============================================================

def create_spark_session():
    """Create a SparkSession configured for CyberShield."""
    return (
        SparkSession.builder
        .appName("CyberShield-Silver-To-PostgreSQL")
        .getOrCreate()
    )


# ============================================================
# Read Silver
# ============================================================

def read_silver(spark):
    """Read cleaned Parquet events from MinIO Silver layer."""

    print(f"\n[SILVER] Reading from: {SILVER_PATH}")

    df = spark.read.parquet(SILVER_PATH)

    count = df.count()
    print(f"[SILVER] Records read: {count}")
    print(f"[SILVER] Columns: {sorted(df.columns)}")

    return df, count


# ============================================================
# Prepare for PostgreSQL
# ============================================================

def prepare_for_postgres(df):
    """
    Prepare the DataFrame for PostgreSQL loading.
    - Cast types for JDBC compatibility
    - Select only the columns that match the target table
    """

    target_columns = [
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

    # Keep only columns that exist in the DataFrame
    available = [c for c in target_columns if c in df.columns]
    df = df.select(*available)

    # Cast ports to integer (they may be long from Parquet)
    if "source_port" in df.columns:
        df = df.withColumn("source_port", F.col("source_port").cast("int"))
    if "destination_port" in df.columns:
        df = df.withColumn("destination_port", F.col("destination_port").cast("int"))

    print(f"[PREPARE] Columns selected: {available}")
    print(f"[PREPARE] Records: {df.count()}")

    return df


# ============================================================
# Load to PostgreSQL (Idempotent)
# ============================================================

def load_to_postgres(spark, df):
    """
    Load data to PostgreSQL using staging table + ON CONFLICT.
    This ensures idempotent loading (no duplicates on re-run).

    Strategy:
    1. Write all Silver data to a staging table (overwrite)
    2. INSERT INTO security_events SELECT ... FROM staging
       ON CONFLICT (event_id) DO NOTHING
    3. Drop the staging table
    """

    print(f"\n[LOAD] JDBC URL: {JDBC_URL}")
    print(f"[LOAD] Target table: {TARGET_TABLE}")
    print(f"[LOAD] Staging table: {STAGING_TABLE}")

    # Step 1: Write to staging table (overwrite mode)
    print("[LOAD] Step 1/3: Writing to staging table...")

    df.write.jdbc(
        url=JDBC_URL,
        table=STAGING_TABLE,
        mode="overwrite",
        properties=JDBC_PROPERTIES,
    )

    print("[LOAD] Step 1/3: Staging table written ✓")

    # Step 2: Upsert from staging to target with ON CONFLICT
    print("[LOAD] Step 2/3: Upserting to target table...")

    # Build column list dynamically from the DataFrame
    columns = df.columns
    col_list = ", ".join(columns)

    upsert_sql = f"""
        INSERT INTO {TARGET_TABLE} ({col_list})
        SELECT {col_list} FROM {STAGING_TABLE}
        ON CONFLICT (event_id) DO NOTHING
    """

    # Execute raw SQL via JDBC connection
    _execute_sql(upsert_sql)
    print("[LOAD] Step 2/3: Upsert complete ✓")

    # Step 3: Drop staging table
    print("[LOAD] Step 3/3: Cleaning up staging table...")
    _execute_sql(f"DROP TABLE IF EXISTS {STAGING_TABLE}")
    print("[LOAD] Step 3/3: Staging table dropped ✓")


def _execute_sql(sql):
    """Execute raw SQL against PostgreSQL via Spark's JVM Gateway."""
    from pyspark.sql import SparkSession

    spark = SparkSession.builder.getOrCreate()
    jvm = spark.sparkContext._gateway.jvm

    conn = jvm.java.sql.DriverManager.getConnection(
        JDBC_URL, POSTGRES_USER, POSTGRES_PASSWORD
    )
    try:
        stmt = conn.createStatement()
        stmt.execute(sql)
        stmt.close()
    finally:
        conn.close()


# ============================================================
# Verify PostgreSQL
# ============================================================

def verify_postgres(spark):
    """Read back data from PostgreSQL and display summary."""

    print(f"\n[VERIFY] Reading from PostgreSQL: {TARGET_TABLE}")

    pg_df = spark.read.jdbc(
        url=JDBC_URL,
        table=TARGET_TABLE,
        properties=JDBC_PROPERTIES,
    )

    total = pg_df.count()
    distinct_ids = pg_df.select("event_id").distinct().count()

    print(f"[VERIFY] Total records: {total}")
    print(f"[VERIFY] Distinct event_ids: {distinct_ids}")
    print(f"[VERIFY] Duplicates: {total - distinct_ids}")

    # Show distribution
    print("\n[VERIFY] By severity:")
    pg_df.groupBy("severity").count().orderBy("severity").show()

    print("[VERIFY] By event_type:")
    pg_df.groupBy("event_type").count().orderBy("event_type").show()

    print("[VERIFY] Sample (5 rows):")
    pg_df.select(
        "event_id", "event_type", "severity",
        "timestamp", "source_ip", "destination_ip"
    ).show(5, truncate=False)

    return total, distinct_ids


# ============================================================
# Main Pipeline
# ============================================================

def main():
    """Execute the Silver → PostgreSQL pipeline."""

    print()
    print("=" * 60)
    print("  CYBERSHIELD DATA PLATFORM")
    print("  Pipeline: SILVER → POSTGRESQL")
    print(f"  Started at: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    spark = create_spark_session()

    try:
        # 1. Read Silver
        silver_df, silver_count = read_silver(spark)

        if silver_count == 0:
            print("\n[ERROR] No data in Silver layer. Run Bronze→Silver first.")
            sys.exit(1)

        print("\n[SILVER] Schema:")
        silver_df.printSchema()

        # 2. Prepare
        print("\n[PIPELINE] Step 1/3: Preparing data for PostgreSQL...")
        prepared_df = prepare_for_postgres(silver_df)

        # 3. Ensure target table exists
        print("[PIPELINE] Step 2/3: Creating target table if needed...")
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS security_events (
                id SERIAL PRIMARY KEY,
                event_id VARCHAR(50) UNIQUE NOT NULL,
                event_type VARCHAR(100),
                severity VARCHAR(20),
                timestamp TIMESTAMPTZ NOT NULL,
                event_date DATE,
                event_hour INTEGER,
                source_ip TEXT,
                destination_ip TEXT,
                protocol VARCHAR(20),
                source_port INTEGER,
                destination_port INTEGER,
                processed_at TIMESTAMPTZ,
                loaded_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
        """
        _execute_sql(create_table_sql)
        print("[PIPELINE] Target table ready ✓")

        # 4. Load
        print("[PIPELINE] Step 3/3: Loading to PostgreSQL...")
        load_to_postgres(spark, prepared_df)

        # 5. Verify
        total, distinct = verify_postgres(spark)

        # Summary
        print()
        print("=" * 60)
        print("  PIPELINE COMPLETE ✓")
        print(f"  Finished at: {datetime.now(timezone.utc).isoformat()}")
        print(f"  Silver records: {silver_count}")
        print(f"  PostgreSQL records: {total}")
        print(f"  Duplicates: {total - distinct}")
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
