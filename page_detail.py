import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import datetime
from datetime import timedelta

from data_fetcher import fetch_stock_data, get_stock_info
from predictor import run_prediction
from news_analyzer import get_news_sentiment, generate_recommendation, extract_market_drivers
import cache_manager
from theme import (
    get_tokens, icon, rail_header, chart_layout,
    news_card_html, signal_badge_html, render_nav,
)


def _build_candlestick(df: pd.DataFrame) -> go.Figure:
    T = get_tokens()
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
        margin=dict(l=0, r=0, t=40, b=0),
        modebar=dict(
            orientation="v",
            bgcolor="rgba(0,0,0,0)",
        ),
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
            y=1.06,
        ),
        legend=dict(
            orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5,
        ),
        hovermode="x unified",
        dragmode="zoom",
    )
    fig.update_layout(**layout)
    return fig


def _build_recommendation_text(rec: dict, news_result: dict) -> str:
    signal = rec["signal"]
    price_pct = rec["price_change_pct"]
    score = rec["combined_score"]
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
    T = get_tokens()
    render_nav(show_back=True)

    if st.button("← Back to watchlist", key="back_btn", type="secondary"):
        st.session_state.page = "watchlist"
        st.session_state.selected_ticker = None
        st.rerun()

    # ── Load data / cache ────────────────────────────────────────────────────
    cached = cache_manager.load(ticker)
    if cached:
        df = cached["df"]
        info = cached["info"]
        result = cached["result"]
    else:
        with st.spinner(f"Fetching 2-year data for {ticker}…"):
            try:
                df = fetch_stock_data(ticker)
                info = get_stock_info(ticker)
            except ValueError as e:
                st.error(str(e))
                return

        result = run_prediction(df, future_days=7)
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
  <div class="stock-name">{info["name"]} ({ticker})</div>
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

    # ── Unpack prediction results ─────────────────────────────────────────────
    test_preds = result["test_preds"]
    test_preds_7d = result["test_preds_7d"]
    y_test = result["y_test"]
    test_start = result["test_start_idx"]
    train_end = result["train_end_idx"]
    future_preds = result["future_preds"]
    test_dates = dates[test_start:]
    predicted_return_pct = (
        future_preds[-1] - current_price) / current_price * 100

    # ── 7-day forecast ────────────────────────────────────────────────────────
    rail_header("7-day price forecast",
                icon("chart-line", 13, T["text_muted"]))
    last_date = pd.Timestamp(dates[-1])
    # Forecast starts from today if it is a business day (Mon–Fri),
    # or the next Monday if today is a weekend. Never in the past.
    today = pd.Timestamp(datetime.date.today())
    forecast_start = max(last_date + pd.tseries.offsets.BDay(1), today)
    future_dates = pd.bdate_range(start=forecast_start, periods=7)

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=dates[-60:], y=prices[-60:],
        mode="lines", name="Last 60 days",
        line=dict(color=T["accent_blue"], width=1.6),
        hovertemplate="<b>%{x|%b %d %Y}</b><br>%{y:.2f}<extra></extra>",
    ))
    # Solid green line: bridge from last historical close → first forecast dot
    fig3.add_trace(go.Scatter(
        x=[dates[-1], future_dates[0]],
        y=[prices[-1], future_preds[0]],
        mode="lines", name="7-day forecast",
        line=dict(color=T["accent_green"], width=2.2),
        showlegend=True, hoverinfo="skip",
    ))
    fig3.add_trace(go.Scatter(
        x=list(future_dates),
        y=list(future_preds),
        mode="lines+markers", name="7-day forecast",
        line=dict(color=T["accent_green"], width=2.2),
        marker=dict(size=8, symbol="circle", color=T["accent_green"],
                    line=dict(color=T["bg_base"], width=2)),
        showlegend=False,
        hovertemplate="<b>%{x|%b %d %Y}</b><br>Forecast: %{y:.2f}<extra></extra>",
    ))
    fig3.add_shape(
        type="rect",
        x0=future_dates[0], x1=future_dates[-1],
        y0=0, y1=1, yref="paper",
        fillcolor=T["accent_green"], opacity=0.08,
        layer="below", line_width=0,
    )
    fig3.update_layout(**chart_layout(380))
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Forecast summary metrics ──────────────────────────────────────────────
    rail_header("Forecast summary")
    T = get_tokens()
    ret_color = T["accent_green"] if predicted_return_pct >= 0 else T["accent_red"]
    ret_icon = icon(
        "trending-up" if predicted_return_pct >= 0 else "trending-down",
        16, ret_color,
    )
    st.markdown(f"""
<div class="forecast-summary-grid">
  <div class="fsc">
    <div class="fsc-label">Expected Return — 7 Days</div>
    <div class="fsc-value" style="color:{ret_color};">{ret_icon}&nbsp;{predicted_return_pct:+.2f}%</div>
  </div>
  <div class="fsc">
    <div class="fsc-label">Predicted Price — Day 7</div>
    <div class="fsc-value">{currency}&nbsp;{future_preds[-1]:.2f}</div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)

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

    # ── Actual vs predicted (60d history + last 7-day backtest window) ────────
    rail_header("Model fit — actual vs predicted",
                icon("layers", 13, T["text_muted"]))

    bt_anchor = test_start + len(test_preds) - 1
    bt_7d_end = min(bt_anchor + 8, len(dates))
    bt_dates_7d = dates[bt_anchor + 1 : bt_7d_end]
    if len(bt_dates_7d) < 7:
        bt_dates_7d = pd.bdate_range(
            start=dates[bt_anchor] + timedelta(days=1), periods=7)

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=dates[-60:], y=prices[-60:],
        mode="lines", name="Last 60 days",
        line=dict(color=T["accent_blue"], width=1.6),
        hovertemplate="<b>%{x|%b %d %Y}</b><br>%{y:.2f}<extra></extra>",
    ))
    fig2.add_trace(go.Scatter(
        x=[dates[-1]] + list(bt_dates_7d),
        y=[prices[-1]] + list(y_test[-1]),
        mode="lines+markers", name="Actual (7d)",
        line=dict(color=T["accent_blue"], width=1.6),
        marker=dict(size=6, color=T["accent_blue"]),
        hovertemplate="<b>%{x|%b %d %Y}</b><br>Actual: %{y:.2f}<extra></extra>",
    ))
    fig2.add_trace(go.Scatter(
        x=[dates[-1]] + list(bt_dates_7d),
        y=[prices[-1]] + list(test_preds_7d[-1]),
        mode="lines+markers", name="Predicted (7d)",
        line=dict(color=T["accent_green"], width=2.2, dash="dot"),
        marker=dict(size=8, symbol="circle", color=T["accent_green"],
                    line=dict(color=T["bg_base"], width=2)),
        hovertemplate="<b>%{x|%b %d %Y}</b><br>Predicted: %{y:.2f}<extra></extra>",
    ))
    fig2.add_shape(
        type="rect",
        x0=dates[-1], x1=bt_dates_7d[-1],
        y0=0, y1=1, yref="paper",
        fillcolor=T["accent_green"], opacity=0.08,
        layer="below", line_width=0,
    )
    fig2.update_layout(**chart_layout(400))
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # ── K-line chart ─────────────────────────────────────────────────────────
    rail_header("K-line chart — OHLC with SMA overlays",
                icon("candlestick", 13, T["text_muted"]))
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    st.plotly_chart(_build_candlestick(df),
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
