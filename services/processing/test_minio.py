from pyspark.sql import SparkSession


def main():
    spark = (
        SparkSession.builder
        .appName("CyberShield-MinIO-Test")
        .getOrCreate()
    )

    print("=" * 60)
    print("TEST SPARK -> MINIO")
    print("=" * 60)

    path = "s3a://cybershield-data/bronze/events/"

    print(f"Reading: {path}")

    df = spark.read.option("recursiveFileLookup", "true").option("multiLine", "true").json(path)

    print("\nSchema:")
    df.printSchema()

    print("\nData:")
    df.show(truncate=False)

    print(f"\nNumber of events: {df.count()}")

    spark.stop()


if __name__ == "__main__":
    main()