import json
import time
import random
from datetime import datetime
from google_play_scraper import reviews, Sort

# App IDs da Decathlon nas lojas
APPS = [
    {"app_id": "br.com.decathlon",  "language": "pt", "country": "br", "city": "Brasil"},
    {"app_id": "com.decathlon.app", "language": "es", "country": "es", "city": "Espanha"},
    {"app_id": "com.decathlon.app", "language": "pt", "country": "pt", "city": "Portugal"},
    {"app_id": "com.decathlon.app", "language": "fr", "country": "fr", "city": "França"},
]

def fetch_google_play_reviews(count: int = 50) -> list[dict]:
    all_reviews = []

    for app in APPS:
        print(f"Coletando Google Play — {app['city']}...")
        try:
            result, _ = reviews(
                app["app_id"],
                lang=app["language"],
                country=app["country"],
                sort=Sort.NEWEST,
                count=count,
            )

            for r in result:
                text = r.get("content", "")
                if not text or len(text) < 10:
                    continue

                all_reviews.append({
                    "review_id": f"gp_{r['reviewId']}",
                    "source": "google_play",
                    "store_id": f"app_{app['country']}",
                    "store_name": f"Decathlon App ({app['city']})",
                    "store_city": app["city"],
                    "rating": float(r.get("score", 3)),
                    "text": text,
                    "language": app["language"],
                    "date": r["at"].isoformat() if r.get("at") else datetime.now().isoformat(),
                    "sport_category": "other",
                    "collected_at": datetime.now().isoformat(),
                })

            print(f"  -> {len(result)} reviews coletadas")
            time.sleep(random.uniform(2, 4))

        except Exception as e:
            print(f"  -> Erro: {e}")
            continue

    return all_reviews


def save_reviews(reviews_list: list[dict], path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(reviews_list, f, ensure_ascii=False, indent=2)
    print(f"\n✅ {len(reviews_list)} reviews salvas em {path}")


if __name__ == "__main__":
    print("=== Coletando reviews reais da Decathlon ===\n")

    # Google Play
    gp_reviews = fetch_google_play_reviews(count=50)
    print(f"\nTotal Google Play: {len(gp_reviews)} reviews")

    # Salva
    output_path = "data/reviews_real.json"
    save_reviews(gp_reviews, output_path)

    # Mostra exemplo
    if gp_reviews:
        print("\nExemplo de review real:")
        print(json.dumps(gp_reviews[0], ensure_ascii=False, indent=2))