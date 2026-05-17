import json
import pandas as pd
from transformers import pipeline
from datetime import datetime


def load_reviews(path: str) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)


def run_bert_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    print("🤖 Carregando modelo BERT multilíngue...")
    print("   (primeira vez demora ~1 minuto para baixar o modelo)")

    # Modelo multilíngue — funciona em PT, ES, FR, EN
    sentiment_pipeline = pipeline(
        "sentiment-analysis",
        model="nlptown/bert-base-multilingual-uncased-sentiment",
        truncation=True,
        max_length=512,
    )

    print(f"✅ Modelo carregado! Analisando {len(df)} reviews...\n")

    labels = []
    scores = []

    for i, text in enumerate(df["text"]):
        try:
            result = sentiment_pipeline(text[:512])[0]
            # Modelo retorna 1-5 stars
            stars = int(result["label"].split()[0])

            if stars >= 4:
                label = "positive"
            elif stars <= 2:
                label = "negative"
            else:
                label = "neutral"

            # Normaliza score para -1 a 1
            score = (stars - 3) / 2

            labels.append(label)
            scores.append(round(score, 3))

        except Exception:
            labels.append("neutral")
            scores.append(0.0)

        if (i + 1) % 25 == 0:
            print(f"   Processadas {i + 1}/{len(df)} reviews...")

    df["bert_label"] = labels
    df["bert_score"] = scores
    return df


def print_bert_insights(df: pd.DataFrame):
    print("\n" + "="*50)
    print("🤖 BERT MULTILINGUAL — INSIGHTS")
    print("="*50)

    print("\n🎯 Distribuição de sentimentos (BERT):")
    dist = df["bert_label"].value_counts()
    for label, count in dist.items():
        pct = round(count / len(df) * 100, 1)
        print(f"   {label}: {count} reviews ({pct}%)")

    print("\n🌍 Sentimento por cidade/país:")
    city_sentiment = df.groupby("store_city")["bert_score"].mean().sort_values()
    for city, score in city_sentiment.items():
        bar = "█" * int(abs(score) * 10)
        sentiment = "😊" if score > 0 else "😞"
        print(f"   {city:<12} {sentiment} {bar} {round(score, 2)}")

    print("\n⚠️  Reviews mais negativas (BERT):")
    worst = df.nsmallest(5, "bert_score")[["store_city", "language", "bert_score", "text"]]
    for _, row in worst.iterrows():
        print(f"   [{row['store_city']} | {row['language']}] score={row['bert_score']}")
        print(f"   \"{row['text'][:80]}...\"")
        print()

    print("="*50)


def save_results(df: pd.DataFrame, path: str):
    df.to_json(path, orient="records", force_ascii=False, indent=2)
    print(f"✅ Resultado salvo em {path}")


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "data/reviews_real.json"

    print(f"=== BERT Sentiment Analysis ===")
    print(f"Arquivo: {path}\n")

    df = load_reviews(path)
    df = run_bert_sentiment(df)
    print_bert_insights(df)

    output = path.replace(".json", "_bert.json")
    save_results(df, output)