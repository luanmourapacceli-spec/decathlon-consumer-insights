"""
Decathlon Consumer Insights — Sport Category Classifier
Classifica reviews em categorias de esporte usando NLP multilíngue
"""

import json
import pandas as pd
from transformers import pipeline


# ─────────────────────────────────────────────
# Categorias e descrições para zero-shot
# ─────────────────────────────────────────────
SPORT_CATEGORIES = {
    "running":      "running shoes, jogging, marathon, trail running, tênis de corrida",
    "cycling":      "bicycle, bike, cycling, mountain bike, bicicleta, ciclismo",
    "fitness":      "gym, workout, fitness, training, academia, musculação, leggings",
    "hiking":       "hiking, trekking, backpack, mountain, mochila, trilha, senderismo",
    "swimming":     "swimming, pool, goggles, swimwear, natação, piscina",
    "football":     "football, soccer, futsal, cleats, futebol, chuteira, fútbol",
    "yoga":         "yoga, pilates, meditation, flexibility, meditação",
    "water_sports": "kayak, surf, paddle, sailing, canoeing, água",
    "app_delivery": "app, delivery, entrega, pagamento, pedido, cashback, suporte, atendimento",
    "other":        "general sports, equipment, clothing, products, gear",
}

CANDIDATE_LABELS = list(SPORT_CATEGORIES.keys())
LABEL_DESCRIPTIONS = list(SPORT_CATEGORIES.values())


def classify_with_keywords(text: str) -> str:
    """Classificador rápido por palavras-chave — roda antes do modelo."""
    text_lower = text.lower()

    keywords = {
        "running":      ["corrida", "correr", "running", "maratona", "tênis", "zapatilla",
                         "jogging", "trail", "pace", "ritmo", "kilómetros", "km"],
        "cycling":      ["bicicleta", "bike", "ciclismo", "mtb", "cycling", "vélo",
                         "bici", "cadence", "pedalada", "velocipede"],
        "fitness":      ["academia", "musculação", "treino", "gym", "fitness", "legging",
                         "camiseta", "haltere", "supino", "agachamento", "muscu", "salle de sport"],
        "hiking":       ["mochila", "trilha", "trekking", "hiking", "montanha", "senderismo",
                         "randonnée", "escalada", "camping", "barraca", "rando"],
        "swimming":     ["natação", "piscina", "swimming", "óculos de natação", "natacion",
                         "nager", "piscine", "swimwear", "swim"],
        "football":     ["futebol", "futsal", "chuteira", "gol", "fútbol", "soccer",
                         "football", "ballon", "bola", "campo"],
        "yoga":         ["yoga", "pilates", "meditação", "meditation", "flexibilidade"],
        "water_sports": ["kayak", "surf", "paddle", "vela", "canoa", "windsurf", "kitesurf"],
        "app_delivery": ["app", "aplicativo", "entrega", "pedido", "cashback",
                         "pagamento", "suporte", "atendimento", "compra", "carrinho",
                         "prazo", "frete", "devolução", "reembolso", "nota fiscal",
                         "application", "livraison", "commande", "paiement",
                         "login", "connexion", "conectar", "senha", "cuenta",
                         "compte", "mot de passe", "password", "bug", "crash",
                         "lento", "trava", "freezing", "update", "atualização"],
    }

    # Palavras-chave emocionais para reviews sem categoria de esporte
    positive_emotions = [
        # Português
        "feliz", "contente", "satisfeito", "satisfeita", "ótimo", "ótima",
        "excelente", "adorei", "amei", "perfeito", "perfeita", "incrível",
        "recomendo", "parabéns", "top", "maravilhoso", "maravilhosa",
        "fantástico", "fantástica", "bom", "boa", "gostei",
        # Espanhol
        "genial", "encantado", "encantada", "maravilloso", "fantástico",
        "perfecto", "excelente", "increíble", "recomiendo", "feliz",
        # Francês
        "parfait", "excellent", "super", "bravo", "génial", "formidable",
        "enchanté", "ravi", "satisfait",
        # Inglês
        "happy", "love", "great", "excellent", "perfect", "amazing",
        "fantastic", "wonderful", "brilliant", "awesome", "recommend",
    ]

    negative_emotions = [
        # Português
        "decepção", "decepcionado", "decepcionada", "horrível", "péssimo",
        "péssima", "terrível", "raiva", "frustrado", "frustrada",
        "frustração", "lamentável", "vergonha", "ódio", "detestei",
        "odiei", "pior", "nunca mais", "absurdo", "inadmissível",
        # Espanhol
        "decepcionante", "pésimo", "pésima", "fatal", "vergonzoso",
        "horrible", "terrible", "odio", "nunca más", "desastre",
        # Francês
        "décevant", "nul", "catastrophe", "horrible", "déçu", "déçue",
        "frustrant", "inacceptable", "scandaleux", "honte",
        # Inglês
        "terrible", "horrible", "awful", "disappointed", "frustrating",
        "worst", "useless", "pathetic", "disgusting", "unacceptable",
        "never again", "waste", "disaster",
    ]

    # Passo 1 — classifica por esporte
    for category, words in keywords.items():
        if any(word in text_lower for word in words):
            return category

    # Passo 2 — se não achou esporte, classifica por emoção
    for word in positive_emotions:
        if word in text_lower:
            return "positive_experience"

    for word in negative_emotions:
        if word in text_lower:
            return "negative_experience"

    return None  # Não classificou — vai para o modelo

def classify_with_model(texts: list[str], classifier) -> list[str]:
    """Usa zero-shot classification para textos não classificados por keywords."""
    results = []
    for text in texts:
        try:
            result = classifier(
                text[:512],
                candidate_labels=CANDIDATE_LABELS,
                hypothesis_template="This review is about {}.",
            )
            results.append(result["labels"][0])
        except Exception:
            results.append("other")
    return results


def classify_reviews(df: pd.DataFrame, use_model: bool = True) -> pd.DataFrame:
    print(f"🏷️  Classificando {len(df)} reviews por categoria de esporte...")

    # Passo 1 — Keywords (rápido)
    df["sport_category"] = df["text"].apply(classify_with_keywords)

    classified = df["sport_category"].notna().sum()
    unclassified = df["sport_category"].isna().sum()
    print(f"   Keywords: {classified} classificadas | {unclassified} para o modelo")

    # Passo 2 — Modelo zero-shot para os não classificados
    if use_model and unclassified > 0:
        print("   Carregando modelo zero-shot...")
        classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
        )

        mask = df["sport_category"].isna()
        unclassified_texts = df.loc[mask, "text"].tolist()
        model_results = classify_with_model(unclassified_texts, classifier)
        df.loc[mask, "sport_category"] = model_results
        print(f"   Modelo: {unclassified} reviews classificadas")

    # Preenche qualquer restante
    df["sport_category"] = df["sport_category"].fillna("other")

    # Estatísticas
    print("\n📊 Distribuição por categoria:")
    for cat, count in df["sport_category"].value_counts().items():
        pct = round(count / len(df) * 100, 1)
        print(f"   {cat:<15} {count:>3} reviews ({pct}%)")

    return df


def run(input_path: str = "data/reviews_real.json",
        output_path: str = "data/reviews_real_classified.json",
        use_model: bool = False):
    """
    use_model=False: usa só keywords (rápido, bom para dev)
    use_model=True: usa BART zero-shot para os não classificados (mais preciso)
    """
    print("=== Sport Category Classifier ===\n")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    df = pd.DataFrame(data)
    df = classify_reviews(df, use_model=use_model)

    df.to_json(output_path, orient="records", force_ascii=False, indent=2)
    print(f"\n✅ Salvo em {output_path}")

    return df


if __name__ == "__main__":
    import sys
    use_model = "--model" in sys.argv
    input_path = "data/reviews_all_sources_analyzed.json"
    output_path = "data/reviews_all_sources_classified.json"
    df = run(input_path=input_path, output_path=output_path, use_model=use_model)