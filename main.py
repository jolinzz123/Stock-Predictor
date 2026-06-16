import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import timedelta

from data_fetcher import fetch_stock_data, get_stock_info
from predictor import run_prediction
from news_analyzer import get_news_sentiment, generate_recommendation
import cache_manager

WATCHLIST = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN", "TSLA",
    "TSM", "AMD", "BABA", "PDD", "JD", "BIDU",
    "SPY", "QQQ", "JPM", "BRK-B", "NFLX", "DIS", "ENPH",
]

# ── Page routing ────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "watchlist"
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = None


@st.cache_data(ttl=900)
def _load_watchlist():
    rows = []
    for t in WATCHLIST:
        try:
            df_w = fetch_stock_data(t, period="3mo")
            info_w = get_stock_info(t)
            close = df_w["Close"].values.astype(float)
            prev = close[-2] if len(close) >= 2 else close[-1]
            curr = close[-1]
            rows.append({
                "ticker": t,
                "name": info_w["name"][:24],
                "price": curr,
                "chg": curr - prev,
                "pct": (curr - prev) / prev * 100,
                "open": float(df_w["Open"].values[-1]),
                "high": float(df_w["High"].values[-1]),
                "low":  float(df_w["Low"].values[-1]),
                "prev": prev,
                "close_arr": close,
            })
        except Exception:
            pass
    return rows


def _sparkline_svg(prices, width=120, height=40):
    if len(prices) < 2:
        return ""
    mn, mx = float(prices.min()), float(prices.max())
    rng = mx - mn if mx != mn else 1.0
    ys = [(1 - (p - mn) / rng) * (height - 4) + 2 for p in prices]
    xs = [i * width / (len(prices) - 1) for i in range(len(prices))]
    color = "#2ECC71" if prices[-1] >= prices[0] else "#FF4B4B"
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<polyline points="{pts}" fill="none" stroke="{color}" '
        f'stroke-width="1.5" stroke-linejoin="round"/></svg>'
    )


def _watchlist_html(rows):
    css = """
    <style>
    .wl-table{width:100%;border-collapse:collapse;font-size:13px;}
    .wl-table th{text-align:right;color:#888;font-weight:500;padding:6px 12px;border-bottom:1px solid #2a2a3a;}
    .wl-table th:first-child{text-align:left;}
    .wl-table td{padding:9px 12px;border-bottom:1px solid #16192a;text-align:right;vertical-align:middle;}
    .wl-table td:first-child{text-align:left;}
    .wl-table tr:hover td{background:#1a1f2e;}
    .wl-up{color:#2ECC71;} .wl-dn{color:#FF4B4B;}
    .wl-tk{font-weight:700;font-size:14px;} .wl-cn{color:#888;font-size:11px;}
    </style>"""
    header = (
        "<table class='wl-table'><thead><tr>"
        "<th>Name</th><th>Price</th><th>Change</th><th>% Change</th>"
        "<th>Open</th><th>High</th><th>Low</th><th>Prev</th><th>60D Trend</th>"
        "</tr></thead><tbody>"
    )
    body = ""
    for r in rows:
        cls = "wl-up" if r["chg"] >= 0 else "wl-dn"
        sign = "+" if r["chg"] >= 0 else ""
        body += (
            f"<tr>"
            f"<td><span class='wl-tk'>{r['ticker']}</span><br>"
            f"<span class='wl-cn'>{r['name']}</span></td>"
            f"<td>{r['price']:.2f}</td>"
            f"<td class='{cls}'>{sign}{r['chg']:.2f}</td>"
            f"<td class='{cls}'>{sign}{r['pct']:.2f}%</td>"
            f"<td>{r['open']:.2f}</td><td>{r['high']:.2f}</td>"
            f"<td>{r['low']:.2f}</td><td>{r['prev']:.2f}</td>"
            f"<td>{r['svg']}</td></tr>"
        )
    return css + header + body + "</tbody></table>"


# ═══════════════════════════════════════════════════════════
# Watchlist page (original design, unchanged)
# ═══════════════════════════════════════════════════════════

def render_watchlist_page():
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

    # ── Input ──────────────────────────────────────────────
    _prefill  = st.session_state.pop("prefill", "AAPL")
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
        run = st.button("Predict", type="primary", use_container_width=True) or _auto_run

    if run and ticker:
        st.session_state.selected_ticker = ticker
        st.session_state.page = "detail"
        st.rerun()

    # ── Watchlist table ────────────────────────────────────
    with st.spinner("Loading market data..."):
        wl_rows = _load_watchlist()

    if wl_rows:
        st.markdown("### Watchlist")
        btn_cols = st.columns(min(len(wl_rows), 10))
        for i, r in enumerate(wl_rows):
            with btn_cols[i % 10]:
                if st.button(r["ticker"], key=f"wl_{r['ticker']}", use_container_width=True):
                    st.session_state.selected_ticker = r["ticker"]
                    st.session_state.page = "detail"
                    st.rerun()

        display_rows = [{**r, "svg": _sparkline_svg(r["close_arr"][-60:])} for r in wl_rows]
        st.markdown(_watchlist_html(display_rows), unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# Detail page
# ═══════════════════════════════════════════════════════════

def render_detail_page(ticker: str):
    # ── Back navigation ───────────────────────────────────
    if st.button("← Back to Watchlist"):
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

    # ── Load from cache or train ──────────────────────────
    cached = cache_manager.load(ticker)

    if cached:
        df     = cached["df"]
        info   = cached["info"]
        result = cached["result"]
        st.success("Loaded from cache — results are ready instantly!")
    else:
        with st.spinner(f"Fetching 2-year data for {ticker}..."):
            try:
                df = fetch_stock_data(ticker)
                info = get_stock_info(ticker)
            except ValueError as e:
                st.error(str(e))
                st.stop()

        st.markdown("### Training LSTM Model")
        progress_bar = st.progress(0)
        status_text = st.empty()

        def on_epoch(epoch, total):
            progress_bar.progress(epoch / total)
            status_text.text(f"Epoch {epoch}/{total}")

        result = run_prediction(df, future_days=7, epoch_callback=on_epoch)

        progress_bar.progress(1.0)
        status_text.success("Model training complete!")
        cache_manager.save(ticker, {"df": df, "info": info, "result": result})

    prices = df["Close"].values.astype(float)
    dates = df.index.tz_localize(None) if df.index.tzinfo else df.index

    currency = info["currency"]
    current_price = info["current_price"]

    # ── Top metric cards ──────────────────────────────────
    st.subheader(f"{info['name']}  ({ticker})")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Current Price", f"{currency} {current_price:.2f}" if current_price else "N/A")
    m2.metric("Data Points", f"{len(prices)} days")
    m3.metric("2Y High", f"{currency} {prices.max():.2f}")
    m4.metric("2Y Low", f"{currency} {prices.min():.2f}")

    # ── K-line (Candlestick) chart ────────────────────────
    st.divider()
    st.subheader("K-Line Chart")

    fig_kline = _build_candlestick(ticker, df, currency)
    st.plotly_chart(fig_kline, use_container_width=True)

    test_preds = result["test_preds"]
    test_preds_7d = np.array(result["test_preds_7d"])
    test_start = result["test_start_idx"]
    train_end = result["train_end_idx"]
    future_preds = result["future_preds"]

    # Extend with days 2-7 of the last test window to fill the trailing gap
    test_preds = np.concatenate([test_preds, test_preds_7d[-1, 1:]])
    test_dates = dates[test_start : test_start + len(test_preds)]

    # ── News sentiment ────────────────────────────────────
    with st.spinner("Fetching news sentiment..."):
        news_result = get_news_sentiment(ticker)

    # ── 7-day forecast chart ──────────────────────────────
    last_date = pd.Timestamp(dates[-1])
    future_dates = pd.bdate_range(start=last_date + timedelta(days=1), periods=7)

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=dates[-60:], y=prices[-60:],
        mode="lines", name="Last 60 Days (Actual)",
        line=dict(color="#4C9BE8", width=1.5),
    ))
    fig3.add_trace(go.Scatter(
        x=[dates[-1], future_dates[0]],
        y=[prices[-1], future_preds[0]],
        mode="lines", showlegend=False,
        line=dict(color="#2ECC71", width=1, dash="dot"),
    ))
    fig3.add_trace(go.Scatter(
        x=future_dates, y=future_preds,
        mode="lines+markers", name="7-Day Forecast",
        line=dict(color="#2ECC71", width=2),
        marker=dict(size=5, symbol="triangle-up"),
    ))
    fig3.update_layout(
        title="7-Day Price Forecast",
        xaxis_title="Date", yaxis_title=f"Price ({currency})",
        template="plotly_dark", height=380,
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ── Forecast table ────────────────────────────────────
    st.subheader("7-Day Forecast Details")
    prev_prices = [prices[-1]] + list(future_preds[:-1])
    forecast_df = pd.DataFrame({
        "Date": future_dates.strftime("%Y-%m-%d"),
        f"Predicted Price ({currency})": [f"{p:.2f}" for p in future_preds],
        "Change": [
            f"{(future_preds[i] - prev_prices[i]) / prev_prices[i] * 100:+.2f}%"
            for i in range(7)
        ],
    })
    st.dataframe(forecast_df, use_container_width=True, hide_index=True)

    st.caption("Disclaimer: This prediction is for educational purposes only and does not constitute investment advice.")

    # ── Historical closing price ──────────────────────────
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=dates, y=prices,
        mode="lines", name="Close",
        line=dict(color="#4C9BE8", width=1.5),
        fill="tozeroy", fillcolor="rgba(76,155,232,0.08)",
    ))
    fig1.update_layout(
        title="Historical Closing Price (2 Years)",
        xaxis_title="Date", yaxis_title=f"Price ({currency})",
        template="plotly_dark", height=380,
        margin=dict(l=0, r=0, t=40, b=0),
    )
    st.plotly_chart(fig1, use_container_width=True)

    # ── Actual vs Predicted ───────────────────────────────
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=dates, y=prices,
        mode="lines", name="Actual",
        line=dict(color="#4C9BE8", width=1.5),
    ))
    fig2.add_trace(go.Scatter(
        x=test_dates, y=test_preds,
        mode="lines", name="Predicted (test set)",
        line=dict(color="#FF7F50", width=1.5),
    ))
    fig2.add_vline(
        x=dates[train_end],
        line_dash="dot", line_color="gray",
        annotation_text="Train / Test split",
        annotation_position="top left",
    )
    fig2.update_layout(
        title="Actual vs Predicted (Historical)",
        xaxis_title="Date", yaxis_title=f"Price ({currency})",
        template="plotly_dark", height=400,
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig2, use_container_width=True)

    # ── News-Based Trend Analysis ─────────────────────────
    st.divider()
    st.subheader("📰 News-Based Short-Term Analysis")

    rec = generate_recommendation(current_price, list(future_preds), news_result)

    # Recommendation badge
    badge_html = f"""
    <div style="
        display:inline-block;
        background:{rec['color']};
        color:#111;
        font-size:1.5rem;
        font-weight:700;
        padding:0.35em 1.1em;
        border-radius:8px;
        letter-spacing:0.05em;
        margin-bottom:0.5rem;
    ">{rec['signal']}</div>
    """
    st.markdown(badge_html, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Combined Score", f"{rec['combined_score']:+.2f}", help="Range −1 (bearish) to +1 (bullish)")
    c2.metric("LSTM 7-Day Forecast", f"{rec['price_change_pct']:+.2f}%")
    c3.metric("News Sentiment", news_result["sentiment_label"],
              delta=f"{news_result['aggregate_score']:+.2f}")

    st.markdown(rec["rationale"])

    # News articles table
    articles = news_result["articles"]
    if articles:
        st.markdown("#### Recent News")
        LABEL_ICON = {
            "Very Positive": "🟢",
            "Positive":      "🟢",
            "Neutral":       "⚪",
            "Negative":      "🔴",
            "Very Negative": "🔴",
        }
        rows = []
        for a in articles:
            icon = LABEL_ICON.get(a["sentiment_label"], "⚪")
            title_link = f"[{a['title']}]({a['url']})" if a["url"] else a["title"]
            rows.append({
                "Title": title_link,
                "Source": a["publisher"],
                "Published": a["published_at"],
                "Sentiment": f"{icon} {a['sentiment_label']} ({a['sentiment_score']:+.2f})",
            })
        news_df = pd.DataFrame(rows)
        st.dataframe(news_df, use_container_width=True, hide_index=True)
    else:
        st.info("No recent news articles found for this ticker.")


# ═══════════════════════════════════════════════════════════
# K-line chart builder
# ═══════════════════════════════════════════════════════════

def _build_candlestick(ticker: str, df: pd.DataFrame, currency: str) -> go.Figure:
    """Build a candlestick chart with SMA overlays and range selector."""
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="OHLC",
        increasing=dict(line=dict(color="#2ECC71", width=1), fillcolor="#2ECC71"),
        decreasing=dict(line=dict(color="#FF4B4B", width=1), fillcolor="#FF4B4B"),
        showlegend=True,
    ))

    # SMA 20
    sma20 = df["Close"].rolling(20).mean()
    fig.add_trace(go.Scatter(
        x=df.index, y=sma20,
        mode="lines", name="SMA 20",
        line=dict(color="#FFA500", width=1.2),
    ))

    # SMA 50
    sma50 = df["Close"].rolling(50).mean()
    fig.add_trace(go.Scatter(
        x=df.index, y=sma50,
        mode="lines", name="SMA 50",
        line=dict(color="#DDA0FF", width=1.2),
    ))

    fig.update_layout(
        title=f"{ticker} — Candlestick Chart",
        xaxis_title="Date",
        yaxis_title=f"Price ({currency})",
        template="plotly_dark",
        height=500,
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_rangeslider_visible=True,
        dragmode="zoom",
        hovermode="x unified",
    )

    # Range selector buttons
    fig.update_xaxes(
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1M", step="month", stepmode="backward"),
                dict(count=3, label="3M", step="month", stepmode="backward"),
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(step="all", label="All"),
            ]),
            bgcolor="#1a1f2e",
            activecolor="#4C9BE8",
            font=dict(color="#cccccc"),
        ),
    )

    return fig


# ═══════════════════════════════════════════════════════════
# Page config + route dispatch
# ═══════════════════════════════════════════════════════════

st.set_page_config(page_title="Stock Predictor", page_icon="static/favicon.svg", layout="wide")

st.markdown("""
<style>
.block-container { padding-top: 4rem !important; }
</style>
""", unsafe_allow_html=True)

if st.session_state.page == "detail" and st.session_state.selected_ticker:
    render_detail_page(st.session_state.selected_ticker)
else:
    render_watchlist_page()
