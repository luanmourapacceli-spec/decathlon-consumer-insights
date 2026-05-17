"""
Load reviews data into PostgreSQL
Decathlon Consumer Insights — Data Engineering Portfolio
"""

import json
import os
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd

DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "decathlon_insights",
    "user":     "postgres",
    "password": "postgres",
}

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS reviews (
    review_id        TEXT PRIMARY KEY,
    source           TEXT,
    store_id         TEXT,
    store_name       TEXT,
    store_city       TEXT,
    rating           NUMERIC(3,1),
    review_text      TEXT,
    language         TEXT,
    review_date      TIMESTAMPTZ,
    sport_category   TEXT,
    sentiment_label  TEXT,
    sentiment_score  NUMERIC(5,3),
    collected_at     TIMESTAMPTZ,
    ingested_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reviews_city       ON reviews (store_city);
CREATE INDEX IF NOT EXISTS idx_reviews_sport      ON reviews (sport_category);
CREATE INDEX IF NOT EXISTS idx_reviews_sentiment  ON reviews (sentiment_label);
CREATE INDEX IF NOT EXISTS idx_reviews_rating     ON reviews (rating);
CREATE INDEX IF NOT EXISTS idx_reviews_date       ON reviews (review_date);
"""

def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def load_reviews(path: str) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)

    # Normalize sentiment columns
    if "bert_label" in df.columns and "sentiment_label" not in df.columns:
        df["sentiment_label"] = df["bert_label"]
    if "bert_score" in df.columns and "sentiment_score" not in df.columns:
        df["sentiment_score"] = df["bert_score"]

    # Fill missing columns
    for col in ["sentiment_label", "sentiment_score"]:
        if col not in df.columns:
            df[col] = None

    return df


def insert_reviews(conn, df: pd.DataFrame) -> int:
    rows = []
    for _, r in df.iterrows():
        rows.append((
            r.get("review_id"),
            r.get("source"),
            r.get("store_id"),
            r.get("store_name"),
            r.get("store_city"),
            r.get("rating"),
            r.get("text"),
            r.get("language"),
            r.get("date"),
            r.get("sport_category"),
            r.get("sentiment_label"),
            r.get("sentiment_score"),
            r.get("collected_at"),
        ))

    sql = """
        INSERT INTO reviews
            (review_id, source, store_id, store_name, store_city,
             rating, review_text, language, review_date, sport_category,
             sentiment_label, sentiment_score, collected_at)
        VALUES %s
        ON CONFLICT (review_id) DO UPDATE SET
            sentiment_label = EXCLUDED.sentiment_label,
            sentiment_score = EXCLUDED.sentiment_score,
            ingested_at     = NOW()
    """

    with conn.cursor() as cur:
        execute_values(cur, sql, rows)
    conn.commit()
    return len(rows)


def run_queries(conn):
    """Roda queries analíticas para verificar os dados."""
    queries = [
        ("Total de reviews", "SELECT COUNT(*) FROM reviews"),
        ("Rating médio", "SELECT ROUND(AVG(rating)::numeric, 2) FROM reviews"),
        ("Por sentimento", "SELECT sentiment_label, COUNT(*) FROM reviews GROUP BY sentiment_label ORDER BY COUNT(*) DESC"),
        ("Por cidade", "SELECT store_city, ROUND(AVG(rating)::numeric, 2) as avg_rating, COUNT(*) as total FROM reviews GROUP BY store_city ORDER BY avg_rating"),
    ]

    print("\n📊 Queries analíticas no PostgreSQL:")
    print("="*50)
    for title, query in queries:
        with conn.cursor() as cur:
            cur.execute(query)
            result = cur.fetchall()
            print(f"\n{title}:")
            for row in result:
                print(f"  {row}")


def export_csv_for_powerbi(df: pd.DataFrame):
    """Exporta CSV otimizado para Power BI."""
    path = "data/reviews_powerbi.csv"
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"\n✅ CSV para Power BI exportado: {path}")
    print("   → No Power BI: Obter Dados → Texto/CSV → selecione o arquivo")
    print("   → Ou conecte direto ao PostgreSQL: localhost:5432 / decathlon_insights")


if __name__ == "__main__":
    print("=== Carregando dados no PostgreSQL ===\n")

    # Carrega o melhor arquivo disponível
    paths = [
        "data/reviews_real_bert.json",
        "data/reviews_real_analyzed.json",
        "data/reviews_analyzed.json",
    ]

    df = None
    for path in paths:
        if os.path.exists(path):
            df = load_reviews(path)
            print(f"✅ Arquivo carregado: {path} ({len(df)} reviews)")
            break

    if df is None:
        print("❌ Nenhum arquivo de dados encontrado!")
        exit(1)

    # Conecta ao PostgreSQL
    try:
        conn = get_connection()
        print("✅ Conectado ao PostgreSQL!")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        exit(1)

    # Cria tabela
    with conn.cursor() as cur:
        cur.execute(CREATE_TABLE_SQL)
    conn.commit()
    print("✅ Tabela criada/verificada!")

    # Insere dados
    inserted = insert_reviews(conn, df)
    print(f"✅ {inserted} reviews inseridas no PostgreSQL!")

    # Roda queries analíticas
    run_queries(conn)

    # Exporta CSV para Power BI
    export_csv_for_powerbi(df)

    conn.close()
    print("\n=== Concluído! ===")
    print("\nPower BI — Conexão direta ao PostgreSQL:")
    print("  Host: localhost")
    print("  Porta: 5432")
    print("  Banco: decathlon_insights")
    print("  Usuário: postgres")
    print("  Senha: postgres")