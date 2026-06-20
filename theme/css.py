import streamlit as st

from .tokens import get_tokens, get_is_dark


def inject_global_css() -> None:
    T = get_tokens()
    is_dark = get_is_dark()

    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Page background sync ─ */
[data-testid="stAppViewContainer"],
[data-testid="stApp"],
[data-testid="stMain"],
section[data-testid="stSidebar"],
.main .block-container {{
    background-color: {T["bg_base"]} !important;
    color: {T["text_primary"]} !important;
}}
[data-testid="stHeader"] {{
    background-color: {T["bg_base"]} !important;
}}
[data-testid="stBottomBlockContainer"] {{
    background-color: {T["bg_base"]} !important;
}}

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
    height: 100% !important;
    box-sizing: border-box !important;
}}
[data-testid="stMetric"]::after {{
    display: none !important;
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
    font-size: 1.45rem !important;
    font-weight: 700 !important;
    font-family: 'JetBrains Mono', monospace !important;
    letter-spacing: -0.03em !important;
}}

/* ── Column alignment ─ */
[data-testid="stHorizontalBlock"] {{
    align-items: stretch !important;
    gap: 0.5rem !important;
}}
[data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) {{
    align-items: end !important;
}}
[data-testid="stHorizontalBlock"] [data-testid="stTextInput"],
[data-testid="stHorizontalBlock"] [data-testid="stButton"] {{
    margin-top: 0 !important;
    margin-bottom: 0 !important;
}}

/* ── Inputs ─ */
[data-testid="stTextInput"] input,
[data-testid="stTextInput"] input[type="text"],
.stTextInput input {{
    background: {T["bg_input"]} !important;
    border: 1px solid {T["border"]} !important;
    border-radius: 10px !important;
    color: {T["text_primary"]} !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.92rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.06em !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    height: 44px !important;
    min-height: 44px !important;
    max-height: 44px !important;
    line-height: 44px !important;
    box-sizing: border-box !important;
    transition: border-color 0.2s, box-shadow 0.2s;
}}
[data-testid="stTextInput"] label,
.stTextInput label {{
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}}
[data-testid="stTextInput"] div[data-testid="InputInstructions"],
[data-testid="stTextInput"] .stTextInput-instructions {{
    display: none !important;
}}

/* ── Primary button height match ─ */
[data-testid="stButton"] button[kind="primary"],
[data-testid="baseButton-primary"] {{
    min-height: 44px !important;
    max-height: 44px !important;
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
    padding: 0 1rem !important;
    height: 44px !important;
    min-height: 44px !important;
    max-height: 44px !important;
    line-height: 44px !important;
    box-sizing: border-box !important;
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
    border: 2px solid {T["border"]} !important;
    border-radius: 10px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.83rem !important;
    font-weight: 600 !important;
    transition: border-color 0.18s, color 0.18s, background 0.18s, box-shadow 0.18s !important;
}}
[data-testid="stButton"] button[kind="secondary"]:hover {{
    border-color: {T["accent_blue"]} !important;
    color: {T["accent_blue"]} !important;
    background: rgba(76,155,232,0.08) !important;
    box-shadow: 0 0 0 3px rgba(76,155,232,0.25) !important;
}}
[data-testid="stButton"] button[kind="secondary"]:focus,
[data-testid="stButton"] button[kind="secondary"]:active,
[data-testid="stButton"] button[kind="secondary"]:focus-visible,
[data-testid="stButton"] button:focus,
[data-testid="stButton"] button:active,
[data-testid="stButton"] button:focus-visible,
[data-testid="baseButton-secondary"]:focus,
[data-testid="baseButton-secondary"]:active {{
    border-color: {T["accent_blue"]} !important;
    border-width: 2px !important;
    box-shadow: 0 0 0 4px rgba(76,155,232,0.45), 0 0 20px rgba(76,155,232,0.30) !important;
    background: rgba(76,155,232,0.12) !important;
    outline: none !important;
    color: {T["accent_blue"]} !important;
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

/* ── Dataframe ─ */
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
[data-testid="stDataFrame"] table {{
    background: {T["bg_surface"]} !important;
    border-collapse: collapse !important;
    width: 100% !important;
}}
[data-testid="stDataFrame"] thead th {{
    background: {T["bg_surface"]} !important;
    color: {T["text_primary"]} !important;
    border-bottom: 1px solid {T["border"]} !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    padding: 0.6rem 1rem !important;
}}
[data-testid="stDataFrame"] tbody td {{
    background: {T["bg_card"]} !important;
    color: {T["text_primary"]} !important;
    border-bottom: 1px solid {T["border"]} !important;
    padding: 0.55rem 1rem !important;
    font-size: 0.84rem !important;
}}
[data-testid="stDataFrame"] tbody tr:hover td {{
    background: {T["bg_card_hover"]} !important;
}}
[data-testid="stDataFrame"] tbody tr:last-child td {{
    border-bottom: none !important;
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
    padding: 0;
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
	/* ── Row links (full-cell clickable) ─ */
	.wl-cell-link {{
	    display: block;
	    width: 100%;
	    height: 100%;
	    padding: 0.75rem 1rem;
	    text-decoration: none !important;
	    color: inherit !important;
	    font-family: inherit;
	    font-size: inherit;
	    font-weight: inherit;
	}}
	.wl-cell-link:hover {{
	    color: inherit !important;
	    text-decoration: none !important;
	}}

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

/* ── Forecast summary cards ─ */
.forecast-summary-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
    margin-bottom: 1rem;
}}
.fsc {{
    background: {T["bg_card"]};
    border: 1px solid {T["border"]};
    border-radius: 10px;
    padding: 1.1rem 1.4rem;
    transition: border-color 0.2s, box-shadow 0.2s;
}}
.fsc:hover {{
    border-color: {T["border_accent"]}55;
    box-shadow: {T["shadow"]};
}}
.fsc-label {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: {T["text_secondary"]};
    margin-bottom: 0.55rem;
}}
.fsc-value {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.45rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: {T["text_primary"]};
    display: flex;
    align-items: center;
    gap: 0.4rem;
    line-height: 1.2;
}}

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
    padding: 1.8rem 1.2rem 0.4rem;
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
