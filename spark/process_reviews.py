import pandas as pd
import json
from textblob import TextBlob


def analyze_sentiment(text: str) -> dict:
    try:
        score = float(TextBlob(text).sentiment.polarity)
        if score > 0.1:
            label = "positive"
        elif score < -0.1:
            label = "negative"
        else:
            label = "neutral"
        return {"sentiment_score": round(score, 3), "sentiment_label": label}
    except:
        return {"sentiment_score": 0.0, "sentiment_label": "neutral"}


def run(input_path: str = "data/reviews_from_kafka.json"):
    print("🚀 Iniciando processamento — Decathlon Consumer Insights")

    df = pd.read_json(input_path)
    print(f"✅ Reviews carregadas: {len(df)}")

    # Análise de sentimento
    sentiments = df["text"].apply(analyze_sentiment)
    df["sentiment_score"] = sentiments.apply(lambda x: x["sentiment_score"])
    df["sentiment_label"] = sentiments.apply(lambda x: x["sentiment_label"])

    print("\n⭐ Rating médio por categoria de esporte:")
    result1 = df.groupby("sport_category")["rating"].mean().round(2).sort_values()
    print(result1.to_string())

    print("\n🎯 Distribuição de sentimentos:")
    result2 = df["sentiment_label"].value_counts()
    print(result2.to_string())

    print("\n⚠️ Reviews negativas por categoria:")
    result3 = df[df["sentiment_label"] == "negative"]["sport_category"].value_counts()
    print(result3.to_string())

    print("\n🌍 Rating médio por cidade:")
    result4 = df.groupby("store_city")["rating"].mean().round(2).sort_values()
    print(result4.to_string())

    output_path = "data/reviews_spark_processed.json"
    df.to_json(output_path, orient="records", force_ascii=False, indent=2)
    print(f"\n✅ Resultado salvo em {output_path}")
    print("🏁 Job finalizado!")


if __name__ == "__main__":
    run()