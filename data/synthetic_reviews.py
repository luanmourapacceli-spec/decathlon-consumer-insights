import json
import random
from datetime import datetime, timedelta

# Templates de reviews reais em português e espanhol
REVIEWS = [
    ("O tênis de corrida é ótimo, mas o atendimento demorou muito.", 3, "running"),
    ("Bicicleta chegou com peça quebrada. Suporte demorou 10 dias.", 1, "cycling"),
    ("Excelente custo-benefício! A camiseta lavou bem e não desbotou.", 5, "fitness"),
    ("A mochila de trilha abriu na costura depois de 2 usos.", 2, "hiking"),
    ("Produto ótimo, entrega rápida e embalagem cuidadosa!", 5, "swimming"),
    ("El kayak es ligero y resistente. Faltan accesorios.", 4, "water_sports"),
    ("Shorts muy ajustados aunque era la talla correcta.", 2, "fitness"),
    ("La app de Decathlon se bloqueó al pagar. Perdí la oferta.", 1, "other"),
    ("Zapatillas de fútbol excelentes, amortiguación perfecta.", 5, "football"),
    ("El pantalón de yoga se rompió en la primera sesión.", 1, "yoga"),
    ("Ótima loja, funcionários muito prestativos e atenciosos.", 5, "other"),
    ("Produto de qualidade inferior ao esperado pelo preço.", 2, "fitness"),
    ("Entrega atrasou 15 dias sem nenhuma comunicação.", 1, "other"),
    ("Material da camiseta é excelente, super recomendo!", 5, "running"),
    ("El servicio al cliente es muy bueno, resolvieron rápido.", 5, "other"),
    # English reviews
    ("Running shoes are amazing, great cushioning and durability.", 5, "running"),
    ("Bicycle arrived damaged. Customer support took forever to reply.", 1, "cycling"),
    ("Best value for money! The training shirt held up perfectly.", 5, "fitness"),
    ("Hiking backpack strap broke after first use. Very disappointed.", 2, "hiking"),
    ("Fast delivery, great packaging. Swimming goggles fit perfectly.", 5, "swimming"),
    ("Yoga pants tore during first session. Poor quality material.", 1, "yoga"),
    ("Football boots are excellent, perfect grip on synthetic turf.", 5, "football"),
    ("App crashed during checkout. Lost my discount code.", 1, "other"),
    ("Staff were incredibly helpful and knowledgeable.", 5, "other"),
    ("Product quality is below expectations for the price.", 2, "fitness"),
    ("Delivery was 2 weeks late with no communication at all.", 1, "other"),
    ("Kayak is lightweight and sturdy. Missing some accessories though.", 4, "water_sports"),
    ("Size chart is completely wrong. Shorts were way too tight.", 2, "fitness"),
    ("Great store experience, will definitely come back!", 5, "other"),
    ("Cycling helmet has poor ventilation for hot weather.", 2, "cycling"),
]

CITIES = ["Lisboa", "Porto", "Madrid", "Barcelona", "Alicante", "Sevilla", "Valencia"]
LANGUAGES = ["pt", "pt", "es", "es", "en"]  # distribuição das 3 línguas


def generate_reviews(n: int = 200) -> list[dict]:
    reviews = []
    base_date = datetime.now()

    for i in range(n):
        text, rating, category = random.choice(REVIEWS)
        city = random.choice(CITIES)
        lang = random.choice(LANGUAGES)

        # Variação de data nos últimos 180 dias
        days_ago = random.randint(0, 180)
        review_date = base_date - timedelta(days=days_ago)

        # Pequena variação no rating
        jitter = random.uniform(-0.3, 0.3)
        rating_final = max(1.0, min(5.0, rating + jitter))

        reviews.append({
            "review_id": f"syn_{i:05d}",
            "source": "synthetic",
            "store_id": f"store_{city.lower()}",
            "store_name": f"Decathlon {city}",
            "store_city": city,
            "rating": round(rating_final, 1),
            "text": text,
            "language": lang,
            "date": review_date.isoformat(),
            "sport_category": category,
            "collected_at": datetime.now().isoformat(),
        })

    return reviews


def save_reviews(reviews: list[dict], path: str = "data/reviews_synthetic.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)
    print(f"✅ {len(reviews)} reviews salvas em {path}")


if __name__ == "__main__":
    reviews = generate_reviews(200)
    save_reviews(reviews)
    
    # Mostra um exemplo
    print("\n📊 Exemplo de review gerada:")
    print(json.dumps(reviews[0], ensure_ascii=False, indent=2))