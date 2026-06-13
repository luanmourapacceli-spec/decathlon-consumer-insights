# Decathlon Consumer Insights

**Live Dashboard (GCP Cloud Run):** https://streamlit-app-1016696917463.europe-west1.run.app

> A data engineering portfolio project analyzing customer satisfaction and pain points across Decathlon stores in Portugal, Spain, and Brazil — built to demonstrate skills aligned with Decathlon Digital's tech stack.

---

## Architecture

```
App Store + Reddit (2,064 reviews)
            ↓
      Kafka Producer
            ↓
   Apache Kafka (Docker)
            ↓
      Kafka Consumer
            ↓
   PostgreSQL (storage)
            ↓
  Apache Spark (processing)
            ↓
  BERT Multilingual (NLP)
            ↓
   Apache Airflow (orchestration)
            ↓
  Streamlit Dashboard → GCP Cloud Run
```

---

## Key Insights

| Category    | Avg Rating | Satisfaction |
| ----------- | ---------- | ------------ |
| 🏊 Swimming | 4.00       | ✅ High      |
| 🚴 Cycling  | 3.87       | ✅ High      |
| 💪 Fitness  | 3.33       | ⚠️ Medium    |
| 🥾 Hiking   | 2.66       | ❌ Low       |
| 🏃 Running  | 2.58       | ❌ Low       |
| 🏈 Football | 1.94       | ❌ Low       |

**Top pain points:** app delivery issues, football product quality, regional dissatisfaction in Brazil.

---

## Tech Stack

| Layer         | Technologies                    |
| ------------- | ------------------------------- |
| Ingestion     | Python, Apache Kafka, Docker    |
| Processing    | Apache Spark (PySpark), Pandas  |
| NLP           | BERT Multilingual, Transformers |
| Orchestration | Apache Airflow                  |
| Storage       | PostgreSQL                      |
| Visualization | Streamlit, Plotly               |
| Cloud         | GCP Cloud Run (europe-west1)    |
| DevOps        | Docker, Docker Compose, Git     |
| Languages     | Python 3.11, SQL                |

---

## Services (Docker Compose)

| Service           | Description                   | Port |
| ----------------- | ----------------------------- | ---- |
| Zookeeper         | Kafka coordination            | 2181 |
| Kafka             | Message broker                | 9092 |
| Kafka UI          | Kafka monitoring              | 8080 |
| PostgreSQL        | Data storage                  | 5432 |
| Airflow Webserver | Pipeline orchestration UI     | 8090 |
| Airflow Scheduler | DAG scheduling                | -    |
| Spark Master      | Distributed processing master | 8282 |
| Spark Worker      | Distributed processing worker | -    |

---

## Airflow DAGs

| DAG                           | Schedule           | Description                                |
| ----------------------------- | ------------------ | ------------------------------------------ |
| `decathlon_consumer_insights` | Every Friday 08:00 | Collect → Sentiment → Kafka → PostgreSQL   |
| `decathlon_spark_processing`  | Every Friday 09:00 | Spark job → process reviews → output table |

---

## How to Run

### Prerequisites

- Python 3.11+
- Docker Desktop
- Git

### Setup

```bash
git clone https://github.com/luanmourapacceli-spec/decathlon-consumer-insights.git
cd decathlon-consumer-insights

python -m venv venv
.\venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### Start all services

```bash
cd infra && docker compose up -d
```

### Access

| Service   | URL                   | Credentials   |
| --------- | --------------------- | ------------- |
| Airflow   | http://localhost:8090 | admin / admin |
| Kafka UI  | http://localhost:8080 | -             |
| Spark UI  | http://localhost:8282 | -             |
| Dashboard | http://localhost:8501 | -             |

### Run Spark job manually

```bash
docker exec decathlon_spark /opt/spark/bin/spark-submit \
  --packages org.postgresql:postgresql:42.6.0 \
  /opt/spark-jobs/process_reviews.py
```

---

## Project Structure

```
decathlon-consumer-insights/
├── dags/                   # Airflow DAGs + Kafka producer/consumer
│   ├── decathlon_pipeline_dag.py
│   └── spark_processing_dag.py
├── spark/                  # PySpark processing jobs
│   └── process_reviews.py
├── ml/                     # BERT sentiment analysis
│   └── sentiment_analysis.py
├── dashboard/              # Streamlit dashboard
│   └── app.py
├── data/                   # Raw and processed reviews
├── infra/                  # Docker Compose
│   └── docker-compose.yml
├── Dockerfile              # Cloud Run deployment
└── requirements.txt
```

---

## Cloud Deployment

Dashboard deployed on **GCP Cloud Run** (europe-west1 — Belgium):

```bash
gcloud builds submit --tag gcr.io/decathlon-insights-2026/streamlit-app
gcloud run deploy streamlit-app \
  --image gcr.io/decathlon-insights-2026/streamlit-app \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated
```

---

## About

Built by **Luan Moura** as a portfolio project targeting a Data Engineering role at Decathlon Digital.

- 📧 luanmourapacceli@gmail.com
- 🔗 [GitHub](https://github.com/luanmourapacceli-spec)
- 💼 [LinkedIn](https://linkedin.com/in/luan-moura)
