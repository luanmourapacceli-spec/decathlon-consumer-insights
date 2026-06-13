from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lower, length, when

spark = SparkSession.builder \
    .appName("DecathlonReviewProcessor") \
    .config("spark.jars.packages", "org.postgresql:postgresql:42.6.0") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

POSTGRES_URL = "jdbc:postgresql://decathlon_postgres:5432/decathlon_insights"
POSTGRES_PROPS = {
    "user": "postgres",
    "password": "postgres",
    "driver": "org.postgresql.Driver"
}

df = spark.read.jdbc(
    url=POSTGRES_URL,
    table="reviews",
    properties=POSTGRES_PROPS
)

print(f"Total reviews carregados: {df.count()}")

df_processed = df \
    .withColumn("review_length", length(col("review_text"))) \
    .withColumn("review_text_lower", lower(col("review_text"))) \
    .withColumn("length_category",
        when(col("review_length") < 50, "short")
        .when(col("review_length") < 200, "medium")
        .otherwise("long")
    )

df_processed.write.jdbc(
    url=POSTGRES_URL,
    table="reviews_spark_processed",
    mode="overwrite",
    properties=POSTGRES_PROPS
)

print("Processamento concluído. Tabela reviews_spark_processed atualizada.")
spark.stop()