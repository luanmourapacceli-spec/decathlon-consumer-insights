import json
import pandas as pd
from textblob import TextBlob
from langdetect import detect

def load_reviews(path: str = "data/reviews_synthetic.json") -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)


def analyze_sentiment(text: str) -> dict:
    """Analisa sentimento de um texto e retorna score e classificação."""
    try:
        blob = TextBlob(text)
        score = blob.sentiment.polarity  # -1.0 (negativo) até 1.0 (positivo)

        if score > 0.1:
            label = "positive"
        elif score < -0.1:
            label = "negative"
        else:
            label = "neutral"

        return {"sentiment_score": round(score, 3), "sentiment_label": label}
    except Exception:
        return {"sentiment_score": 0.0, "sentiment_label": "neutral"}


def run_analysis(df: pd.DataFrame) -> pd.DataFrame:
    print(f"📊 Analisando {len(df)} reviews...")

    # Aplica análise de sentimento em cada review
    sentiments = df["text"].apply(analyze_sentiment)
    df["sentiment_score"] = sentiments.apply(lambda x: x["sentiment_score"])
    df["sentiment_label"] = sentiments.apply(lambda x: x["sentiment_label"])

    return df


def print_insights(df: pd.DataFrame):
    print("\n" + "="*50)
    print("📈 INSIGHTS — DECATHLON CONSUMER ANALYSIS")
    print("="*50)

    # Distribuição de sentimentos
    print("\n🎯 Distribuição de sentimentos:")
    dist = df["sentiment_label"].value_counts()
    for label, count in dist.items():
        pct = round(count / len(df) * 100, 1)
        print(f"   {label}: {count} reviews ({pct}%)")

    # Rating médio por categoria
    print("\n⭐ Rating médio por categoria de esporte:")
    avg_rating = df.groupby("sport_category")["rating"].mean().sort_values()
    for category, rating in avg_rating.items():
        bar = "█" * int(rating * 2)
        print(f"   {category:<15} {bar} {round(rating, 2)}")

    # Top 3 categorias com mais insatisfação
    print("\n⚠️  Categorias com mais reviews negativas:")
    negative = df[df["sentiment_label"] == "negative"]
    top_negative = negative["sport_category"].value_counts().head(3)
    for category, count in top_negative.items():
        print(f"   {category}: {count} reviews negativas")

    # Reviews mais negativas
    print("\n💬 Exemplos de reviews mais negativas:")
    worst = df.nsmallest(3, "sentiment_score")[["store_city", "text", "sentiment_score"]]
    for _, row in worst.iterrows():
        print(f"   [{row['store_city']}] score={row['sentiment_score']}: {row['text'][:60]}...")

    print("\n" + "="*50)


def save_results(df: pd.DataFrame, path: str = "data/reviews_analyzed.json"):
    df.to_json(path, orient="records", force_ascii=False, indent=2)
    print(f"\n✅ Resultado salvo em {path}")


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "data/reviews_synthetic.json"
    df = load_reviews(path)
    df = run_analysis(df)
    print_insights(df)
    output = path.replace(".json", "_analyzed.json")
    save_results(df, output)