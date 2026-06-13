import json
import time
import pandas as pd
import mlflow
import mlflow.sklearn
from transformers import pipeline
from datetime import datetime


MLFLOW_TRACKING_URI = "http://localhost:5000"
EXPERIMENT_NAME = "decathlon-bert-sentiment"


def load_reviews(path: str) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)


def run_bert_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)

    with mlflow.start_run(run_name=f"bert-run-{datetime.now().strftime('%Y%m%d-%H%M%S')}"):

        mlflow.log_param("model_name", "nlptown/bert-base-multilingual-uncased-sentiment")
        mlflow.log_param("total_reviews", len(df))
        mlflow.log_param("languages", list(df["language"].unique()) if "language" in df.columns else "unknown")
        mlflow.log_param("sources", list(df["source"].unique()) if "source" in df.columns else "unknown")

        print("🤖 Carregando modelo BERT multilíngue...")
        start_time = time.time()

        sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="nlptown/bert-base-multilingual-uncased-sentiment",
            truncation=True,
            max_length=512,
        )

        load_time = round(time.time() - start_time, 2)
        mlflow.log_metric("model_load_time_seconds", load_time)
        print(f"✅ Modelo carregado em {load_time}s! Analisando {len(df)} reviews...\n")

        labels = []
        scores = []
        inference_start = time.time()

        for i, text in enumerate(df["text"]):
            try:
                result = sentiment_pipeline(str(text)[:512])[0]
                stars = int(result["label"].split()[0])

                if stars >= 4:
                    label = "positive"
                elif stars <= 2:
                    label = "negative"
                else:
                    label = "neutral"

                score = (stars - 3) / 2
                labels.append(label)
                scores.append(round(score, 3))

            except Exception:
                labels.append("neutral")
                scores.append(0.0)

            if (i + 1) % 25 == 0:
                print(f"   Processadas {i + 1}/{len(df)} reviews...")

        inference_time = round(time.time() - inference_start, 2)
        df["bert_label"] = labels
        df["bert_score"] = scores

        total = len(df)
        positive_count = labels.count("positive")
        negative_count = labels.count("negative")
        neutral_count = labels.count("neutral")
        avg_score = round(sum(scores) / total, 4)

        mlflow.log_metric("inference_time_seconds", inference_time)
        mlflow.log_metric("avg_sentiment_score", avg_score)
        mlflow.log_metric("positive_count", positive_count)
        mlflow.log_metric("negative_count", negative_count)
        mlflow.log_metric("neutral_count", neutral_count)
        mlflow.log_metric("positive_pct", round(positive_count / total * 100, 2))
        mlflow.log_metric("negative_pct", round(negative_count / total * 100, 2))
        mlflow.log_metric("neutral_pct", round(neutral_count / total * 100, 2))

        if "rating" in df.columns:
            avg_rating = round(df["rating"].mean(), 4)
            mlflow.log_metric("avg_rating", avg_rating)

        print(f"\n✅ MLflow run registrado!")
        print(f"   Positivos: {positive_count} ({round(positive_count/total*100,1)}%)")
        print(f"   Negativos: {negative_count} ({round(negative_count/total*100,1)}%)")
        print(f"   Neutros:   {neutral_count} ({round(neutral_count/total*100,1)}%)")
        print(f"   Score médio: {avg_score}")
        print(f"   Tempo de inferência: {inference_time}s")

    return df


def save_results(df: pd.DataFrame, path: str):
    df.to_json(path, orient="records", force_ascii=False, indent=2)
    print(f"✅ Resultado salvo em {path}")


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "data/reviews_real.json"

    print(f"=== BERT Sentiment Analysis + MLflow ===")
    print(f"Arquivo: {path}\n")

    df = load_reviews(path)
    df = run_bert_sentiment(df)

    output = path.replace(".json", "_bert.json")
    save_results(df, output)