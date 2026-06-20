import streamlit as st
import numpy as np

from .tokens import get_tokens
from .icons import icon, sentiment_icon


def rail_header(title: str, ico: str | None = None) -> None:
    ico_html = f"{ico}&nbsp;" if ico else ""
    st.markdown(f"""
<div class="rail-header">
  <span class="rail-bar"></span>
  <span class="rail-title">{ico_html}{title}</span>
  <span class="rail-line"></span>
</div>
""", unsafe_allow_html=True)


def chart_layout(height: int = 380) -> dict:
    T = get_tokens()
    return dict(
        template=T["plotly_theme"],
        height=height,
        paper_bgcolor=T["chart_paper"],
        plot_bgcolor=T["chart_paper"],
        margin=dict(l=0, r=0, t=12, b=45),
        xaxis=dict(
            gridcolor=T["chart_grid"],
            linecolor=T["border"],
            tickfont=dict(family="JetBrains Mono",
                          size=10, color=T["text_muted"]),
        ),
        yaxis=dict(
            gridcolor=T["chart_grid"],
            linecolor=T["border"],
            tickfont=dict(family="JetBrains Mono",
                          size=10, color=T["text_muted"]),
        ),
        legend=dict(
            orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5,
            font=dict(family="Space Grotesk", size=11,
                      color=T["text_secondary"]),
            bgcolor="rgba(0,0,0,0)",
        ),
        font=dict(family="Space Grotesk", color=T["text_secondary"]),
        hoverlabel=dict(
            bgcolor=T["bg_card"],
            bordercolor=T["border"],
            font=dict(family="JetBrains Mono", size=11,
                      color=T["text_primary"]),
        ),
    )


def pill_html(label: str) -> str:
    l = label.lower()
    cls = "pill-pos" if "positive" in l else (
        "pill-neg" if "negative" in l else "pill-neu")
    ico = sentiment_icon(label)
    return f'<span class="sentiment-pill {cls}">{ico}&nbsp;{label}</span>'


def news_card_html(article: dict) -> str:
    T = get_tokens()
    label = article.get("sentiment_label", "Neutral")
    l = label.lower()
    cls = "pos" if "positive" in l else ("neg" if "negative" in l else "neu")
    url = article.get("url", "")
    link = (
        f'<a href="{url}" target="_blank" rel="noopener" '
        f'style="display:inline-flex;align-items:center;gap:3px;font-size:0.73rem;'
        f'color:{T["accent_blue"]};text-decoration:none;font-family:Space Grotesk,sans-serif;'
        f'font-weight:500;margin-top:0.4rem;">'
        f'{icon("external-link", 11, T["accent_blue"])} Read article</a>'
        if url else ""
    )
    score = article.get("sentiment_score", 0)
    return f"""
<div class="news-card {cls}">
  <div class="news-title">{article.get("title","")}</div>
  <div class="news-meta">
    {article.get("publisher","")}
    <span class="sep">·</span>
    {article.get("published_at","")}
    <span class="sep">·</span>
    {pill_html(label)}
    <span style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:{T["text_muted"]};">{score:+.3f}</span>
  </div>
  {link}
</div>
"""


def signal_badge_html(signal: str) -> str:
    T = get_tokens()
    sig = signal.lower()
    if "buy" in sig:
        bg, bd, col, ico = T["badge_buy_bg"], T["badge_buy_bd"], T["accent_green"], icon(
            "trending-up", 22, T["accent_green"])
    elif "sell" in sig:
        bg, bd, col, ico = T["badge_sell_bg"], T["badge_sell_bd"], T["accent_red"], icon(
            "trending-down", 22, T["accent_red"])
    else:
        bg, bd, col, ico = T["badge_hold_bg"], T["badge_hold_bd"], T["accent_amber"], icon(
            "minus", 22, T["accent_amber"])
    return f"""
<div class="signal-wrap">
  <div class="signal-badge" style="background:{bg};border-color:{bd};color:{col};">
    {ico}&nbsp;{signal}
  </div>
</div>
"""


def sparkline_svg(prices: np.ndarray, width: int = 120, height: int = 38) -> str:
    T = get_tokens()
    if len(prices) < 2:
        return ""
    mn, mx = float(prices.min()), float(prices.max())
    rng = mx - mn if mx != mn else 1.0
    ys = [(1 - (p - mn) / rng) * (height - 6) + 3 for p in prices]
    xs = [i * width / (len(prices) - 1) for i in range(len(prices))]
    color = T["accent_green"] if prices[-1] >= prices[0] else T["accent_red"]
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'style="display:block;">'
        f'<polyline points="{pts}" fill="none" stroke="{color}" '
        f'stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"/></svg>'
    )


def render_nav(show_back: bool = False, active_page: str = "watchlist") -> None:
    T = get_tokens()

    brand_svg = (
        '<svg width="32" height="32" viewBox="0 0 24 24" fill="none"'
        ' stroke="' + T["accent_blue"] + '" stroke-width="2.2"'
        ' stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="3 17 8 10 13 14 21 5"/>'
        '<circle cx="21" cy="5" r="2.5" fill="' +
        T["accent_green"] + '" stroke="none"/>'
        '</svg>'
    )

    back_html = ""
    if show_back:
        back_html = (
            '<div style="margin-bottom:0.28rem;">'
            '<span style="font-size:0.7rem;color:' + T["text_muted"] + ';'
            'font-family:Space Grotesk,sans-serif;letter-spacing:0.04em;">'
            '← Watchlist'
            '</span></div>'
        )

    if back_html:
        st.markdown(back_html, unsafe_allow_html=True)

    # ── Row 1: Logo (left) + theme toggle (right) — real same row ──────────
    col_logo, col_theme = st.columns([8, 1])
    with col_logo:
        st.markdown(
            '<div class="topnav-brand" style="margin-top:0.3rem;">'
            '<div class="brand-mark">' + brand_svg + '</div>Foresight</div>',
            unsafe_allow_html=True,
        )
    with col_theme:
        is_dark = st.session_state.get("theme") == "dark"
        label = "☀️ Light" if is_dark else "🌙 Dark"
        if st.button(label, use_container_width=True, key="nav_theme_toggle", type="secondary"):
            st.session_state.theme = "light" if is_dark else "dark"
            st.rerun()

    st.markdown('<div style="border-bottom:1px solid ' + T["border"] + '; margin-bottom:2rem;"></div>', unsafe_allow_html=True)

    # ── Row 2: Market / Compare tabs ────────────────────────────────────────
    n1, n2 = st.columns([1, 1])
    with n1:
        if active_page == "watchlist":
            st.button("Market", disabled=True, use_container_width=True,
                      key="nav_market", type="secondary")
        else:
            if st.button("Market", use_container_width=True,
                         key="nav_market", type="secondary"):
                st.session_state.page = "watchlist"
                st.session_state.selected_ticker = None
                st.rerun()
    with n2:
        if active_page == "compare":
            st.button("Compare", disabled=True, use_container_width=True,
                      key="nav_compare", type="secondary")
        else:
            if st.button("Compare", use_container_width=True,
                         key="nav_compare", type="secondary"):
                st.session_state.page = "compare"
                st.rerun()