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
from plotly.subplots import make_subplots

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Decathlon — Consumer Insights",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# THEME & STYLES
# ─────────────────────────────────────────────
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

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif;
    background-color: {COLORS['bg']};
    color: {COLORS['text']};
}}

/* Sidebar */
[data-testid="stSidebar"] {{
    background-color: {COLORS['card']};
    border-right: 1px solid {COLORS['border']};
}}
[data-testid="stSidebar"] * {{ color: {COLORS['text']} !important; }}

/* Cards */
.insight-card {{
    background: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 8px;
}}
.kpi-value {{
    font-size: 2rem;
    font-weight: 700;
    line-height: 1;
    margin: 4px 0;
}}
.kpi-label {{
    font-size: 0.75rem;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: {COLORS['muted']};
    margin-bottom: 4px;
}}
.kpi-delta {{
    font-size: 0.8rem;
    font-weight: 500;
    color: {COLORS['muted']};
    margin-top: 4px;
}}
.kpi-delta.good {{ color: {COLORS['positive']}; }}
.kpi-delta.bad  {{ color: {COLORS['negative']}; }}

/* Section headers */
.section-header {{
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: {COLORS['muted']};
    margin: 24px 0 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid {COLORS['border']};
}}

/* Insight badges */
.insight-badge {{
    display: inline-block;
    background: rgba(239,68,68,0.15);
    border: 1px solid rgba(239,68,68,0.3);
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 0.82rem;
    margin: 4px 0;
    width: 100%;
}}
.insight-badge.positive {{
    background: rgba(34,197,94,0.12);
    border-color: rgba(34,197,94,0.3);
}}

/* Hide Streamlit chrome */
#MainMenu, footer, header {{ visibility: hidden; }}
[data-testid="stToolbar"] {{ display: none; }}
.block-container {{ padding: 1.5rem 2rem; }}

/* Tabs */
[data-baseweb="tab-list"] {{
    background: {COLORS['card']};
    border-radius: 8px;
    padding: 4px;
    gap: 4px;
}}
[data-baseweb="tab"] {{
    border-radius: 6px !important;
    font-weight: 500 !important;
}}

/* Multiselect */
[data-baseweb="tag"] {{ background-color: {COLORS['primary']} !important; }}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data() -> pd.DataFrame:
    paths = [
        "data/reviews_real_bert.json",
        "data/reviews_real_analyzed.json",
        "data/reviews_analyzed.json",
    ]
    for path in paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                df = pd.DataFrame(json.load(f))
            # Normalize column names
            if "bert_label" in df.columns and "sentiment_label" not in df.columns:
                df["sentiment_label"] = df["bert_label"]
            if "bert_score" in df.columns and "sentiment_score" not in df.columns:
                df["sentiment_score"] = df["bert_score"]
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            return df
    return pd.DataFrame()


def sentiment_color(label: str) -> str:
    return COLORS.get(label, COLORS["muted"])


# ─────────────────────────────────────────────
# SIDEBAR — FILTERS
# ─────────────────────────────────────────────
def render_sidebar(df: pd.DataFrame) -> pd.DataFrame:
    with st.sidebar:
        st.markdown("### Decathlon Insights")
        muted = COLORS["muted"]
        st.markdown(f"<span style='color:{muted};font-size:0.78rem'>Consumer Satisfaction Analysis</span>", unsafe_allow_html=True)
        st.divider()

        st.markdown("**Filters**")

        # Source filter
        sources = sorted(df["source"].unique().tolist())
        selected_sources = st.multiselect("Data source", sources, default=sources)

        # Language filter
        languages = sorted(df["language"].unique().tolist())
        lang_labels = {"pt": "🇧🇷 Portuguese", "es": "🇪🇸 Spanish", "fr": "🇫🇷 French", "en": "🇬🇧 English"}
        selected_langs = st.multiselect(
            "Language",
            languages,
            default=languages,
            format_func=lambda x: lang_labels.get(x, x)
        )

        # Sentiment filter
        sentiments = ["positive", "neutral", "negative"]
        selected_sentiments = st.multiselect("Sentiment", sentiments, default=sentiments)

        # Rating range
        min_r, max_r = float(df["rating"].min()), float(df["rating"].max())
        rating_range = st.slider("Rating range", min_r, max_r, (min_r, max_r), step=0.5)

        st.divider()
        st.markdown(f"<span style='color:{COLORS['muted']};font-size:0.75rem'>Last updated: {pd.Timestamp.now().strftime('%b %d, %Y')}</span>", unsafe_allow_html=True)

        # Apply filters
        filtered = df[
            df["source"].isin(selected_sources) &
            df["language"].isin(selected_langs) &
            df["sentiment_label"].isin(selected_sentiments) &
            df["rating"].between(rating_range[0], rating_range[1])
        ]
        return filtered


# ─────────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────────
def render_kpis(df: pd.DataFrame, df_full: pd.DataFrame):
    total = len(df)
    avg_rating = df["rating"].mean()
    pct_positive = len(df[df["sentiment_label"] == "positive"]) / total * 100 if total else 0
    pct_negative = len(df[df["sentiment_label"] == "negative"]) / total * 100 if total else 0
    target_rating = 4.0

    rating_delta = avg_rating - target_rating
    delta_class = "good" if rating_delta >= 0 else "bad"
    delta_symbol = "↑" if rating_delta >= 0 else "↓"

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="insight-card">
            <div class="kpi-label">Total Reviews</div>
            <div class="kpi-value">{total:,}</div>
            <div class="kpi-delta">{len(df_full):,} in full dataset</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="insight-card">
            <div class="kpi-label">Average Rating</div>
            <div class="kpi-value">{avg_rating:.2f} <span style="font-size:1rem">/ 5</span></div>
            <div class="kpi-delta {delta_class}">{delta_symbol} {abs(rating_delta):.2f} vs target of {target_rating}</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="insight-card">
            <div class="kpi-label">Positive Sentiment</div>
            <div class="kpi-value" style="color:{COLORS['positive']}">{pct_positive:.1f}%</div>
            <div class="kpi-delta">{len(df[df['sentiment_label']=='positive']):,} reviews</div>
        </div>""", unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="insight-card">
            <div class="kpi-label">Negative Sentiment</div>
            <div class="kpi-value" style="color:{COLORS['negative']}">{pct_negative:.1f}%</div>
            <div class="kpi-delta">{len(df[df['sentiment_label']=='negative']):,} reviews need attention</div>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# AUTOMATED INSIGHTS
# ─────────────────────────────────────────────
def render_auto_insights(df: pd.DataFrame):
    st.markdown('<div class="section-header">Automated Insights</div>', unsafe_allow_html=True)

    insights = []

    # Worst category
    cat_rating = df.groupby("sport_category")["rating"].mean()
    worst_cat = cat_rating.idxmin()
    worst_val = cat_rating.min()
    if worst_val < 3.0:
        insights.append(("negative", f"⚠️  <b>{worst_cat.title()}</b> has the lowest avg rating ({worst_val:.2f}/5) — requires immediate product review"))

    # Best category
    best_cat = cat_rating.idxmax()
    best_val = cat_rating.max()
    insights.append(("positive", f"✓  <b>{best_cat.title()}</b> leads satisfaction with {best_val:.2f}/5 avg rating"))

    # Most negative city
    city_neg = df[df["sentiment_label"] == "negative"].groupby("store_city").size()
    if not city_neg.empty:
        top_neg_city = city_neg.idxmax()
        insights.append(("negative", f"⚠️  <b>{top_neg_city}</b> generates the most negative reviews ({city_neg.max()} reviews) — investigate regional issues"))

    # Language with worst sentiment
    lang_score = df.groupby("language")["sentiment_score"].mean()
    worst_lang = lang_score.idxmin()
    lang_labels = {"pt": "Portuguese", "es": "Spanish", "fr": "French", "en": "English"}
    insights.append(("negative", f"⚠️  <b>{lang_labels.get(worst_lang, worst_lang)}</b> speakers report the lowest satisfaction (score: {lang_score.min():.2f})"))

    cols = st.columns(2)
    for i, (kind, text) in enumerate(insights):
        with cols[i % 2]:
            st.markdown(f'<div class="insight-badge {kind}">{text}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────
def chart_rating_by_category(df: pd.DataFrame):
    data = df.groupby("sport_category").agg(
        avg_rating=("rating", "mean"),
        count=("rating", "count")
    ).reset_index().sort_values("avg_rating")

    data["color"] = data["avg_rating"].apply(
        lambda x: COLORS["negative"] if x < 2.5 else (COLORS["neutral"] if x < 3.5 else COLORS["positive"])
    )

    fig = go.Figure(go.Bar(
        x=data["avg_rating"],
        y=data["sport_category"],
        orientation="h",
        marker_color=data["color"],
        text=data["avg_rating"].round(2),
        textposition="outside",
        textfont=dict(color=COLORS["text"], size=11),
        customdata=data["count"],
        hovertemplate="<b>%{y}</b><br>Avg Rating: %{x:.2f}<br>Reviews: %{customdata}<extra></extra>",
    ))
    fig.add_vline(x=4.0, line_dash="dash", line_color=COLORS["muted"], opacity=0.5,
                  annotation_text="Target 4.0", annotation_font_color=COLORS["muted"])
    fig.update_layout(**PLOTLY_THEME, title="Categories with Lowest Customer Satisfaction",
                      xaxis_range=[0, 5.5], height=320)
    return fig


def chart_sentiment_distribution(df: pd.DataFrame):
    counts = df["sentiment_label"].value_counts().reset_index()
    counts.columns = ["label", "count"]
    color_map = {"positive": COLORS["positive"], "neutral": COLORS["neutral"], "negative": COLORS["negative"]}

    fig = go.Figure(go.Pie(
        labels=counts["label"],
        values=counts["count"],
        hole=0.65,
        marker_colors=[color_map.get(l, COLORS["muted"]) for l in counts["label"]],
        textinfo="label+percent",
        textfont=dict(color=COLORS["text"], size=12),
        hovertemplate="<b>%{label}</b><br>%{value} reviews (%{percent})<extra></extra>",
    ))
    total = len(df)
    fig.add_annotation(text=f"<b>{total}</b><br><span style='font-size:10px'>reviews</span>",
                       x=0.5, y=0.5, showarrow=False,
                       font=dict(size=16, color=COLORS["text"]))
    fig.update_layout(**PLOTLY_THEME, title="Overall Sentiment Distribution",
                      showlegend=True, height=320,
                      legend=dict(orientation="h", y=-0.1))
    return fig


def chart_sentiment_by_city(df: pd.DataFrame):
    city_data = df.groupby(["store_city", "sentiment_label"]).size().reset_index(name="count")
    totals = city_data.groupby("store_city")["count"].sum()
    city_data["pct"] = city_data.apply(lambda r: r["count"] / totals[r["store_city"]] * 100, axis=1)

    color_map = {"positive": COLORS["positive"], "neutral": COLORS["neutral"], "negative": COLORS["negative"]}

    fig = px.bar(
        city_data, x="store_city", y="pct", color="sentiment_label",
        color_discrete_map=color_map,
        barmode="stack",
        custom_data=["count"],
    )
    fig.update_traces(hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y:.1f}%<br>(%{customdata[0]} reviews)<extra></extra>")
    fig.update_layout(**PLOTLY_THEME, title="Sentiment Breakdown by Location",
                      xaxis_title="", yaxis_title="% of Reviews",
                      legend_title="", height=320,
                      legend=dict(orientation="h", y=1.12))
    return fig


def chart_rating_trend(df: pd.DataFrame):
    df_time = df.dropna(subset=["date"]).copy()
    if df_time.empty:
        return None
    df_time["month"] = df_time["date"].dt.to_period("M").astype(str)
    trend = df_time.groupby("month").agg(avg_rating=("rating", "mean"), count=("rating", "count")).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trend["month"], y=trend["avg_rating"],
        mode="lines+markers",
        line=dict(color=COLORS["primary"], width=2),
        marker=dict(size=6, color=COLORS["primary"]),
        fill="tozeroy",
        fillcolor=f"rgba(59,130,246,0.1)",
        name="Avg Rating",
        hovertemplate="<b>%{x}</b><br>Avg Rating: %{y:.2f}<extra></extra>",
    ))
    fig.add_hline(y=4.0, line_dash="dash", line_color=COLORS["muted"], opacity=0.5,
                  annotation_text="Target", annotation_font_color=COLORS["muted"])
    fig.update_layout(**PLOTLY_THEME, title="Rating Trend Over Time",
                      xaxis_title="", yaxis_title="Avg Rating",
                      yaxis_range=[0, 5.5], height=280)
    return fig


def chart_negative_by_category(df: pd.DataFrame):
    neg = df[df["sentiment_label"] == "negative"]
    if neg.empty:
        return None
    data = neg["sport_category"].value_counts().reset_index()
    data.columns = ["category", "count"]

    fig = go.Figure(go.Bar(
        x=data["count"], y=data["category"],
        orientation="h",
        marker_color=COLORS["negative"],
        marker_opacity=0.85,
        text=data["count"],
        textposition="outside",
        textfont=dict(color=COLORS["text"], size=11),
        hovertemplate="<b>%{y}</b><br>Negative reviews: %{x}<extra></extra>",
    ))
    fig.update_layout(**PLOTLY_THEME, title="Where Customers Are Most Unhappy",
                      height=280)
    return fig


# ─────────────────────────────────────────────
# REVIEW TABLE
# ─────────────────────────────────────────────
def render_review_table(df: pd.DataFrame):
    st.markdown('<div class="section-header">Review Explorer</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        sentiment_filter = st.selectbox("Filter by sentiment", ["All", "negative", "positive", "neutral"])
    with col2:
        sort_by = st.selectbox("Sort by", ["Most Recent", "Lowest Rating", "Highest Rating"])

    filtered = df.copy()
    if sentiment_filter != "All":
        filtered = filtered[filtered["sentiment_label"] == sentiment_filter]

    if sort_by == "Most Recent":
        filtered = filtered.sort_values("date", ascending=False)
    elif sort_by == "Lowest Rating":
        filtered = filtered.sort_values("rating")
    else:
        filtered = filtered.sort_values("rating", ascending=False)

    display = filtered[["store_city", "language", "rating", "sentiment_label", "text"]].head(20).copy()
    display.columns = ["Location", "Lang", "Rating", "Sentiment", "Review"]

    def color_sentiment(val):
        colors_map = {"positive": "#22c55e", "negative": "#ef4444", "neutral": "#f59e0b"}
        c = colors_map.get(val, "white")
        return f"color: {c}; font-weight: 600"

    styled = display.style.map(color_sentiment, subset=["Sentiment"])
    st.dataframe(styled, use_container_width=True, height=420)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    df_full = load_data()

    if df_full.empty:
        st.error("No data found. Run the data pipeline first.")
        return

    df = render_sidebar(df_full)

    # Header
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:16px; margin-bottom:8px;">
        <div>
            <h1 style="margin:0; font-size:1.6rem; font-weight:700; letter-spacing:-0.02em">
                Decathlon Consumer Insights
            </h1>
            <p style="margin:0; color:{COLORS['muted']}; font-size:0.85rem">
                Real-time customer satisfaction analysis · {len(df):,} reviews filtered
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # KPIs
    render_kpis(df, df_full)

    # Automated insights
    render_auto_insights(df)

    # Main charts
    st.markdown('<div class="section-header">Satisfaction Analysis</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(chart_rating_by_category(df), use_container_width=True)
    with col2:
        st.plotly_chart(chart_sentiment_distribution(df), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(chart_sentiment_by_city(df), use_container_width=True)
    with col2:
        fig_neg = chart_negative_by_category(df)
        if fig_neg:
            st.plotly_chart(fig_neg, use_container_width=True)

    # Trend
    trend_fig = chart_rating_trend(df)
    if trend_fig:
        st.markdown('<div class="section-header">Trends</div>', unsafe_allow_html=True)
        st.plotly_chart(trend_fig, use_container_width=True)

    # Review table
    render_review_table(df)

    # Footer
    st.markdown(f"""
    <div style="margin-top:48px; padding-top:16px; border-top:1px solid {COLORS['border']};
                display:flex; justify-content:space-between; align-items:center;">
        <span style="color:{COLORS['muted']};font-size:0.75rem">
            Decathlon Consumer Insights · Built by Luan Moura · Data Engineering Portfolio
        </span>
        <span style="color:{COLORS['muted']};font-size:0.75rem">
            Sources: Google Play · Synthetic Data
        </span>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()