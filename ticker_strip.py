import streamlit as st
from data_fetcher import fetch_stock_data
from theme import get_tokens

STRIP_TICKERS = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN", "TSLA",
    "TSM", "AMD", "BABA", "PDD", "JD", "BIDU",
    "SPY", "QQQ", "JPM", "BRK-B", "NFLX", "DIS", "ENPH",
    "ORCL", "CRM", "ADBE", "INTC", "IBM", "QCOM", "TXN",
    "V", "MA", "PYPL", "UBER", "ABNB", "SHOP", "SQ",
    "KO", "PEP", "MCD", "NKE", "SBUX", "COST", "WMT",
    "XOM", "CVX", "BAC", "WFC", "GS", "PFE", "JNJ",
    "BA", "GE",
]


@st.cache_data(ttl=300)
def _load_strip_data():
    rows = []
    for t in STRIP_TICKERS:
        try:
            df_t = fetch_stock_data(t, period="1mo")
            close = df_t["Close"].values.astype(float)
            prev = close[-2] if len(close) >= 2 else close[-1]
            curr = close[-1]
            pct = (curr - prev) / prev * 100
            rows.append({
                "ticker": t,
                "price": curr,
                "pct": pct,
                "close_arr": close[-15:],
            })
        except Exception:
            continue
    return rows


def _mini_sparkline(prices, width=46, height=20, color="#2ECC71"):
    """draw a mini trend chart for marquee"""
    if len(prices) < 2:
        return ""
    mn, mx = float(prices.min()), float(prices.max())
    rng = mx - mn if mx != mn else 1.0
    ys = [(1 - (p - mn) / rng) * (height - 4) + 2 for p in prices]
    xs = [i * width / (len(prices) - 1) for i in range(len(prices))]
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'style="vertical-align:middle; margin-left:8px;">'
        f'<polyline points="{pts}" fill="none" stroke="{color}" '
        f'stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"/></svg>'
    )


def render_ticker_strip():
    T = get_tokens()  # take the color follow to current theme (dark/light)

    rows = _load_strip_data()
    if not rows:
        return

    items_html = ""
    for r in rows:
        is_up = r["pct"] >= 0
        color = T["accent_green"] if is_up else T["accent_red"]
        arrow = "▲" if is_up else "▼"
        spark = _mini_sparkline(r["close_arr"], color=color)
        items_html += (
            f"<span style='margin-right:42px; white-space:nowrap; display:inline-flex; align-items:center;'>"
            f"<b style='color:{T['text_primary']}; font-weight:700;'>{r['ticker']}</b>"
            f"<span style='color:{color}; margin-left:8px; font-weight:600;'>"
            f"{r['price']:.2f} {arrow} {abs(r['pct']):.2f}%</span>"
            f"{spark}"
            f"</span>"
        )

    full_content = items_html + items_html

    html = f"""
    <div style="overflow:hidden; white-space:nowrap; background:{T['bg_card']};
                border:1px solid {T['border']}; padding:10px 0; border-radius:8px;
                margin-bottom:14px; box-shadow:{T['shadow']};">
        <div style="display:inline-block; animation: ticker-scroll 140s linear infinite;">
            {full_content}
        </div>
    </div>
    <style>
        @keyframes ticker-scroll {{
            0%   {{ transform: translateX(0); }}
            100% {{ transform: translateX(-50%); }}
        }}
    </style>
    """
    st.markdown(html, unsafe_allow_html=True)