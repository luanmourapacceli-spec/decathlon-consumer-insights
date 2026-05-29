"""
Decathlon Consumer Insights — Production Dashboard
Data Engineering Portfolio | Luan Moura
"""

import json
import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Decathlon — Consumer Insights",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLORS = {
    "positive": "#22c55e",
    "neutral":  "#f59e0b",
    "negative": "#ef4444",
    "primary":  "#3b82f6",
    "bg":       "#0f172a",
    "card":     "#1e293b",
    "border":   "#334155",
    "text":     "#f1f5f9",
    "muted":    "#94a3b8",
}

PLOTLY_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color=COLORS["text"], size=12),
    margin=dict(l=12, r=12, t=36, b=12),
    xaxis=dict(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
    yaxis=dict(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; background-color: #0f172a; color: #f1f5f9; }
[data-testid="stSidebar"] { background-color: #1e293b; border-right: 1px solid #334155; }
[data-testid="stSidebar"] * { color: #f1f5f9 !important; }
[data-testid="stSidebarCollapseButton"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
.insight-card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px 24px; margin-bottom: 8px; }
.kpi-value { font-size: 2rem; font-weight: 700; line-height: 1; margin: 4px 0; }
.kpi-label { font-size: 0.75rem; font-weight: 500; letter-spacing: 0.08em; text-transform: uppercase; color: #94a3b8; margin-bottom: 4px; }
.kpi-delta { font-size: 0.8rem; font-weight: 500; color: #94a3b8; margin-top: 4px; }
.kpi-delta.good { color: #22c55e; }
.kpi-delta.bad { color: #ef4444; }
.section-header { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: #94a3b8; margin: 24px 0 12px; padding-bottom: 8px; border-bottom: 1px solid #334155; }
.insight-badge { display: inline-block; background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.3); border-radius: 6px; padding: 8px 12px; font-size: 0.82rem; margin: 4px 0; width: 100%; }
.insight-badge.positive { background: rgba(34,197,94,0.12); border-color: rgba(34,197,94,0.3); }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }
.block-container { padding: 1.5rem 2rem; }
[data-baseweb="tag"] { background-color: #3b82f6 !important; }

/* Botão hamburguer */
.hamburger-btn {
    position: fixed;
    top: 12px;
    left: 12px;
    z-index: 999999;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 10px;
    cursor: pointer;
    font-size: 1.2rem;
    color: #f1f5f9;
    line-height: 1;
}
.hamburger-btn:hover {
    background: #334155;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE — controla sidebar
# ─────────────────────────────────────────────
if "show_sidebar" not in st.session_state:
    st.session_state.show_sidebar = True


@st.cache_data(ttl=300)
def load_data() -> pd.DataFrame:
    paths = [
        "data/reviews_all_sources_classified_bert.json",
        "data/reviews_all_sources_classified.json",
        "data/reviews_all_sources_analyzed.json",
        "data/reviews_real_analyzed.json",
        "data/reviews_real_bert.json",
        "data/reviews_analyzed.json",
    ]
    for path in paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                df = pd.DataFrame(json.load(f))
            # Sempre usa BERT quando disponível — mais preciso que TextBlob
            if "bert_label" in df.columns:
                df["sentiment_label"] = df["bert_label"]
            if "bert_score" in df.columns:
                df["sentiment_score"] = df["bert_score"]
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            return df
    return pd.DataFrame()


def render_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Painel de filtros inline — aparece abaixo do header."""
    with st.container():
        st.markdown('<div style="background:#1e293b;border:1px solid #334155;border-radius:12px;padding:16px;margin-bottom:16px;">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            sources = sorted(df["source"].unique().tolist())
            selected_sources = st.multiselect("Data source", sources, default=sources, key="src")

        with col2:
            languages = sorted(df["language"].unique().tolist())
            lang_labels = {"pt": "🇧🇷 Portuguese", "es": "🇪🇸 Spanish", "fr": "🇫🇷 French", "en": "🇬🇧 English"}
            selected_langs = st.multiselect("Language", languages, default=languages,
                                            format_func=lambda x: lang_labels.get(x, x), key="lang")

        with col3:
            sentiments = ["positive", "neutral", "negative"]
            selected_sentiments = st.multiselect("Sentiment", sentiments, default=sentiments, key="sent")

        with col4:
            min_r = float(df["rating"].min())
            max_r = float(df["rating"].max())
            rating_range = st.slider("Rating range", min_r, max_r, (min_r, max_r), step=0.5, key="rating")

        st.markdown('</div>', unsafe_allow_html=True)

    return df[
        df["source"].isin(selected_sources) &
        df["language"].isin(selected_langs) &
        df["sentiment_label"].isin(selected_sentiments) &
        df["rating"].between(rating_range[0], rating_range[1])
    ]

def render_kpis(df: pd.DataFrame, df_full: pd.DataFrame):
    total = len(df)
    avg_rating = round(df["rating"].mean(), 2)
    pct_pos = round(len(df[df["sentiment_label"] == "positive"]) / total * 100, 1) if total else 0
    pct_neg = round(len(df[df["sentiment_label"] == "negative"]) / total * 100, 1) if total else 0
    target = 4.0
    delta = round(avg_rating - target, 2)
    delta_class = "good" if delta >= 0 else "bad"
    delta_sym = "↑" if delta >= 0 else "↓"
    pos_count = len(df[df["sentiment_label"] == "positive"])
    neg_count = len(df[df["sentiment_label"] == "negative"])

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="insight-card"><div class="kpi-label">Total Reviews</div><div class="kpi-value">{total:,}</div><div class="kpi-delta">{len(df_full):,} in full dataset</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="insight-card"><div class="kpi-label">Average Rating</div><div class="kpi-value">{avg_rating} <span style="font-size:1rem">/ 5</span></div><div class="kpi-delta {delta_class}">{delta_sym} {abs(delta)} vs target of {target}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="insight-card"><div class="kpi-label">Positive Sentiment</div><div class="kpi-value" style="color:#22c55e">{pct_pos}%</div><div class="kpi-delta">{pos_count:,} reviews</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="insight-card"><div class="kpi-label">Negative Sentiment</div><div class="kpi-value" style="color:#ef4444">{pct_neg}%</div><div class="kpi-delta">{neg_count:,} reviews need attention</div></div>', unsafe_allow_html=True)


def render_auto_insights(df: pd.DataFrame):
    st.markdown('<div class="section-header">Automated Insights</div>', unsafe_allow_html=True)
    insights = []

    cat_rating = df.groupby("sport_category")["rating"].mean()
    worst_cat = cat_rating.idxmin()
    worst_val = round(cat_rating.min(), 2)
    if worst_val < 3.0:
        insights.append(("negative", f"⚠️ <b>{worst_cat.title()}</b> has the lowest avg rating ({worst_val}/5) — requires immediate product review"))

    best_cat = cat_rating.idxmax()
    best_val = round(cat_rating.max(), 2)
    insights.append(("positive", f"✓ <b>{best_cat.title()}</b> leads satisfaction with {best_val}/5 avg rating"))

    city_neg = df[df["sentiment_label"] == "negative"].groupby("store_city").size()
    if not city_neg.empty:
        top_neg_city = city_neg.idxmax()
        insights.append(("negative", f"⚠️ <b>{top_neg_city}</b> generates the most negative reviews ({city_neg.max()} reviews) — investigate regional issues"))

    if "sentiment_score" in df.columns:
        lang_score = df.groupby("language")["sentiment_score"].mean()
        worst_lang = lang_score.idxmin()
        lang_map = {"pt": "Portuguese", "es": "Spanish", "fr": "French", "en": "English"}
        insights.append(("negative", f"⚠️ <b>{lang_map.get(worst_lang, worst_lang)}</b> speakers report the lowest satisfaction (score: {round(lang_score.min(), 2)})"))

    cols = st.columns(2)
    for i, (kind, text) in enumerate(insights):
        with cols[i % 2]:
            st.markdown(f'<div class="insight-badge {kind}">{text}</div>', unsafe_allow_html=True)


def chart_rating_by_category(df):
    data = df.groupby("sport_category").agg(avg_rating=("rating", "mean"), count=("rating", "count")).reset_index().sort_values("avg_rating")
    data["color"] = data["avg_rating"].apply(lambda x: "#ef4444" if x < 2.5 else ("#f59e0b" if x < 3.5 else "#22c55e"))
    fig = go.Figure(go.Bar(x=data["avg_rating"], y=data["sport_category"], orientation="h",
        marker_color=data["color"], text=data["avg_rating"].round(2), textposition="outside",
        textfont=dict(color=COLORS["text"], size=11), customdata=data["count"],
        hovertemplate="<b>%{y}</b><br>Avg Rating: %{x}<br>Reviews: %{customdata}<extra></extra>"))
    fig.add_vline(x=4.0, line_dash="dash", line_color=COLORS["muted"], opacity=0.5,
                  annotation_text="Target 4.0", annotation_font_color=COLORS["muted"])
    fig.update_layout(**PLOTLY_THEME, title="Categories with Lowest Customer Satisfaction", xaxis_range=[0, 5.5], height=320)
    return fig


def chart_sentiment_distribution(df):
    counts = df["sentiment_label"].value_counts().reset_index()
    counts.columns = ["label", "count"]
    color_map = {"positive": "#22c55e", "neutral": "#f59e0b", "negative": "#ef4444"}
    fig = go.Figure(go.Pie(labels=counts["label"], values=counts["count"], hole=0.65,
        marker_colors=[color_map.get(l, COLORS["muted"]) for l in counts["label"]],
        textinfo="label+percent", textfont=dict(color=COLORS["text"], size=12),
        hovertemplate="<b>%{label}</b><br>%{value} reviews (%{percent})<extra></extra>"))
    fig.add_annotation(text=f"<b>{len(df)}</b><br>reviews", x=0.5, y=0.5, showarrow=False,
                       font=dict(size=16, color=COLORS["text"]))
    fig.update_layout(**PLOTLY_THEME, title="Overall Sentiment Distribution", showlegend=True, height=320,
                      legend=dict(orientation="h", y=-0.1))
    return fig


def chart_sentiment_by_city(df):
    city_data = df.groupby(["store_city", "sentiment_label"]).size().reset_index(name="count")
    totals = city_data.groupby("store_city")["count"].sum()
    city_data["pct"] = city_data.apply(lambda r: r["count"] / totals[r["store_city"]] * 100, axis=1)
    color_map = {"positive": "#22c55e", "neutral": "#f59e0b", "negative": "#ef4444"}
    fig = px.bar(city_data, x="store_city", y="pct", color="sentiment_label",
                 color_discrete_map=color_map, barmode="stack", custom_data=["count"])
    fig.update_traces(hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y}%<br>(%{customdata[0]} reviews)<extra></extra>")
    fig.update_layout(**PLOTLY_THEME, title="Sentiment Breakdown by Location",
                      xaxis_title="", yaxis_title="% of Reviews", legend_title="", height=320,
                      legend=dict(orientation="h", y=1.12))
    return fig


def chart_negative_by_category(df):
    neg = df[df["sentiment_label"] == "negative"]
    if neg.empty:
        return None
    data = neg["sport_category"].value_counts().reset_index()
    data.columns = ["category", "count"]
    fig = go.Figure(go.Bar(x=data["count"], y=data["category"], orientation="h",
        marker_color="#ef4444", marker_opacity=0.85, text=data["count"], textposition="outside",
        textfont=dict(color=COLORS["text"], size=11),
        hovertemplate="<b>%{y}</b><br>Negative reviews: %{x}<extra></extra>"))
    fig.update_layout(**PLOTLY_THEME, title="Where Customers Are Most Unhappy", height=280)
    return fig


def chart_rating_trend(df):
    df_time = df.dropna(subset=["date"]).copy()
    if df_time.empty:
        return None
    df_time["month"] = df_time["date"].dt.to_period("M").astype(str)
    trend = df_time.groupby("month").agg(avg_rating=("rating", "mean"), count=("rating", "count")).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend["month"], y=trend["avg_rating"], mode="lines+markers",
        line=dict(color=COLORS["primary"], width=2), marker=dict(size=6, color=COLORS["primary"]),
        fill="tozeroy", fillcolor="rgba(59,130,246,0.1)", name="Avg Rating",
        hovertemplate="<b>%{x}</b><br>Avg Rating: %{y}<extra></extra>"))
    fig.add_hline(y=4.0, line_dash="dash", line_color=COLORS["muted"], opacity=0.5,
                  annotation_text="Target", annotation_font_color=COLORS["muted"])
    fig.update_layout(**PLOTLY_THEME, title="Rating Trend Over Time",
                      xaxis_title="", yaxis_title="Avg Rating", yaxis_range=[0, 5.5], height=280)
    return fig


def render_review_table(df):
    st.markdown('<div class="section-header">Review Explorer</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        sentiment_filter = st.selectbox("Filter by sentiment", ["All", "negative", "positive", "neutral"])
    with col2:
        sort_by = st.selectbox("Sort by", ["Most Recent", "Lowest Rating", "Highest Rating"])
    with col3:
        per_page = st.selectbox("Rows per page", [10, 20, 50, 100], index=1)

    filtered = df.copy()
    if sentiment_filter != "All":
        filtered = filtered[filtered["sentiment_label"] == sentiment_filter]
    if sort_by == "Most Recent":
        filtered = filtered.sort_values("date", ascending=False)
    elif sort_by == "Lowest Rating":
        filtered = filtered.sort_values("rating")
    else:
        filtered = filtered.sort_values("rating", ascending=False)

    total = len(filtered)
    total_pages = max(1, (total + per_page - 1) // per_page)

    col_info, col_nav = st.columns([3, 1])
    with col_info:
        st.markdown(f"<span style='color:#94a3b8;font-size:0.8rem'>{total:,} reviews found</span>", unsafe_allow_html=True)
    with col_nav:
        page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)

    start = (page - 1) * per_page
    end = start + per_page
    page_df = filtered.iloc[start:end]

    display = page_df[["store_city", "language", "rating", "sentiment_label", "text"]].copy()
    display.columns = ["Location", "Lang", "Rating", "Sentiment", "Review"]

    def color_sentiment(val):
        c = {"positive": "#22c55e", "negative": "#ef4444", "neutral": "#f59e0b"}.get(val, "white")
        return f"color: {c}; font-weight: 600"

    st.dataframe(display.style.map(color_sentiment, subset=["Sentiment"]), use_container_width=True, height=420)
    st.markdown(f"<span style='color:#94a3b8;font-size:0.75rem'>Page {page} of {total_pages} | Showing {start+1}-{min(end, total)} of {total:,} reviews</span>", unsafe_allow_html=True)
def main():
    df_full = load_data()
    if df_full.empty:
        st.error("No data found. Run the data pipeline first.")
        return

    # Header com botão hamburguer
    st.markdown(f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;"><h1 style="margin:0;font-size:1.6rem;font-weight:700;letter-spacing:-0.02em">Decathlon Consumer Insights</h1><span style="color:#94a3b8;font-size:0.85rem">| {len(df_full):,} reviews</span></div>', unsafe_allow_html=True)

    # Layout com sidebar manual
    if st.session_state.show_sidebar:
        col_side, col_main = st.columns([1.5, 8.5])
    else:
        col_side = None
        col_main = st.columns([1])[0]

    # Sidebar manual
    if st.session_state.show_sidebar and col_side:
        with col_side:
            st.markdown('<div style="background:#1e293b;border:1px solid #334155;border-radius:12px;padding:16px;position:sticky;top:0;">', unsafe_allow_html=True)
            
            if st.button("☰ Hide", key="hamburger"):
                st.session_state.show_sidebar = False
                st.rerun()

            st.markdown("### Filters")
            sources = sorted(df_full["source"].unique().tolist())
            selected_sources = st.multiselect("Data source", sources, default=sources, key="src")

            languages = sorted(df_full["language"].unique().tolist())
            lang_labels = {"pt": "🇧🇷 PT", "es": "🇪🇸 ES", "fr": "🇫🇷 FR", "en": "🇬🇧 EN"}
            selected_langs = st.multiselect("Language", languages, default=languages,
                                            format_func=lambda x: lang_labels.get(x, x), key="lang")

            sentiments = ["positive", "neutral", "negative"]
            selected_sentiments = st.multiselect("Sentiment", sentiments, default=sentiments, key="sent")

            min_r = float(df_full["rating"].min())
            max_r = float(df_full["rating"].max())
            rating_range = st.slider("Rating", min_r, max_r, (min_r, max_r), step=0.5, key="rating")

            st.markdown('</div>', unsafe_allow_html=True)

            df = df_full[
                df_full["source"].isin(selected_sources) &
                df_full["language"].isin(selected_langs) &
                df_full["sentiment_label"].isin(selected_sentiments) &
                df_full["rating"].between(rating_range[0], rating_range[1])
            ]
    else:
        df = df_full

    # Conteúdo principal
    with col_main:
        if not st.session_state.show_sidebar:
            if st.button("☰ Filters", key="hamburger"):
                st.session_state.show_sidebar = True
                st.rerun()

        render_kpis(df, df_full)
        render_auto_insights(df)

        st.markdown('<div class="section-header">Satisfaction Analysis</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(chart_rating_by_category(df), use_container_width=True)
        with c2:
            st.plotly_chart(chart_sentiment_distribution(df), use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(chart_sentiment_by_city(df), use_container_width=True)
        with c2:
            fig_neg = chart_negative_by_category(df)
            if fig_neg:
                st.plotly_chart(fig_neg, use_container_width=True)

        trend_fig = chart_rating_trend(df)
        if trend_fig:
            st.markdown('<div class="section-header">Trends</div>', unsafe_allow_html=True)
            st.plotly_chart(trend_fig, use_container_width=True)

        render_review_table(df)

        border_color = COLORS["border"]
        muted_color = COLORS["muted"]
        footer = f'<div style="margin-top:48px;padding-top:16px;border-top:1px solid {border_color};display:flex;justify-content:space-between;"><span style="color:{muted_color};font-size:0.75rem">Decathlon Consumer Insights | Built by Luan Moura</span><span style="color:{muted_color};font-size:0.75rem">Sources: App Store | Reddit</span></div>'
        st.markdown(footer, unsafe_allow_html=True)


if __name__ == "__main__":
    main()