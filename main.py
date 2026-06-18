import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from ticker_strip import render_ticker_strip
from datetime import timedelta

from data_fetcher import fetch_stock_data, get_stock_info
from predictor import run_prediction
from news_analyzer import (
    get_news_sentiment,
    generate_recommendation,
    extract_market_drivers,
)
from comparator import compare_stocks
import cache_manager

# ── Watchlist ───────────────────────────────────────────────────────────────
WATCHLIST = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN", "TSLA",
    "TSM", "AMD", "BABA", "PDD", "JD", "BIDU",
    "SPY", "QQQ", "JPM", "BRK-B", "NFLX", "DIS", "ENPH",
]

# ── Page routing ────────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "watchlist"
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = None
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# ── Page config (must run before any other st call) ─────────────────────────
st.set_page_config(
    page_title="Foresight — Stock Intelligence",
    page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><polyline points='3 17 9 11 13 15 21 7' fill='none' stroke='%234C9BE8' stroke-width='2.5' stroke-linecap='round'/></svg>",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Design tokens ───────────────────────────────────────────────────────────
DARK = {
    "bg_base":        "#080C10",
    "bg_surface":     "#0F1923",
    "bg_card":        "#111D2B",
    "bg_card_hover":  "#162234",
    "bg_input":       "#0D1824",
    "border":         "#1E2D3D",
    "border_accent":  "#4C9BE8",
    "accent_green":   "#2ECC71",
    "accent_blue":    "#4C9BE8",
    "accent_red":     "#FF4D6D",
    "accent_amber":   "#F5A623",
    "text_primary":   "#E8F1F9",
    "text_secondary": "#7A92A8",
    "text_muted":     "#3D5166",
    "chart_grid":     "#111D2B",
    "chart_paper":    "rgba(0,0,0,0)",
    "plotly_theme":   "plotly_dark",
    "glow_blue":      "rgba(76,155,232,0.35)",
    "glow_green":     "rgba(46,204,113,0.3)",
    "shadow":         "0 4px 28px rgba(0,0,0,0.55)",
    "pos_pill_bg":    "rgba(46,204,113,0.10)",
    "neg_pill_bg":    "rgba(255,77,109,0.10)",
    "neu_pill_bg":    "rgba(122,146,168,0.10)",
    "scrollbar_track": "#0F1923",
    "scrollbar_thumb": "#1E2D3D",
    "badge_buy_bg":   "rgba(46,204,113,0.10)",
    "badge_buy_bd":   "rgba(46,204,113,0.30)",
    "badge_sell_bg":  "rgba(255,77,109,0.10)",
    "badge_sell_bd":  "rgba(255,77,109,0.30)",
    "badge_hold_bg":  "rgba(245,166,35,0.10)",
    "badge_hold_bd":  "rgba(245,166,35,0.30)",
    "wl_hover":       "#16202e",
    "wl_border":      "#1E2D3D",
    "disclaimer_bg":  "rgba(245,166,35,0.06)",
}
LIGHT = {
    "bg_base":        "#EEF2F7",
    "bg_surface":     "#F7F9FC",
    "bg_card":        "#FFFFFF",
    "bg_card_hover":  "#F0F5FB",
    "bg_input":       "#FFFFFF",
    "border":         "#D4DDE8",
    "border_accent":  "#1A72CC",
    "accent_green":   "#16A34A",
    "accent_blue":    "#1A72CC",
    "accent_red":     "#D93052",
    "accent_amber":   "#C07B00",
    "text_primary":   "#0A1929",
    "text_secondary": "#4A6280",
    "text_muted":     "#9EB3C8",
    "chart_grid":     "#E8EEF5",
    "chart_paper":    "rgba(0,0,0,0)",
    "plotly_theme":   "plotly_white",
    "glow_blue":      "rgba(26,114,204,0.18)",
    "glow_green":     "rgba(22,163,74,0.15)",
    "shadow":         "0 2px 16px rgba(0,40,90,0.08)",
    "pos_pill_bg":    "rgba(22,163,74,0.09)",
    "neg_pill_bg":    "rgba(217,48,82,0.09)",
    "neu_pill_bg":    "rgba(74,98,128,0.09)",
    "scrollbar_track": "#EEF2F7",
    "scrollbar_thumb": "#C8D5E3",
    "badge_buy_bg":   "rgba(22,163,74,0.09)",
    "badge_buy_bd":   "rgba(22,163,74,0.28)",
    "badge_sell_bg":  "rgba(217,48,82,0.09)",
    "badge_sell_bd":  "rgba(217,48,82,0.28)",
    "badge_hold_bg":  "rgba(192,123,0,0.09)",
    "badge_hold_bd":  "rgba(192,123,0,0.28)",
    "wl_hover":       "#F4F7FB",
    "wl_border":      "#D4DDE8",
    "disclaimer_bg":  "rgba(192,123,0,0.06)",
}

T = DARK if st.session_state.theme == "dark" else LIGHT
is_dark = st.session_state.theme == "dark"

# ── Inline SVG icons ────────────────────────────────────────────────────────


def icon(name: str, size: int = 15, color: str | None = None) -> str:
    c = color or T["text_secondary"]
    s = f'width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"'
    icons = {
        "trending-up":   f'<svg {s}><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
        "trending-down": f'<svg {s}><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/></svg>',
        "minus":         f'<svg {s}><line x1="5" y1="12" x2="19" y2="12"/></svg>',
        "sun":           f'<svg {s}><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',
        "moon":          f'<svg {s}><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>',
        "activity":      f'<svg {s}><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
        "brain":         f'<svg {s}><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.46 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.44-3.14Z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.46 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.44-3.14Z"/></svg>',
        "calendar":      f'<svg {s}><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
        "newspaper":     f'<svg {s}><path d="M4 3h16a1 1 0 0 1 1 1v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4a1 1 0 0 1 1-1z"/><line x1="8" y1="7" x2="16" y2="7"/><line x1="8" y1="11" x2="16" y2="11"/><line x1="8" y1="15" x2="12" y2="15"/></svg>',
        "external-link": f'<svg {s}><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>',
        "layers":        f'<svg {s}><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
        "chart-line":    f'<svg {s}><polyline points="3 17 9 11 13 15 21 7"/><polyline points="14 7 21 7 21 14"/></svg>',
        "alert":         f'<svg {s}><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        "info":          f'<svg {s}><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
        "check":         f'<svg {s}><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
        "search":        f'<svg {s}><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
        "arrow-left":    f'<svg {s}><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>',
        "candlestick":   f'<svg {s}><line x1="8" y1="2" x2="8" y2="22"/><rect x="5" y="7" width="6" height="8" rx="1"/><line x1="16" y1="2" x2="16" y2="22"/><rect x="13" y="11" width="6" height="6" rx="1"/></svg>',
    }
    return icons.get(name, icons["info"])


def sentiment_icon(label: str) -> str:
    if "positive" in label.lower():
        return icon("trending-up", 13, T["accent_green"])
    if "negative" in label.lower():
        return icon("trending-down", 13, T["accent_red"])
    return icon("minus", 13, T["text_secondary"])


# ── Global CSS ───────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}

html, body, [data-testid="stAppViewContainer"],
[data-testid="stMain"], .main {{
    background: {T["bg_base"]} !important;
    color: {T["text_primary"]} !important;
    font-family: 'Inter', system-ui, sans-serif !important;
}}
#MainMenu, footer, header {{ visibility: hidden; }}
[data-testid="stToolbar"], [data-testid="stDecoration"] {{ display: none; }}
[data-testid="stSidebar"] {{ display: none; }}
.block-container {{
    max-width: 1400px !important;
    padding: 0 2rem 5rem !important;
}}

::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {T["scrollbar_track"]}; }}
::-webkit-scrollbar-thumb {{ background: {T["scrollbar_thumb"]}; border-radius: 3px; }}

/* ── Nav ─ */
.topnav {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.1rem 0 0.9rem;
    border-bottom: 1px solid {T["border"]};
    margin-bottom: 2rem;
    position: relative;
}}
/* subtle gradient underline on the nav border */
.topnav::after {{
    content: '';
    position: absolute;
    bottom: -1px; left: 0;
    width: 160px; height: 1px;
    background: linear-gradient(90deg, {T["accent_blue"]}, {T["accent_green"]}, transparent);
}}
.topnav-left {{
    display: flex;
    align-items: center;
    gap: 1.4rem;
}}
.topnav-brand {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.08rem;
    font-weight: 700;
    letter-spacing: -0.025em;
    /* gradient text */
    background: linear-gradient(120deg, {T["accent_blue"]} 0%, {T["accent_green"]} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-fill-color: transparent;
}}
.brand-mark {{
    width: 28px; height: 28px;
    border-radius: 7px;
    background: linear-gradient(135deg, {T["accent_blue"]}22, {T["accent_green"]}22);
    border: 1px solid {T["accent_blue"]}33;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    position: relative;
    overflow: hidden;
}}
.brand-mark::after {{
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, {T["accent_blue"]}18, transparent 60%);
}}
/* animated dot inside brand mark replaced by SVG chart line */
.topnav-pills {{
    display: flex;
    align-items: center;
    gap: 0.35rem;
}}
.nav-pill {{
    font-size: 0.65rem;
    font-weight: 600;
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    padding: 3px 9px;
    border-radius: 999px;
    border: 1px solid {T["border"]};
    color: {T["text_muted"]};
    background: {T["bg_card"]};
    white-space: nowrap;
    transition: border-color 0.2s, color 0.2s;
}}
.nav-pill:hover {{
    border-color: {T["accent_blue"]}55;
    color: {T["text_secondary"]};
}}
.nav-pill.active {{
    border-color: {T["accent_blue"]}44;
    color: {T["accent_blue"]};
    background: {T["accent_blue"]}0d;
}}
/* theme toggle icon button */
.theme-icon-btn {{
    width: 32px; height: 32px;
    border-radius: 8px;
    border: 1px solid {T["border"]};
    background: {T["bg_card"]};
    display: flex; align-items: center; justify-content: center;
    cursor: pointer;
    transition: border-color 0.18s, background 0.18s;
    flex-shrink: 0;
}}
.theme-icon-btn:hover {{
    border-color: {T["accent_blue"]}55;
    background: {T["bg_card_hover"]};
}}

/* ── Section rail header ─ */
.rail-header {{
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin: 2rem 0 1.1rem;
}}
.rail-bar {{
    width: 3px; height: 16px;
    border-radius: 2px;
    background: {T["accent_blue"]};
    box-shadow: 0 0 8px {T["glow_blue"]};
    flex-shrink: 0;
}}
.rail-title {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.8rem;
    font-weight: 600;
    color: {T["text_secondary"]};
    letter-spacing: 0.09em;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 0.45rem;
}}
.rail-line {{
    flex: 1;
    height: 1px;
    background: {T["border"]};
}}

/* ── Metric cards ─ */
[data-testid="stMetric"] {{
    background: {T["bg_card"]} !important;
    border: 1px solid {T["border"]} !important;
    border-radius: 10px !important;
    padding: 1rem 1.2rem !important;
    transition: border-color 0.2s, box-shadow 0.2s;
    position: relative;
    overflow: hidden;
}}
[data-testid="stMetric"]::after {{
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 2px;
    background: linear-gradient(90deg, {T["accent_blue"]}30, transparent);
}}
[data-testid="stMetric"]:hover {{
    border-color: {T["border_accent"]}55 !important;
    box-shadow: {T["shadow"]} !important;
}}
[data-testid="stMetricLabel"] {{
    color: {T["text_secondary"]} !important;
    font-size: 0.72rem !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
}}
[data-testid="stMetricValue"] {{
    color: {T["text_primary"]} !important;
    font-size: 1.45rem !important;
    font-weight: 700 !important;
    font-family: 'JetBrains Mono', monospace !important;
    letter-spacing: -0.03em !important;
}}
[data-testid="stMetricDelta"] {{
    font-size: 0.78rem !important;
    font-family: 'JetBrains Mono', monospace !important;
}}

/* ── Inputs ─ */
[data-testid="stTextInput"] input {{
    background: {T["bg_input"]} !important;
    border: 1px solid {T["border"]} !important;
    border-radius: 10px !important;
    color: {T["text_primary"]} !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.06em !important;
    padding: 0.65rem 1rem !important;
    height: 46px !important;
    transition: border-color 0.2s, box-shadow 0.2s;
}}
[data-testid="stTextInput"] input:focus {{
    border-color: {T["accent_blue"]} !important;
    box-shadow: 0 0 0 3px {T["glow_blue"]} !important;
    outline: none !important;
}}
[data-testid="stTextInput"] input::placeholder {{
    color: {T["text_muted"]} !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 400 !important;
    letter-spacing: 0 !important;
    font-size: 0.87rem !important;
}}

/* ── Buttons ─ */
[data-testid="stButton"] button[kind="primary"],
[data-testid="baseButton-primary"] {{
    background: {T["accent_blue"]} !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    height: 46px !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 4px 14px {T["glow_blue"]} !important;
    transition: opacity 0.18s, transform 0.12s !important;
}}
[data-testid="stButton"] button[kind="primary"]:hover {{
    opacity: 0.87 !important;
    transform: translateY(-1px) !important;
}}
[data-testid="stButton"] button[kind="secondary"],
[data-testid="baseButton-secondary"] {{
    background: {T["bg_card"]} !important;
    color: {T["text_secondary"]} !important;
    border: 1px solid {T["border"]} !important;
    border-radius: 10px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.83rem !important;
    font-weight: 500 !important;
    transition: border-color 0.18s, color 0.18s !important;
}}
[data-testid="stButton"] button[kind="secondary"]:hover {{
    border-color: {T["accent_blue"]}88 !important;
    color: {T["text_primary"]} !important;
}}

/* ── Link buttons ─ */
[data-testid="stLinkButton"] a {{
    background: {T["bg_card"]} !important;
    color: {T["accent_blue"]} !important;
    border: 1px solid {T["border"]} !important;
    border-radius: 8px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    padding: 0.38rem 0.85rem !important;
    transition: border-color 0.18s !important;
}}
[data-testid="stLinkButton"] a:hover {{
    border-color: {T["accent_blue"]} !important;
}}

/* ── Progress bar ─ */
[data-testid="stProgressBar"] > div {{
    background: {T["border"]} !important;
    border-radius: 4px !important;
}}
[data-testid="stProgressBar"] > div > div {{
    background: linear-gradient(90deg, {T["accent_blue"]}, {T["accent_green"]}) !important;
    border-radius: 4px !important;
}}

/* ── Alert / info ─ */
[data-testid="stAlert"] {{
    background: {T["bg_card"]} !important;
    border: 1px solid {T["border"]} !important;
    border-radius: 10px !important;
    color: {T["text_secondary"]} !important;
    font-size: 0.88rem !important;
}}

/* ── Dataframe — force dark theme into Streamlit's internal iframe ─ */
[data-testid="stDataFrame"] {{
    border: 1px solid {T["border"]} !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    background: {T["bg_card"]} !important;
}}
[data-testid="stDataFrame"] > div {{
    background: {T["bg_card"]} !important;
    border-radius: 12px !important;
}}
/* Target the glide-data-editor canvas wrapper */
[data-testid="stDataFrame"] iframe {{
    filter: {'invert(0)' if not is_dark else 'none'} !important;
}}

/* ── Custom HTML forecast table ─ */
.forecast-table-wrap {{
    border: 1px solid {T["border"]};
    border-radius: 14px;
    overflow: hidden;
    background: {
        'linear-gradient(160deg, #0F1D2E 0%, #0A1520 60%, #0D1F30 100%)' if is_dark else T["bg_card"]};
    position: relative;
    box-shadow: {'0 0 0 1px rgba(76,155,232,0.08), 0 8px 32px rgba(0,0,0,0.4)' if is_dark else T["shadow"]};
    margin-bottom: 1.25rem;
}}
.forecast-table-wrap::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, {T["accent_blue"]}, {T["accent_green"]}80, transparent);
    z-index: 1;
}}
{'/* dark-mode ambient glow */ .forecast-table-wrap::after { content: ""; position: absolute; top: -40px; left: 50%; transform: translateX(-50%); width: 60%; height: 60px; background: radial-gradient(ellipse, rgba(76,155,232,0.12) 0%, transparent 70%); pointer-events: none; z-index: 0; }' if is_dark else ''}
.forecast-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
    position: relative;
    z-index: 1;
}}
.forecast-table thead tr {{
    background: {'rgba(76,155,232,0.06)' if is_dark else T["bg_surface"]};
    border-bottom: 1px solid {T["border"]};
}}
.forecast-table th {{
    padding: 0.75rem 1.2rem;
    text-align: left;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: {T["text_muted"]};
    white-space: nowrap;
}}
.forecast-table th:not(:first-child) {{
    text-align: right;
}}
.forecast-table tbody tr {{
    border-bottom: 1px solid {T["border"] if not is_dark else "rgba(30,45,61,0.7)"};
    transition: background 0.15s;
}}
.forecast-table tbody tr:nth-child(odd) {{
    background: {
        'rgba(76,155,232,0.03)' if is_dark else 'rgba(26,114,204,0.025)'};
}}
.forecast-table tbody tr:nth-child(even) {{
    background: {'rgba(46,204,113,0.025)' if is_dark else 'transparent'};
}}
.forecast-table tbody tr:last-child {{
    border-bottom: none;
}}
.forecast-table tbody tr:hover {{
    background: {'rgba(76,155,232,0.09)' if is_dark else T["bg_card_hover"]} !important;
}}
.forecast-table td {{
    padding: 0.78rem 1.2rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.83rem;
    color: {T["text_primary"]};
    white-space: nowrap;
}}
.forecast-table td:not(:first-child) {{
    text-align: right;
}}
.forecast-table td.date-col {{
    color: {T["text_secondary"]};
    font-size: 0.8rem;
    {'border-left: 2px solid rgba(76,155,232,0.15);' if is_dark else ''}
}}
.forecast-table td.chg-pos {{
    color: {T["accent_green"]};
    {'text-shadow: 0 0 12px rgba(46,204,113,0.4);' if is_dark else ''}
}}
.forecast-table td.chg-neg {{
    color: {T["accent_red"]};
    {'text-shadow: 0 0 12px rgba(255,77,109,0.4);' if is_dark else ''}
}}
.forecast-table td.chg-neu {{ color: {T["text_muted"]}; }}

/* ── Expander ─ */
[data-testid="stExpander"] {{
    background: {T["bg_card"]} !important;
    border: 1px solid {T["border"]} !important;
    border-radius: 10px !important;
    margin-bottom: 0.5rem !important;
}}
[data-testid="stExpander"] summary {{
    color: {T["text_primary"]} !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.88rem !important;
    padding: 0.75rem 1rem !important;
}}

hr {{ border: none !important; border-top: 1px solid {T["border"]} !important; margin: 1.75rem 0 !important; }}

/* ── Compact icon-only theme toggle ─ */
.nav-toggle-wrap {{
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding-top: 0.7rem;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid {T["border"]};
    margin-bottom: 2rem;
}}
.nav-toggle-wrap [data-testid="stButton"] button {{
    width: 34px !important;
    height: 34px !important;
    min-width: 34px !important;
    max-width: 34px !important;
    padding: 0 !important;
    font-size: 1.05rem !important;
    border-radius: 9px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-shadow: none !important;
    background: {T["bg_card"]} !important;
    border: 1px solid {T["border"]} !important;
    color: {T["text_secondary"]} !important;
    transition: border-color 0.18s, color 0.18s !important;
    line-height: 1 !important;
}}
.nav-toggle-wrap [data-testid="stButton"] button:hover {{
    border-color: {T["accent_blue"]}77 !important;
    color: {T["text_primary"]} !important;
    background: {T["bg_card_hover"]} !important;
}}

/* ── Watchlist table ─ */
.wl-wrap {{
    border: 1px solid {T["wl_border"]};
    border-radius: 12px;
    overflow: hidden;
    margin-top: 0.5rem;
}}
.wl-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.83rem;
}}
.wl-table th {{
    text-align: right;
    color: {T["text_muted"]};
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 0.7rem;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    padding: 0.7rem 1rem;
    border-bottom: 1px solid {T["border"]};
    background: {T["bg_surface"]};
    white-space: nowrap;
}}
.wl-table th:first-child {{ text-align: left; }}
.wl-table td {{
    padding: 0.75rem 1rem;
    border-bottom: 1px solid {T["border"]};
    text-align: right;
    vertical-align: middle;
    color: {T["text_primary"]};
    font-family: 'JetBrains Mono', monospace;
    background: {T["bg_card"]};
    white-space: nowrap;
}}
.wl-table td:first-child {{ text-align: left; font-family: 'Inter', sans-serif; }}
.wl-table tr:last-child td {{ border-bottom: none; }}
.wl-table tbody tr:hover td {{ background: {T["wl_hover"]}; cursor: pointer; }}
.wl-ticker {{ font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 0.88rem; color: {T["text_primary"]}; }}
.wl-name {{ color: {T["text_muted"]}; font-size: 0.72rem; font-family: 'Inter', sans-serif; margin-top: 1px; }}
.wl-up {{ color: {T["accent_green"]}; }}
.wl-dn {{ color: {T["accent_red"]}; }}
.wl-neutral {{ color: {T["text_muted"]}; }}

/* ── Signal badge ─ */
.signal-wrap {{ display:flex; justify-content:center; margin: 1.25rem 0; }}
.signal-badge {{
    display: inline-flex;
    align-items: center;
    gap: 0.55rem;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.45rem;
    font-weight: 700;
    letter-spacing: 0.07em;
    padding: 0.8rem 2.4rem;
    border-radius: 12px;
    border: 1px solid;
    position: relative;
    overflow: hidden;
}}
.signal-badge::before {{
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse at 30% 50%, rgba(255,255,255,0.07), transparent 70%);
    pointer-events: none;
}}

/* ── Recommendation narrative box ─ */
.rec-box {{
    background: {T["bg_card"]};
    border: 1px solid {T["border"]};
    border-radius: 10px;
    padding: 1.1rem 1.4rem;
    font-size: 0.9rem;
    line-height: 1.75;
    color: {T["text_secondary"]};
    font-family: 'Inter', sans-serif;
    margin: 1rem 0;
}}

/* ── News card ─ */
.news-card {{
    background: {T["bg_card"]};
    border: 1px solid {T["border"]};
    border-radius: 10px;
    padding: 0.95rem 1.1rem 0.95rem 1.25rem;
    margin-bottom: 0.6rem;
    position: relative;
    transition: border-color 0.18s, transform 0.14s;
    overflow: hidden;
}}
.news-card::before {{
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    border-radius: 0 2px 2px 0;
    transition: background 0.2s;
}}
.news-card.pos::before {{ background: {T["accent_green"]}; }}
.news-card.neg::before {{ background: {T["accent_red"]}; }}
.news-card.neu::before {{ background: {T["text_muted"]}; }}
.news-card:hover {{
    border-color: {T["border_accent"]}55;
    transform: translateX(2px);
}}
.news-title {{
    font-size: 0.88rem;
    font-weight: 500;
    color: {T["text_primary"]};
    line-height: 1.45;
    margin-bottom: 0.38rem;
}}
.news-meta {{
    font-size: 0.73rem;
    color: {T["text_muted"]};
    display: flex;
    align-items: center;
    gap: 0.45rem;
    flex-wrap: wrap;
    font-family: 'Space Grotesk', sans-serif;
}}
.news-meta .sep {{ opacity: 0.5; }}
.sentiment-pill {{
    display: inline-flex;
    align-items: center;
    gap: 3px;
    font-size: 0.69rem;
    font-weight: 600;
    font-family: 'Space Grotesk', sans-serif;
    padding: 1px 8px;
    border-radius: 999px;
    letter-spacing: 0.03em;
}}
.pill-pos {{ background: {T["pos_pill_bg"]}; color: {T["accent_green"]}; border: 1px solid {T["accent_green"]}33; }}
.pill-neg {{ background: {T["neg_pill_bg"]}; color: {T["accent_red"]}; border: 1px solid {T["accent_red"]}33; }}
.pill-neu {{ background: {T["neu_pill_bg"]}; color: {T["text_secondary"]}; border: 1px solid {T["border"]}; }}

/* ── Sentiment bar ─ */
.sbar-labels {{
    display: flex;
    justify-content: space-between;
    font-size: 0.72rem;
    color: {T["text_muted"]};
    font-family: 'Space Grotesk', sans-serif;
    margin-bottom: 0.3rem;
}}
.sbar {{
    display: flex; height: 5px;
    border-radius: 3px; overflow: hidden; gap: 2px;
}}
.sbar-p {{ background: {T["accent_green"]}; border-radius: 3px 0 0 3px; }}
.sbar-n {{ background: {T["text_muted"]}; }}
.sbar-e {{ background: {T["accent_red"]}; border-radius: 0 3px 3px 0; }}

/* ── Disclaimer ─ */
.disclaimer {{
    display: flex;
    align-items: center;
    gap: 0.55rem;
    background: {T["disclaimer_bg"]};
    border: 1px solid {T["accent_amber"]}33;
    border-radius: 8px;
    padding: 0.6rem 1rem;
    font-size: 0.76rem;
    color: {T["accent_amber"]};
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 500;
    margin: 0.85rem 0;
}}

/* ── Chart wrapper ─ */
.chart-wrap {{
    background: {T["bg_card"]};
    border: 1px solid {T["border"]};
    border-radius: 12px;
    padding: 1.2rem 1.2rem 0.4rem;
    margin-bottom: 0.5rem;
    box-shadow: {T["shadow"]};
}}

/* ── Watchlist ticker buttons ─ */
.wl-btn-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-bottom: 1rem;
}}
.wl-btn {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 6px;
    border: 1px solid {T["border"]};
    background: {T["bg_card"]};
    color: {T["text_secondary"]};
    cursor: pointer;
    transition: border-color 0.15s, color 0.15s;
}}
.wl-btn:hover {{
    border-color: {T["accent_blue"]}66;
    color: {T["text_primary"]};
}}

/* ── Stock header ─ */
.stock-header {{
    margin: 1.25rem 0 0.5rem;
}}
.stock-name {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: {T["text_primary"]};
    letter-spacing: -0.025em;
    line-height: 1.2;
}}
.stock-sub {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: {T["text_muted"]};
    letter-spacing: 0.07em;
    margin-top: 3px;
}}

/* ── Info hint ─ */
.hint-box {{
    display: flex;
    align-items: center;
    gap: 0.65rem;
    margin-top: 1.5rem;
    padding: 1rem 1.2rem;
    background: {T["bg_card"]};
    border: 1px solid {T["border"]};
    border-radius: 10px;
    font-size: 0.87rem;
    color: {T["text_secondary"]};
    font-family: 'Inter', sans-serif;
}}
</style>
""", unsafe_allow_html=True)


# ── Reusable helpers ─────────────────────────────────────────────────────────

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
    return dict(
        template=T["plotly_theme"],
        height=height,
        paper_bgcolor=T["chart_paper"],
        plot_bgcolor=T["chart_paper"],
        margin=dict(l=0, r=0, t=12, b=0),
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
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
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


# ── Nav bar (shared across pages) ───────────────────────────────────────────
def render_nav(show_back: bool = False) -> None:
    # Brand mark: tiny chart polyline inside a rounded tile
    brand_svg = (
        '<svg width="15" height="15" viewBox="0 0 24 24" fill="none"'
        ' stroke="' + T["accent_blue"] + '" stroke-width="2.4"'
        ' stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="3 17 8 10 13 14 21 5"/>'
        '<circle cx="21" cy="5" r="2.5" fill="' +
        T["accent_green"] + '" stroke="none"/>'
        '</svg>'
    )

    # Unicode symbol for the compact toggle (renders fine in st.button label)
    toggle_ico = "\u2600" if is_dark else "\u263D"   # ☀ / ☽
    toggle_tip = "Switch to light mode" if is_dark else "Switch to dark mode"

    # Optional breadcrumb on detail page
    back_html = ""
    if show_back:
        back_html = (
            '<div style="margin-bottom:0.28rem;">'
            '<span style="font-size:0.7rem;color:' + T["text_muted"] + ';'
            'font-family:Space Grotesk,sans-serif;letter-spacing:0.04em;">'
            '← Watchlist'
            '</span></div>'
        )

    # Metadata pills — rendered as pure HTML, no Streamlit widget
    pills = (
        '<div class="topnav-pills">'
        '<span class="nav-pill active">LSTM</span>'
        '<span class="nav-pill">2Y window</span>'
        '<span class="nav-pill">7-day forecast</span>'
        '<span class="nav-pill">Sentiment</span>'
        '</div>'
    )

    # Render nav brand area full-width; toggle sits inside the nav via HTML+button overlay
    c_nav, c_tog = st.columns([11, 1])
    with c_nav:
        st.markdown(
            back_html +
            '<div class="topnav">'
            '  <div class="topnav-left">'
            '    <div class="topnav-brand">'
            '      <div class="brand-mark">' + brand_svg + '</div>'
            '      Foresight'
            '    </div>'
            + pills +
            '  </div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with c_tog:
        # Vertically centred, sits flush with the nav bar
        st.markdown(
            '<div class="nav-toggle-wrap">',
            unsafe_allow_html=True,
        )
        if st.button(toggle_ico, key="theme_toggle", help=toggle_tip, type="secondary"):
            st.session_state.theme = "light" if is_dark else "dark"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
#  WATCHLIST PAGE
# ════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=900)
def _load_watchlist() -> list[dict]:
    rows = []
    for t in WATCHLIST:
        try:
            df_w = fetch_stock_data(t, period="3mo")
            info_w = get_stock_info(t)
            close = df_w["Close"].values.astype(float)
            prev = close[-2] if len(close) >= 2 else close[-1]
            curr = close[-1]
            rows.append({
                "ticker":    t,
                "name":      info_w["name"][:26],
                "price":     curr,
                "chg":       curr - prev,
                "pct":       (curr - prev) / prev * 100,
                "open":      float(df_w["Open"].values[-1]),
                "high":      float(df_w["High"].values[-1]),
                "low":       float(df_w["Low"].values[-1]),
                "prev":      prev,
                "close_arr": close,
            })
        except Exception:
            pass
    return rows


def _watchlist_table_html(rows: list[dict]) -> str:
    header = f"""
<div class="wl-wrap">
<table class="wl-table">
<thead><tr>
  <th>Ticker</th>
  <th>Price</th>
  <th>Change</th>
  <th>Change %</th>
  <th>Open</th>
  <th>High</th>
  <th>Low</th>
  <th>Prev close</th>
  <th style="text-align:center;">60D trend</th>
</tr></thead>
<tbody>"""
    body = ""
    for r in rows:
        up = r["chg"] >= 0
        cls = "wl-up" if up else "wl-dn"
        sign = "+" if up else ""
        spark = sparkline_svg(r["close_arr"][-60:])
        body += f"""
<tr>
  <td>
    <div class="wl-ticker">{r["ticker"]}</div>
    <div class="wl-name">{r["name"]}</div>
  </td>
  <td>{r["price"]:.2f}</td>
  <td class="{cls}">{sign}{r["chg"]:.2f}</td>
  <td class="{cls}">{sign}{r["pct"]:.2f}%</td>
  <td>{r["open"]:.2f}</td>
  <td>{r["high"]:.2f}</td>
  <td>{r["low"]:.2f}</td>
  <td>{r["prev"]:.2f}</td>
  <td style="text-align:center;">{spark}</td>
</tr>"""
    return header + body + "</tbody></table></div>"


# Watchlist page
def render_watchlist_page():
    render_ticker_strip()
    st.markdown("""
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="44" height="44">
        <rect width="64" height="64" rx="12" fill="#1E2530"/>
        <polyline points="6,48 18,30 28,38 40,18 54,26"
          fill="none" stroke="#ffffff" stroke-width="4"
          stroke-linecap="round" stroke-linejoin="round"/>
        <circle cx="54" cy="26" r="5" fill="#2ECC71"/>
      </svg>
      <span style="font-size:2.4rem; font-weight:700; color:var(--text-color); letter-spacing:-0.5px;">Stock Predictor</span>
    </div>
    """, unsafe_allow_html=True)

    # Navigation bar
    nav1, nav2, _ = st.columns([1, 1, 6])
    with nav1:
        st.button("Market", disabled=True,
                  use_container_width=True, key="nav_market")
    with nav2:
        if st.button("Compare", use_container_width=True, key="nav_compare"):
            st.session_state.page = "compare"
            st.rerun()

    # Input
    _prefill = st.session_state.pop("prefill", "AAPL")
    _auto_run = st.session_state.pop("auto_run", False)

    col_input, col_btn = st.columns([4, 1])
    with col_input:
        ticker = st.text_input(
            "Ticker",
            value=_prefill,
            placeholder="e.g. AAPL, TSLA, 600519.SS, 000858.SZ",
            label_visibility="collapsed",
        ).strip().upper()
    with col_btn:
        run_btn = st.button("Analyse", type="primary",
                            use_container_width=True) or auto_run

    if "recent_searches" not in st.session_state:
        st.session_state.recent_searches = []

    if run_btn and ticker:
        if ticker in st.session_state.recent_searches:
            st.session_state.recent_searches.remove(ticker)
        st.session_state.recent_searches.insert(0, ticker)
        st.session_state.recent_searches = st.session_state.recent_searches[:8]

        st.session_state.selected_ticker = ticker
        st.session_state.page = "detail"
        st.rerun()
    # ── Recent searches (dropdown, write in recent search without Predict) ──────
    if st.session_state.recent_searches:
        recent_line = "  ·  ".join(st.session_state.recent_searches)
        st.caption(f"Recent: {recent_line}")

    if not run_btn:
        st.markdown(f"""
<div class="hint-box">
  {icon("info", 15, T["text_muted"])}
  Enter any ticker above and click <strong style="color:{T["text_primary"]};
  font-family:Space Grotesk,sans-serif;">Analyse</strong> — or click a symbol from
  the watchlist below to open its detail view.
</div>
""", unsafe_allow_html=True)
        picked = st.radio(
            "pick recent",
            options=st.session_state.recent_searches,
            horizontal=True,
            label_visibility="collapsed",
            index=None,
        )
    if picked and picked != st.session_state.get("_last_picked"):
        st.session_state._last_picked = picked
        st.session_state.prefill = picked
        st.rerun()

    # ── Watchlist table
    rail_header("Market watchlist", icon("chart-line", 13, T["text_muted"]))
    with st.spinner("Loading market data…"):
        wl_rows = _load_watchlist()

    # Quick-access ticker chips (Streamlit buttons rendered as chips via CSS)
    if wl_rows:
        cols = st.columns(min(len(wl_rows), 10))
        for i, r in enumerate(wl_rows):
            up = r["chg"] >= 0
            label = f"{'▲' if up else '▼'} {r['ticker']}"
            with cols[i % 10]:
                if st.button(label, key=f"chip_{r['ticker']}", use_container_width=True, type="secondary"):
                    st.session_state.selected_ticker = r["ticker"]
                    st.session_state.page = "detail"
                    st.rerun()

        st.markdown(_watchlist_table_html(wl_rows), unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
#  DETAIL PAGE
# ════════════════════════════════════════════════════════════════════════════

def _build_candlestick(_ticker: str, df: pd.DataFrame,
                       _currency: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"],   close=df["Close"],
        name="OHLC",
        increasing=dict(
            line=dict(color=T["accent_green"], width=1), fillcolor=T["accent_green"]),
        decreasing=dict(
            line=dict(color=T["accent_red"],   width=1), fillcolor=T["accent_red"]),
    ))
    sma20 = df["Close"].rolling(20).mean()
    sma50 = df["Close"].rolling(50).mean()
    fig.add_trace(go.Scatter(x=df.index, y=sma20, mode="lines",
                             name="SMA 20", line=dict(color=T["accent_amber"], width=1.2)))
    fig.add_trace(go.Scatter(x=df.index, y=sma50, mode="lines",
                             name="SMA 50", line=dict(color="#A78BFA", width=1.2)))
    layout = chart_layout(height=480)
    layout.update(
        xaxis_rangeslider_visible=True,
        xaxis_rangeselector=dict(
            buttons=[
                dict(count=1,  label="1M", step="month", stepmode="backward"),
                dict(count=3,  label="3M", step="month", stepmode="backward"),
                dict(count=6,  label="6M", step="month", stepmode="backward"),
                dict(count=1,  label="YTD", step="year", stepmode="todate"),
                dict(count=1,  label="1Y", step="year", stepmode="backward"),
                dict(step="all", label="All"),
            ],
            bgcolor=T["bg_surface"],
            activecolor=T["accent_blue"],
            font=dict(color=T["text_secondary"],
                      family="Space Grotesk", size=11),
        ),
        hovermode="x unified",
        dragmode="zoom",
    )
    fig.update_layout(**layout)
    return fig


def _build_recommendation_text(rec: dict, news_result: dict) -> str:
    """
    Compose a concise narrative paragraph explaining the recommendation,
    grounded in actual signal drivers rather than generic boilerplate.
    """
    signal = rec["signal"]
    price_pct = rec["price_change_pct"]
    score = rec["combined_score"]
    sentiment = news_result["sentiment_label"]
    pos = news_result["positive_count"]
    neg = news_result["negative_count"]
    neu = news_result["neutral_count"]
    total = pos + neg + neu or 1

    direction = "rise" if price_pct > 0 else "fall"
    trend_str = f"{'up' if price_pct > 0 else 'down'} {abs(price_pct):.1f}%"
    score_desc = (
        "strongly bullish" if score > 0.5 else
        "moderately bullish" if score > 0.15 else
        "roughly neutral" if score > -0.15 else
        "moderately bearish" if score > -0.5 else
        "strongly bearish"
    )

    # News driver sentence
    if pos > neg and pos > neu:
        news_sent = (
            f"News flow is tilting positive — {pos} of {total} recent articles "
            f"carry a constructive tone, which supports near-term momentum."
        )
    elif neg > pos and neg > neu:
        news_sent = (
            f"News flow is cautionary — {neg} of {total} recent articles "
            f"carry a negative tone, which weighs on the short-term outlook."
        )
    else:
        news_sent = (
            f"News flow is mixed, with {pos} positive, {neu} neutral and {neg} negative "
            f"articles, offering no strong directional signal from the press."
        )

    if "BUY" in signal:
        action_hint = "treat this as a potential entry point if your own analysis aligns"
    elif "SELL" in signal:
        action_hint = "consider reducing exposure or waiting for a clearer reversal signal"
    else:
        action_hint = "no decisive edge in either direction; monitor for a breakout catalyst"

    return (
        f"The LSTM model projects the price to <strong>{direction} {trend_str} "
        f"over the next 7 trading days</strong>, while the overall combined signal "
        f"reads as <strong>{score_desc}</strong> (score {score:+.2f}). "
        f"{news_sent} "
        f"Taking both the quantitative forecast and the prevailing sentiment into account, "
        f"the model issues a <strong>{signal}</strong> signal — {action_hint}."
    )


def render_detail_page(ticker: str) -> None:
    render_nav(show_back=True)
    render_ticker_strip()

    # Back button
    if st.button("← Back to watchlist",
                 key="back_btn", type="secondary"):
        st.session_state.page = "watchlist"
        st.session_state.selected_ticker = None
        st.rerun()

    st.markdown("""
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="44" height="44">
        <rect width="64" height="64" rx="12" fill="#1E2530"/>
        <polyline points="6,48 18,30 28,38 40,18 54,26"
          fill="none" stroke="#ffffff" stroke-width="4"
          stroke-linecap="round" stroke-linejoin="round"/>
        <circle cx="54" cy="26" r="5" fill="#2ECC71"/>
      </svg>
      <span style="font-size:2.4rem; font-weight:700; color:var(--text-color); letter-spacing:-0.5px;">Stock Predictor</span>
    </div>
    """, unsafe_allow_html=True)
    # ── Load data / cache ────────────────────────────────────────────────────
    cached = cache_manager.load(ticker)
    if cached:
        df = cached["df"]
        info = cached["info"]
        result = cached["result"]
        st.success("Loaded from cache — results ready instantly.")
    else:
        with st.spinner(f"Fetching 2-year data for {ticker}…"):
            try:
                df = fetch_stock_data(ticker)
                info = get_stock_info(ticker)
            except ValueError as e:
                st.error(str(e))
                return

        rail_header("LSTM model training", icon("brain", 13, T["text_muted"]))
        progress_bar = st.progress(0)
        status_text = st.empty()

        def on_epoch(epoch, total):
            progress_bar.progress(epoch / total)
            status_text.markdown(
                f'<span style="font-family:Space Grotesk,sans-serif;font-size:0.8rem;'
                f'color:{T["text_muted"]};">Training · epoch {epoch} / {total}</span>',
                unsafe_allow_html=True,
            )

        result = run_prediction(df, future_days=7, epoch_callback=on_epoch)
        progress_bar.progress(1.0)
        status_text.markdown(
            f'<span style="font-family:Space Grotesk,sans-serif;font-size:0.8rem;'
            f'color:{T["accent_green"]};">{icon("check", 13, T["accent_green"])} '
            f'&nbsp;Training complete</span>',
            unsafe_allow_html=True,
        )
        cache_manager.save(ticker, {"df": df, "info": info, "result": result})

    prices = df["Close"].to_numpy(dtype=float)

    if isinstance(df.index, pd.DatetimeIndex):
        if df.index.tz is not None:
            dates = df.index.tz_localize(None)
        else:
            dates = df.index
    else:
        dates = df.index

    currency = info["currency"]
    current_price = info["current_price"]

    # ── Stock header + metrics ───────────────────────────────────────────────
    st.markdown(f"""
<div class="stock-header">
  <div class="stock-name">{info["name"]}</div>
  <div class="stock-sub">{ticker} &nbsp;·&nbsp; {currency}</div>
</div>
""", unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    high_price = float(df["Close"].max())
    low_price = float(df["Close"].min())

    m1.metric(
        "Current price",
        f"{currency} {current_price:.2f}" if current_price else "N/A"
    )
    m2.metric("Data points", f"{len(prices)} days")
    m3.metric("2Y high", f"{currency} {high_price:.2f}")
    m4.metric("2Y low", f"{currency} {low_price:.2f}")

    st.markdown("<hr/>", unsafe_allow_html=True)

    # ── K-line chart ─────────────────────────────────────────────────────────
    rail_header("K-line chart — OHLC with SMA overlays",
                icon("candlestick", 13, T["text_muted"]))
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    st.plotly_chart(_build_candlestick(ticker, df, currency),
                    use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Historical close ──────────────────────────────────────────────────────
    rail_header("Historical closing price — 2 years",
                icon("activity", 13, T["text_muted"]))
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=dates, y=prices, mode="lines", name="Close",
        line=dict(color=T["accent_blue"], width=1.6),
        fill="tozeroy",
        fillcolor=f"rgba({int(T['accent_blue'][1:3],16)},{int(T['accent_blue'][3:5],16)},{int(T['accent_blue'][5:7],16)},0.07)",
        hovertemplate="<b>%{x|%b %d %Y}</b><br>%{y:.2f} " +
        currency + "<extra></extra>",
    ))
    fig1.update_layout(**chart_layout(340))
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Unpack prediction results ─────────────────────────────────────────────
    test_preds = result["test_preds"]
    test_start = result["test_start_idx"]
    train_end = result["train_end_idx"]
    future_preds = result["future_preds"]
    test_dates = dates[test_start:]
    predicted_return_pct = (
        future_preds[-1] - current_price) / current_price * 100

    # ── Forecast summary metrics ──────────────────────────────────────────────
    rail_header("Forecast summary")
    c1, c2 = st.columns(2)
    c1.metric("Expected return — 7 days", f"{predicted_return_pct:+.2f}%",
              delta=f"{predicted_return_pct:+.2f}%")
    c2.metric("Predicted price — day 7", f"{currency} {future_preds[-1]:.2f}")

    st.markdown("<hr/>", unsafe_allow_html=True)

    # ── Actual vs predicted ───────────────────────────────────────────────────
    rail_header("Model fit — actual vs predicted",
                icon("layers", 13, T["text_muted"]))
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=dates, y=prices, mode="lines", name="Actual",
        line=dict(color=T["accent_blue"], width=1.6),
        hovertemplate="<b>%{x|%b %d %Y}</b><br>Actual: %{y:.2f}<extra></extra>",
    ))
    fig2.add_trace(go.Scatter(
        x=test_dates, y=test_preds, mode="lines", name="Predicted",
        line=dict(color=T["accent_green"], width=1.6, dash="dot"),
        hovertemplate="<b>%{x|%b %d %Y}</b><br>Predicted: %{y:.2f}<extra></extra>",
    ))
    fig2.add_vline(
        x=dates[train_end], line_dash="dot", line_color=T["text_muted"],
        annotation_text="Train / Test split",
        annotation_position="top left",
        annotation_font=dict(color=T["text_muted"],
                             size=11, family="Space Grotesk"),
    )
    fig2.update_layout(**chart_layout(400))
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── 7-day forecast ────────────────────────────────────────────────────────
    rail_header("7-day price forecast",
                icon("chart-line", 13, T["text_muted"]))
    last_date = pd.Timestamp(dates[-1])
    future_dates = pd.bdate_range(
        start=last_date + timedelta(days=1), periods=7)

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=dates[-60:], y=prices[-60:],
        mode="lines", name="Last 60 days",
        line=dict(color=T["accent_blue"], width=1.6),
        hovertemplate="<b>%{x|%b %d %Y}</b><br>%{y:.2f}<extra></extra>",
    ))
    fig3.add_trace(go.Scatter(
        x=[dates[-1], future_dates[0]],
        y=[prices[-1], future_preds[0]],
        mode="lines", showlegend=False,
        line=dict(color=T["accent_green"], width=1.2, dash="dot"),
    ))
    fig3.add_trace(go.Scatter(
        x=future_dates, y=future_preds,
        mode="lines+markers", name="7-day forecast",
        line=dict(color=T["accent_green"], width=2.2),
        marker=dict(size=8, symbol="circle", color=T["accent_green"],
                    line=dict(color=T["bg_base"], width=2)),
        hovertemplate="<b>%{x|%b %d %Y}</b><br>Forecast: %{y:.2f}<extra></extra>",
    ))
    fig3.add_vrect(
        x0=future_dates[0], x1=future_dates[-1],
        fillcolor=T["accent_green"], opacity=0.03,
        layer="below", line_width=0,
    )
    fig3.update_layout(**chart_layout(380))
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Forecast table ────────────────────────────────────────────────────────
    rail_header("7-day forecast breakdown",
                icon("calendar", 13, T["text_muted"]))
    prev_prices = [prices[-1]] + list(future_preds[:-1])

    def _cc(v):
        return "chg-pos" if v.startswith("+") else ("chg-neg" if v.startswith("-") else "chg-neu")

    daily_chg = [
        f"{(future_preds[i]-prev_prices[i])/prev_prices[i]*100:+.2f}%" for i in range(7)]
    vs_today = [
        f"{(future_preds[i]-current_price)/current_price*100:+.2f}%" for i in range(7)]
    dates_fmt = future_dates.strftime("%Y-%m-%d")

    tbody = "".join(
        f"<tr>"
        f"<td class='date-col'>{dates_fmt[i]}</td>"
        f"<td>{future_preds[i]:.2f}</td>"
        f"<td class='{_cc(daily_chg[i])}'>{daily_chg[i]}</td>"
        f"<td class='{_cc(vs_today[i])}'>{vs_today[i]}</td>"
        f"</tr>"
        for i in range(7)
    )
    table_html = (
        '<div class="forecast-table-wrap">'
        '<table class="forecast-table">'
        "<thead><tr>"
        "<th>Date</th>"
        f"<th>Predicted price ({currency})</th>"
        "<th>Daily change</th>"
        "<th>vs today</th>"
        "</tr></thead>"
        f"<tbody>{tbody}</tbody>"
        "</table></div>"
    )
    st.markdown(table_html, unsafe_allow_html=True)

    st.markdown(f"""
<div class="disclaimer">
  {icon("alert", 13, T["accent_amber"])}
  For educational and research purposes only — not investment advice.
</div>
""", unsafe_allow_html=True)

    # ── News & sentiment ──────────────────────────────────────────────────────
    st.markdown("<hr/>", unsafe_allow_html=True)
    rail_header("News & sentiment analysis", icon(
        "newspaper", 13, T["text_muted"]))

    with st.spinner("Fetching latest news and analysing sentiment…"):
        news_result = get_news_sentiment(ticker)
        rec = generate_recommendation(
            current_price, list(future_preds), news_result)

    st.markdown(signal_badge_html(rec["signal"]), unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Combined score",    f"{rec['combined_score']:+.2f}")
    c2.metric("Forecast return",   f"{rec['price_change_pct']:+.2f}%")
    c3.metric("News sentiment",    news_result["sentiment_label"])
    total_arts = (news_result["positive_count"]
                  + news_result["neutral_count"]
                  + news_result["negative_count"])
    c4.metric("Articles analysed", str(total_arts))

    narrative = _build_recommendation_text(rec, news_result)
    st.markdown(
        f'<div class="rec-box">{narrative}</div>', unsafe_allow_html=True)

    total = total_arts or 1
    pos_pct = news_result["positive_count"] / total * 100
    neu_pct = news_result["neutral_count"] / total * 100
    neg_pct = news_result["negative_count"] / total * 100
    st.markdown(f"""
<div style="margin:0.75rem 0 1.75rem;">
  <div class="sbar-labels">
    <span>{news_result["positive_count"]} positive</span>
    <span>{news_result["neutral_count"]} neutral</span>
    <span>{news_result["negative_count"]} negative</span>
  </div>
  <div class="sbar">
    <div class="sbar-p" style="width:{pos_pct:.1f}%;"></div>
    <div class="sbar-n" style="width:{neu_pct:.1f}%;"></div>
    <div class="sbar-e" style="width:{neg_pct:.1f}%;"></div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
    rail_header("Top market drivers", icon("search", 13, T["text_muted"]))
    for article in extract_market_drivers(news_result):
        st.markdown(news_card_html(article), unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='text-align:center;font-size:0.72rem;color:{T['text_muted']};"
        f"padding-bottom:2rem;font-family:Space Grotesk,sans-serif;'>"
        f"Foresight · LSTM forecasting · yfinance data · Educational use only"
        f"</div>",
        unsafe_allow_html=True,
    )


# Compare page


def _cached_compare(ticker_a, ticker_b):
    """Cache comparison results for 1 hour."""
    return compare_stocks(ticker_a, ticker_b)


def render_compare_page():
    # Back / nav
    col1, col2, _ = st.columns([1, 1, 6])
    with col1:
        if st.button("Market", use_container_width=True, key="nav_back_cp"):
            st.session_state.page = "watchlist"
            st.session_state.selected_ticker = None
            st.rerun()
    with col2:
        st.button("Compare", disabled=True,
                  use_container_width=True, key="nav_cp")

    st.markdown("""
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="44" height="44">
        <rect width="64" height="64" rx="12" fill="#1E2530"/>
        <polyline points="6,48 18,30 28,38 40,18 54,26"
          fill="none" stroke="#ffffff" stroke-width="4"
          stroke-linecap="round" stroke-linejoin="round"/>
        <circle cx="54" cy="26" r="5" fill="#2ECC71"/>
      </svg>
      <span style="font-size:2.4rem; font-weight:700; color:var(--text-color); letter-spacing:-0.5px;">Stock Comparer</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Select Two Stocks to Compare")

    ticker_list = WATCHLIST[:]

    col_a, col_b, col_go = st.columns([4, 4, 3])
    with col_a:
        ticker_a = st.selectbox("Stock A", ticker_list, index=0, key="comp_a")
    with col_b:
        ticker_b = st.selectbox("Stock B", ticker_list, index=1, key="comp_b")
    with col_go:
        st.write("")
        st.write("")
        run_compare = st.button(
            "\u2192 Compare", type="primary", use_container_width=True, key="compare_go")

    if run_compare:
        if ticker_a == ticker_b:
            st.warning("Please select two different stocks to compare.")
            return

        with st.spinner("Fetching data and running predictions for both stocks (this may take a minute)..."):
            report = _cached_compare(ticker_a, ticker_b)

        if report is None:
            st.error(
                "Could not complete comparison. Check the ticker symbols and try again.")
            return

        _display_compare_results(report)


def _build_radar_chart(report):
    fig = go.Figure()
    ta = report["ticker_a"]
    tb = report["ticker_b"]
    sc = report["scores"]

    axes = ["Predicted Return", "Risk", "Confidence", "Sentiment"]
    kv = {"predicted_return": 0, "volatility": 1,
          "model_confidence": 2, "sentiment": 3}
    ra, rb = [], []
    for dk, idx in kv.items():
        dd = sc.get(dk, {})
        na = dd.get("norm_a", 50) or 50
        nb = dd.get("norm_b", 50) or 50
        ra.append(na)
        rb.append(nb)
    ra.append(ra[0])
    rb.append(rb[0])
    axes.append(axes[0])

    fig.add_trace(go.Scatterpolar(
        r=ra, theta=axes, fill="toself",
        name=ta, line=dict(color="#4C9BE8", width=2),
        fillcolor="rgba(76,155,232,0.25)",
    ))
    fig.add_trace(go.Scatterpolar(
        r=rb, theta=axes, fill="toself",
        name=tb, line=dict(color="#FF7F50", width=2),
        fillcolor="rgba(255,127,80,0.25)",
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        template="plotly_dark", height=340,
        margin=dict(l=50, r=50, t=50, b=80),
        legend=dict(orientation="h", yanchor="bottom",
                    y=1.02, xanchor="right", x=1),
    )
    return fig


def _display_compare_results(report):
    ta = report["ticker_a"]
    tb = report["ticker_b"]
    sc = report["scores"]
    wr = report.get("winner")
    win_tag = wr.get("winner") if isinstance(wr, dict) else wr

    st.divider()

    # Compact recommendation banner row
    c1, spacer, c2 = st.columns([4, 0.5, 4])
    with c1:
        if win_tag:
            clr = "#2ECC71"
            txt = f"Recommended: {win_tag}"
            ic = chr(8593)
        else:
            clr = "#F39C12"
            txt = "Tie - Suggestions below"
            ic = chr(9878)
        st.markdown(
            f"<div style='background:{clr};color:#111;font-size:1.4rem;font-weight:700;"
            f"padding:0.3em 1em;border-radius:8px;text-align:center;'>"
            f"{ic} {txt}</div>",
            unsafe_allow_html=True,
        )
    with c2:
        ca, cb = st.columns(2)
        ca.metric(f"{ta} Score", f"{report['score_a']:.0f}/{report['total']}",
                  help="Combined weighted score across all dimensions (higher = better)")
        cb.metric(f"{tb} Score", f"{report['score_b']:.0f}/{report['total']}",
                  help="Combined weighted score across all dimensions (higher = better)")

    st.markdown(f"**{report['reason']}**")

    # Side by side: table + radar
    cl, cr = st.columns([1, 1])

    with cl:
        st.markdown(
            "*Note: the total score is a weighted sum of the sub-scores below.*")
        rows = []
        wmap = {"predicted_return": 3, "volatility": 2,
                "model_confidence": 2, "sentiment": 2, "price_trend": 1}
        for dk, dd in sc.items():
            w = wmap.get(dk, 1)
            lab = dd["label"]
            norm_a = dd.get("norm_a", chr(8212))
            norm_b = dd.get("norm_b", chr(8212))
            stars_a = dd.get("stars_a", chr(8212))
            stars_b = dd.get("stars_b", chr(8212))
            ww = dd.get("winner")
            if ww == "a":
                better = ta
                pts = f"+{w}"
            elif ww == "b":
                better = tb
                pts = f"+{w}"
            else:
                better = "Tie"
                pts = f"+-{w/2}"
            rows.append({
                "Dimension": lab,
                ta: f"{stars_a}",
                tb: f"{stars_b}",
                "Better": better,
                "Pts (Weight)": pts,
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(
            "Risk (Volatility): historical std dev of daily returns | Model Confidence: based on our LSTM model backtest MSE")

    with cr:
        fig = _build_radar_chart(report)
        st.plotly_chart(fig, use_container_width=True)

    # Prediction chart (full width)
    da = report["data_a"]
    db = report["data_b"]
    pa = da.get("predicted_price_7d")
    pb = db.get("predicted_price_7d")
    if pa and pb:
        days = list(range(1, 8))
        pa_pct = [(p / pa[0] - 1) * 100 for p in pa]
        pb_pct = [(p / pb[0] - 1) * 100 for p in pb]
        f2 = go.Figure()
        f2.add_trace(go.Scatter(x=days, y=pa_pct, mode="lines+markers", name=ta,
                                line=dict(color="#4C9BE8", width=2), marker=dict(size=6)))
        f2.add_trace(go.Scatter(x=days, y=pb_pct, mode="lines+markers", name=tb,
                                line=dict(color="#FF7F50", width=2), marker=dict(size=6)))
        f2.update_layout(
            title="7-Day Forecast Comparison",
            xaxis_title="Day", yaxis_title="Cumulative Return (%)",
            template="plotly_dark", height=340,
            margin=dict(l=0, r=0, t=40, b=0),
            legend=dict(orientation="h", yanchor="bottom",
                        y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(f2, use_container_width=True)


# ROUTER
if st.session_state.page == "detail" and st.session_state.selected_ticker:
    render_detail_page(st.session_state.selected_ticker)
elif st.session_state.page == "compare":
    render_compare_page()
else:
    render_watchlist_page()
