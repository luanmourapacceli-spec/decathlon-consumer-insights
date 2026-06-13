"""
Decathlon Consumer Insights — Spark Processing DAG
Executa o job PySpark de processamento de reviews após o pipeline principal
Roda automaticamente toda sexta-feira às 09:00 (1h após o pipeline principal)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "luan-moura",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "decathlon_spark_processing",
    default_args=default_args,
    description="Processamento distribuído de reviews com Apache Spark",
    schedule_interval="0 9 * * 5",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["decathlon", "consumer-insights", "spark"],
)


def check_reviews_exist():
    import psycopg2
    conn = psycopg2.connect(
        host="decathlon_postgres",
        port=5432,
        dbname="decathlon_insights",
        user="postgres",
        password="postgres",
    )
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM reviews")
        count = cur.fetchone()[0]
    conn.close()
    if count == 0:
        raise ValueError("Nenhum review encontrado no PostgreSQL. Abortando job Spark.")
    print(f"✅ {count} reviews disponíveis para processamento Spark")
    return count


def verify_spark_output():
    import psycopg2
    conn = psycopg2.connect(
        host="decathlon_postgres",
        port=5432,
        dbname="decathlon_insights",
        user="postgres",
        password="postgres",
    )
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_name = 'reviews_spark_processed'
        """)
        table_exists = cur.fetchone()[0]
        if not table_exists:
            raise ValueError("Tabela reviews_spark_processed não foi criada pelo Spark.")
        cur.execute("SELECT COUNT(*) FROM reviews_spark_processed")
        count = cur.fetchone()[0]
    conn.close()
    print(f"✅ Spark processou {count} reviews com sucesso")
    return count


task_check_reviews = PythonOperator(
    task_id="check_reviews_exist",
    python_callable=check_reviews_exist,
    dag=dag,
)

task_spark_submit = BashOperator(
    task_id="spark_submit_process_reviews",
    bash_command=(
        "docker exec decathlon_spark "
        "/opt/spark/bin/spark-submit "
        "--packages org.postgresql:postgresql:42.6.0 "
        "/opt/spark-jobs/process_reviews.py"
    ),
    dag=dag,
)

task_verify_output = PythonOperator(
    task_id="verify_spark_output",
    python_callable=verify_spark_output,
    dag=dag,
)

task_notify = BashOperator(
    task_id="spark_pipeline_complete",
    bash_command='echo "Spark processing concluído! $(date)"',
    dag=dag,
)

task_check_reviews >> task_spark_submit >> task_verify_output >> task_notify