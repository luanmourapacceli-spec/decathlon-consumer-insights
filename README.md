# Decathlon Consumer Insights

**Live Dashboard:** https://decathlon-consumer-insights.streamlit.app

> A data engineering portfolio project analyzing customer satisfaction and pain points across Decathlon stores in Portugal, Spain, and Brazil.

## 📊 Project Overview

This project builds an end-to-end data pipeline that collects, processes, and visualizes customer reviews to identify satisfaction patterns and key pain points by sport category, store location, and language.

**Built to demonstrate data engineering skills aligned with Decathlon Digital's tech stack.**

---

## Architecture

```
Reviews (PT/ES/EN)
       ↓
  Kafka Producer
       ↓
Apache Kafka (Docker)
       ↓
  Kafka Consumer
       ↓
 Data Processing
  (Pandas + NLP)
       ↓
 Streamlit Dashboard
```

---

## Key Insights

| Category    | Avg Rating | Satisfaction |
| ----------- | ---------- | ------------ |
| 🏈 Football | 4.93       | ✅ High      |
| 🏊 Swimming | 4.91       | ✅ High      |
| 🏃 Running  | 4.27       | ✅ High      |
| 💪 Fitness  | 3.16       | ⚠️ Medium    |
| 🚴 Cycling  | 1.41       | ❌ Low       |
| 🧘 Yoga     | 1.11       | ❌ Low       |

**Top pain points:** product quality, delivery delays, app crashes, incorrect size charts.

---

## Tech Stack

| Layer         | Technologies                 |
| ------------- | ---------------------------- |
| Ingestion     | Python, Apache Kafka, Docker |
| Processing    | Pandas, TextBlob, NLP        |
| Orchestration | Apache Airflow (in progress) |
| Storage       | PostgreSQL, JSON             |
| Visualization | Streamlit, Plotly            |
| DevOps        | Docker, Git, GitHub Actions  |
| Languages     | Python 3.14, SQL             |

---

## How to Run

### Prerequisites

- Python 3.11+
- Docker Desktop
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/luanmourapacceli-spec/decathlon-consumer-insights.git
cd decathlon-consumer-insights

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Run the pipeline

```bash
# 1. Start Kafka
cd infra && docker-compose up -d

# 2. Generate synthetic reviews
python data/synthetic_reviews.py

# 3. Publish to Kafka
python dags/kafka_producer.py

# 4. Consume from Kafka
python dags/kafka_consumer.py

# 5. Process and analyze
python spark/process_reviews.py

# 6. Launch dashboard
streamlit run dashboard/app.py
```

---

## 📁 Project Structure

decathlon-consumer-insights/
├── dags/ # Kafka producer and consumer
├── spark/ # Data processing jobs
├── ml/ # Sentiment analysis models
├── dashboard/ # Streamlit interactive dashboard
├── data/ # Raw and processed data
├── infra/ # Docker + docker-compose
└── requirements.txt # Python dependencies

---

## About

Built by **Luan Moura** as a portfolio project targeting a Data Engineering role at Decathlon Digital.

- 📧 luanmourapacceli@gmail.com
- 🔗 [GitHub](https://github.com/luanmourapacceli-spec)
- 💼 [LinkedIn](https://linkedin.com/in/luan-moura)
