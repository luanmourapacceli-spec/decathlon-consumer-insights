"""
Decathlon Consumer Insights — Multi Source Scraper
Fontes: Google Play, App Store, Trustpilot, Reddit, Google Maps, Decathlon.com
"""

import json
import time
import random
import requests
from datetime import datetime
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8,es;q=0.7,fr;q=0.6",
}


def normalize_review(review_id, source, store_id, store_name,
                     store_city, rating, text, language, date) -> dict:
    return {
        "review_id": review_id,
        "source": source,
        "store_id": store_id,
        "store_name": store_name,
        "store_city": store_city,
        "rating": float(rating),
        "text": text,
        "language": language,
        "date": date,
        "sport_category": "other",
        "collected_at": datetime.now().isoformat(),
    }


# ─────────────────────────────────────────────
# 1. GOOGLE PLAY
# ─────────────────────────────────────────────
def fetch_google_play(count: int = 100) -> list[dict]:
    from google_play_scraper import reviews, Sort
    apps = [
    {"app_id": "1567575282", "country": "br", "lang": "pt", "city": "Brasil"},
    {"app_id": "1168607403", "country": "es", "lang": "es", "city": "Espanha"},
    {"app_id": "1168607403", "country": "fr", "lang": "fr", "city": "França"},
    {"app_id": "1168607403", "country": "gb", "lang": "en", "city": "UK"},
    {"app_id": "1168607403", "country": "pt", "lang": "pt", "city": "Portugal"},
]
    results = []
    for app in apps:
        try:
            data, _ = reviews(app["app_id"], lang=app["lang"],
                              country=app["country"], sort=Sort.NEWEST, count=count)
            for r in data:
                if not r.get("content") or len(r["content"]) < 10:
                    continue
                results.append(normalize_review(
                    f"gp_{r['reviewId']}", "google_play",
                    f"app_{app['country']}", f"Decathlon App ({app['city']})",
                    app["city"], r.get("score", 3), r["content"],
                    app["lang"], r["at"].isoformat() if r.get("at") else datetime.now().isoformat()
                ))
            print(f"  Google Play {app['city']}: {len(data)} reviews")
            time.sleep(random.uniform(2, 4))
        except Exception as e:
            print(f"  Google Play {app['city']} erro: {e}")
    return results


# ─────────────────────────────────────────────
# 2. APP STORE (scraping direto via API pública)
# ─────────────────────────────────────────────
def fetch_app_store(count: int = 100) -> list[dict]:
    """App Store via iTunes API — público e sem autenticação."""
    apps = [
        {"app_id": "1567575282", "country": "br", "lang": "pt", "city": "Brasil"},
        {"app_id": "1168607403", "country": "es", "lang": "es", "city": "Espanha"},
        {"app_id": "1168607403", "country": "fr", "lang": "fr", "city": "França"},
        {"app_id": "1168607403", "country": "gb", "lang": "en", "city": "UK"},
        {"app_id": "1168607403", "country": "pt", "lang": "pt", "city": "Portugal"},
    ]
    results = []
    for app in apps:
        for page in range(1, 11):
            url = (
                f"https://itunes.apple.com/{app['country']}/rss/customerreviews/"
                f"page={page}/id={app['app_id']}/sortby=mostrecent/json"
            )
            try:
                resp = requests.get(url, headers=HEADERS, timeout=15)
                resp.raise_for_status()
                feed = resp.json().get("feed", {})
                entries = feed.get("entry", [])
                if not entries:
                    break
                # Primeira entrada é info do app, não review
                for entry in entries[1:]:
                    rating_obj = entry.get("im:rating", {})
                    if not rating_obj:
                        continue
                    text = entry.get("content", {}).get("label", "")
                    title = entry.get("title", {}).get("label", "")
                    full_text = f"{title}. {text}".strip(". ")
                    if len(full_text) < 10:
                        continue
                    rid = entry.get("id", {}).get("label", str(random.randint(0, 999999)))
                    rating = float(rating_obj.get("label", 3))
                    date = entry.get("updated", {}).get("label", datetime.now().isoformat())
                    results.append(normalize_review(
                        f"as_{rid}", "app_store",
                        f"appstore_{app['country']}",
                        f"Decathlon App Store ({app['city']})",
                        app["city"], rating, full_text, app["lang"], date
                    ))
                time.sleep(random.uniform(1, 2))
            except Exception as e:
                print(f"  App Store {app['city']} p{page} erro: {e}")
                break
        print(f"  App Store {app['city']}: {sum(1 for r in results if r['store_city']==app['city'])} reviews")
    return results
    """App Store RSS feed — público e sem autenticação."""
    apps = [
        {"app_id": "997405033", "country": "br", "lang": "pt", "city": "Brasil"},
        {"app_id": "997405033", "country": "es", "lang": "es", "city": "Espanha"},
        {"app_id": "997405033", "country": "fr", "lang": "fr", "city": "França"},
        {"app_id": "997405033", "country": "gb", "lang": "en", "city": "UK"},
        {"app_id": "997405033", "country": "pt", "lang": "pt", "city": "Portugal"},
    ]
    results = []
    for app in apps:
        for page in range(1, 6):  # até 5 páginas, 50 reviews cada
            url = (
                f"https://itunes.apple.com/{app['country']}/rss/customerreviews/"
                f"page={page}/id={app['app_id']}/sortby=mostrecent/json"
            )
            try:
                resp = requests.get(url, headers=HEADERS, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                entries = data.get("feed", {}).get("entry", [])
                if not entries:
                    break
                for entry in entries:
                    if "im:rating" not in entry:
                        continue
                    text = entry.get("content", {}).get("label", "")
                    if len(text) < 10:
                        continue
                    rid = entry.get("id", {}).get("label", f"as_{random.randint(0,999999)}")
                    rating = float(entry["im:rating"]["label"])
                    date = entry.get("updated", {}).get("label", datetime.now().isoformat())
                    results.append(normalize_review(
                        f"as_{rid}", "app_store",
                        f"appstore_{app['country']}", f"Decathlon App Store ({app['city']})",
                        app["city"], rating, text, app["lang"], date
                    ))
                if len(results) >= count * len(apps):
                    break
                time.sleep(random.uniform(1, 2))
            except Exception as e:
                print(f"  App Store {app['city']} p{page} erro: {e}")
                break
        print(f"  App Store {app['city']}: reviews coletadas")
    return results


# ─────────────────────────────────────────────
# 3. TRUSTPILOT
# ─────────────────────────────────────────────
def fetch_trustpilot(pages: int = 5) -> list[dict]:
    urls = [
        ("https://www.trustpilot.com/review/www.decathlon.com.br", "pt", "Brasil"),
        ("https://es.trustpilot.com/review/www.decathlon.es", "es", "Espanha"),
        ("https://fr.trustpilot.com/review/www.decathlon.fr", "fr", "França"),
        ("https://www.trustpilot.com/review/www.decathlon.co.uk", "en", "UK"),
    ]
    results = []
    for base_url, lang, city in urls:
        for page in range(1, pages + 1):
            url = f"{base_url}?page={page}"
            try:
                resp = requests.get(url, headers=HEADERS, timeout=15)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                scripts = soup.find_all("script", {"type": "application/ld+json"})
                for script in scripts:
                    try:
                        data = json.loads(script.string or "{}")
                        for item in data.get("review", []):
                            rating = item.get("reviewRating", {}).get("ratingValue", 3)
                            body = item.get("description", "")
                            if len(body) < 10:
                                continue
                            date = item.get("datePublished", datetime.now().isoformat())
                            author = item.get("author", {}).get("name", "anon")
                            rid = f"tp_{abs(hash(author + date)) % 999999}"
                            results.append(normalize_review(
                                rid, "trustpilot",
                                f"tp_{lang}", f"Decathlon Trustpilot ({city})",
                                city, float(rating), body, lang, date
                            ))
                    except Exception:
                        continue
                time.sleep(random.uniform(2, 4))
            except Exception as e:
                print(f"  Trustpilot {city} p{page} erro: {e}")
                break
        print(f"  Trustpilot {city}: reviews coletadas")
    return results


# ─────────────────────────────────────────────
# 4. REDDIT
# ─────────────────────────────────────────────
def fetch_reddit(limit: int = 100) -> list[dict]:
    """Reddit API pública — sem autenticação para posts públicos."""
    subreddits = [
        ("decathlon", "en"),
        ("running", "en"),
        ("cycling", "en"),
        ("Fitness", "en"),
    ]
    results = []
    headers = {**HEADERS, "Accept": "application/json"}

    for subreddit, lang in subreddits:
        url = f"https://www.reddit.com/r/{subreddit}/search.json"
        params = {
            "q": "decathlon",
            "sort": "new",
            "limit": limit,
            "t": "year",
        }
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            posts = data.get("data", {}).get("children", [])
            for post in posts:
                p = post.get("data", {})
                text = p.get("selftext", "") or p.get("title", "")
                if len(text) < 20:
                    continue
                score = p.get("score", 0)
                # Converte score Reddit para rating 1-5
                if score > 100:
                    rating = 5.0
                elif score > 50:
                    rating = 4.0
                elif score > 10:
                    rating = 3.0
                elif score > 0:
                    rating = 2.0
                else:
                    rating = 1.0
                created = datetime.fromtimestamp(p.get("created_utc", 0)).isoformat()
                rid = f"rd_{p.get('id', random.randint(0, 999999))}"
                results.append(normalize_review(
                    rid, "reddit",
                    f"reddit_{subreddit}", f"Reddit r/{subreddit}",
                    "Online", rating, text[:500], lang, created
                ))
            print(f"  Reddit r/{subreddit}: {len(posts)} posts")
            time.sleep(random.uniform(2, 3))
        except Exception as e:
            print(f"  Reddit r/{subreddit} erro: {e}")
    return results


# ─────────────────────────────────────────────
# 5. DECATHLON.COM — Reviews de produtos
# ─────────────────────────────────────────────
def fetch_decathlon_products(pages: int = 3) -> list[dict]:
    """Scraping de reviews de produtos no site Decathlon Brasil."""
    results = []
    categories = [
        ("running", "tenis-de-corrida"),
        ("cycling", "bicicleta"),
        ("fitness", "academia-e-fitness"),
        ("hiking", "caminhada-e-trekking"),
    ]

    for sport, category in categories:
        url = f"https://www.decathlon.com.br/{category}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Busca JSON-LD de produtos
            scripts = soup.find_all("script", {"type": "application/ld+json"})
            for script in scripts:
                try:
                    data = json.loads(script.string or "{}")
                    if data.get("@type") == "ItemList":
                        for item in data.get("itemListElement", []):
                            product = item.get("item", {})
                            for review in product.get("review", []):
                                text = review.get("reviewBody", "")
                                if len(text) < 10:
                                    continue
                                rating = review.get("reviewRating", {}).get("ratingValue", 3)
                                date = review.get("datePublished", datetime.now().isoformat())
                                rid = f"dc_{abs(hash(text[:50])) % 999999}"
                                results.append(normalize_review(
                                    rid, "decathlon_site",
                                    f"site_{sport}", f"Decathlon.com.br ({sport})",
                                    "Brasil", float(rating), text, "pt", date
                                ))
                except Exception:
                    continue
            print(f"  Decathlon.com.br {sport}: reviews coletadas")
            time.sleep(random.uniform(2, 3))
        except Exception as e:
            print(f"  Decathlon.com.br {sport} erro: {e}")
    return results


# ─────────────────────────────────────────────
# MAIN — Coleta todas as fontes
# ─────────────────────────────────────────────
def collect_all(output_path: str = "data/reviews_all_sources.json") -> list[dict]:
    print("=== Multi Source Scraper — Decathlon Consumer Insights ===\n")

    all_reviews = []

    print("1. Google Play...")
    gp = fetch_google_play(count=100)
    all_reviews.extend(gp)
    print(f"   Total: {len(gp)}\n")

    print("2. App Store...")
    apps = fetch_app_store(count=50)
    all_reviews.extend(apps)
    print(f"   Total: {len(apps)}\n")

    print("3. Trustpilot...")
    tp = fetch_trustpilot(pages=5)
    all_reviews.extend(tp)
    print(f"   Total: {len(tp)}\n")

    print("4. Reddit...")
    rd = fetch_reddit(limit=100)
    all_reviews.extend(rd)
    print(f"   Total: {len(rd)}\n")

    print("5. Decathlon.com.br...")
    dc = fetch_decathlon_products(pages=3)
    all_reviews.extend(dc)
    print(f"   Total: {len(dc)}\n")

    # Remove duplicatas por review_id
    seen = set()
    unique = []
    for r in all_reviews:
        if r["review_id"] not in seen:
            seen.add(r["review_id"])
            unique.append(r)

    print(f"✅ Total coletado: {len(unique)} reviews únicas")
    print(f"   Fontes: Google Play, App Store, Trustpilot, Reddit, Decathlon.com")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)
    print(f"✅ Salvo em {output_path}")

    return unique


if __name__ == "__main__":
    collect_all()