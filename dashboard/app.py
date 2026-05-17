import json
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(
    page_title="Decathlon Consumer Insights",
    page_icon="🏃",
    layout="wide"
)

# Carrega os dados
@st.cache_data
def load_data():
    with open("data/reviews_analyzed.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)

df = load_data()

# Header
st.title("🏃 Decathlon Consumer Insights")
st.markdown("**Análise de satisfação e insatisfação dos consumidores**")
st.divider()

# KPIs no topo
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total de Reviews", len(df))
with col2:
    avg_rating = round(df["rating"].mean(), 2)
    st.metric("Rating Médio", f"⭐ {avg_rating}")
with col3:
    pct_positive = round(len(df[df["sentiment_label"] == "positive"]) / len(df) * 100, 1)
    st.metric("Reviews Positivas", f"{pct_positive}%")
with col4:
    pct_negative = round(len(df[df["sentiment_label"] == "negative"]) / len(df) * 100, 1)
    st.metric("Reviews Negativas", f"{pct_negative}%")

st.divider()

# Gráficos — linha 1
col1, col2 = st.columns(2)

with col1:
    st.subheader("⭐ Rating médio por categoria")
    avg_by_sport = df.groupby("sport_category")["rating"].mean().reset_index()
    avg_by_sport = avg_by_sport.sort_values("rating")
    fig1 = px.bar(
        avg_by_sport,
        x="rating",
        y="sport_category",
        orientation="h",
        color="rating",
        color_continuous_scale=["red", "yellow", "green"],
        range_color=[1, 5],
    )
    fig1.update_layout(showlegend=False, height=350)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("🎯 Distribuição de sentimentos")
    sentiment_counts = df["sentiment_label"].value_counts().reset_index()
    sentiment_counts.columns = ["sentiment", "count"]
    fig2 = px.pie(
        sentiment_counts,
        values="count",
        names="sentiment",
        color="sentiment",
        color_discrete_map={
            "positive": "#2ecc71",
            "neutral": "#f39c12",
            "negative": "#e74c3c"
        }
    )
    fig2.update_layout(height=350)
    st.plotly_chart(fig2, use_container_width=True)

# Gráficos — linha 2
col1, col2 = st.columns(2)

with col1:
    st.subheader("⚠️ Reviews negativas por categoria")
    negative_df = df[df["sentiment_label"] == "negative"]
    neg_by_sport = negative_df["sport_category"].value_counts().reset_index()
    neg_by_sport.columns = ["category", "count"]
    fig3 = px.bar(
        neg_by_sport,
        x="category",
        y="count",
        color="count",
        color_continuous_scale=["yellow", "red"],
    )
    fig3.update_layout(showlegend=False, height=350)
    st.plotly_chart(fig3, use_container_width=True)

with col2:
    st.subheader("🌍 Reviews por cidade")
    city_counts = df["store_city"].value_counts().reset_index()
    city_counts.columns = ["city", "count"]
    fig4 = px.bar(
        city_counts,
        x="city",
        y="count",
        color="count",
        color_continuous_scale=["lightblue", "darkblue"],
    )
    fig4.update_layout(showlegend=False, height=350)
    st.plotly_chart(fig4, use_container_width=True)

st.divider()

# Tabela de reviews negativas
st.subheader("💬 Reviews mais negativas")
worst = df.nsmallest(10, "sentiment_score")[
    ["store_city", "sport_category", "rating", "sentiment_score", "text"]
]
worst.columns = ["Cidade", "Categoria", "Rating", "Score Sentimento", "Review"]
st.dataframe(worst, use_container_width=True)

# Filtro por categoria
st.divider()
st.subheader("🔍 Explorar por categoria")
category = st.selectbox("Seleciona uma categoria:", df["sport_category"].unique())
filtered = df[df["sport_category"] == category][
    ["store_city", "rating", "sentiment_label", "text"]
]
filtered.columns = ["Cidade", "Rating", "Sentimento", "Review"]
st.dataframe(filtered, use_container_width=True)