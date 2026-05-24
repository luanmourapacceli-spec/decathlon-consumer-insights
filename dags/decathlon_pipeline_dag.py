"""
Decathlon Consumer Insights — Pipeline DAG
Orquestra: coleta → processamento → análise → atualização
Roda automaticamente toda sexta-feira às 08:00
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "luan-moura",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "decathlon_consumer_insights",
    default_args=default_args,
    description="Pipeline de análise de satisfação dos consumidores Decathlon",
    schedule_interval="0 8 * * 5",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["decathlon", "consumer-insights", "nlp"],
)


def collect_reviews():
    import sys
    sys.path.append("/opt/airflow")
    from data.real_reviews_scraper import fetch_google_play_reviews, save_reviews
    reviews = fetch_google_play_reviews(count=100)
    save_reviews(reviews, "/opt/airflow/data/reviews_real.json")
    print(f"✅ {len(reviews)} reviews coletadas")
    return len(reviews)


def run_sentiment():
    import sys
    sys.path.append("/opt/airflow")
    from ml.sentiment_analysis import load_reviews, run_analysis, save_results
    df = load_reviews("/opt/airflow/data/reviews_real.json")
    df = run_analysis(df)
    save_results(df, "/opt/airflow/data/reviews_real_analyzed.json")
    print(f"✅ Sentimento analisado para {len(df)} reviews")


def publish_kafka():
    import json
    from kafka import KafkaProducer
    with open("/opt/airflow/data/reviews_real_analyzed.json", "r", encoding="utf-8") as f:
        reviews = json.load(f)
    producer = KafkaProducer(
        bootstrap_servers="decathlon_kafka:9092",
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
    )
    for review in reviews:
        producer.send("decathlon.reviews.raw", key=review.get("store_id", ""), value=review)
    producer.flush()
    producer.close()
    print(f"✅ {len(reviews)} reviews publicadas no Kafka")


def load_postgres():
    import json
    import psycopg2
    from psycopg2.extras import execute_values
    import pandas as pd

    conn = psycopg2.connect(
        host="decathlon_postgres",
        port=5432,
        dbname="decathlon_insights",
        user="postgres",
        password="postgres",
    )

    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                review_id TEXT PRIMARY KEY,
                source TEXT, store_id TEXT, store_name TEXT,
                store_city TEXT, rating NUMERIC(3,1),
                review_text TEXT, language TEXT,
                review_date TIMESTAMPTZ, sport_category TEXT,
                sentiment_label TEXT, sentiment_score NUMERIC(5,3),
                collected_at TIMESTAMPTZ, ingested_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
    conn.commit()

    with open("/opt/airflow/data/reviews_real_analyzed.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    df = pd.DataFrame(data)
    if "bert_label" in df.columns and "sentiment_label" not in df.columns:
        df["sentiment_label"] = df["bert_label"]
    if "bert_score" in df.columns and "sentiment_score" not in df.columns:
        df["sentiment_score"] = df["bert_score"]

    rows = [(
        r.get("review_id"), r.get("source"), r.get("store_id"),
        r.get("store_name"), r.get("store_city"), r.get("rating"),
        r.get("text"), r.get("language"), r.get("date"),
        r.get("sport_category"), r.get("sentiment_label"),
        r.get("sentiment_score"), r.get("collected_at"),
    ) for _, r in df.iterrows()]

    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO reviews
                (review_id, source, store_id, store_name, store_city,
                 rating, review_text, language, review_date, sport_category,
                 sentiment_label, sentiment_score, collected_at)
            VALUES %s
            ON CONFLICT (review_id) DO UPDATE SET ingested_at = NOW()
        """, rows)
    conn.commit()
    conn.close()
    print(f"✅ {len(rows)} reviews carregadas no PostgreSQL")


task_collect = PythonOperator(
    task_id="collect_google_play_reviews",
    python_callable=collect_reviews,
    dag=dag,
)

task_sentiment = PythonOperator(
    task_id="run_sentiment_analysis",
    python_callable=run_sentiment,
    dag=dag,
)

task_kafka = PythonOperator(
    task_id="publish_to_kafka",
    python_callable=publish_kafka,
    dag=dag,
)

task_load = PythonOperator(
    task_id="load_to_postgres",
    python_callable=load_postgres,
    dag=dag,
)

task_notify = BashOperator(
    task_id="pipeline_complete",
    bash_command='echo "Pipeline Decathlon Consumer Insights concluído! $(date)"',
    dag=dag,
)

task_collect >> task_sentiment >> task_kafka >> task_load >> task_notify