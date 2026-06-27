import datetime
from datetime import timedelta
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from data_fetcher import fetch_stock_data, get_stock_info
from predictor import run_prediction
from ticker_strip import render_ticker_strip
from news_analyzer import (
    extract_market_drivers,
    get_news_sentiment,
    get_ticker_sentiment_context,
)
from recommendation import generate_recommendation
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


def _build_recommendation_text(rec: dict, news_result: dict, coverage_note: str = "") -> str:
    signal = rec["signal"]
    price_pct = rec["price_change_pct"]
    score = rec["combined_score"]
    pos = news_result["positive_count"]
    neg = news_result["negative_count"]
    neu = news_result["neutral_count"]
    total = pos + neg + neu

    # ── 1. Price movement phrase ─────────────────────────────────────────────
    abs_pct = abs(price_pct)
    if abs_pct < 0.05:                          # essentially flat
        price_phrase = "minimal price movement (<b>~0%</b>)"
    elif price_pct > 0:
        price_phrase = f"a rise of <b>+{abs_pct:.1f}%</b>"
    else:
        price_phrase = f"a decline of <b>−{abs_pct:.1f}%</b>"

    # ── 2. Signal strength descriptor ───────────────────────────────────────
    score_desc = (
        "strongly bullish" if score > 0.5 else
        "moderately bullish" if score > 0.15 else
        "roughly neutral" if score > -0.15 else
        "moderately bearish" if score > -0.5 else
        "strongly bearish"
    )

    # ── 3. News flow sentence ────────────────────────────────────────────────
    if total == 0:
        news_sent = "No recent news articles were found for this ticker."
    elif total < 4:
        news_sent = (
            f"Only {total} recent article{'s' if total > 1 else ''} found — "
            f"sentiment data is thin; the price forecast carries more weight here."
        )
    elif pos > neg and pos > neu:
        news_sent = (
            f"News flow leans positive — {pos} of {total} articles carry a "
            f"constructive tone, supporting near-term momentum."
        )
    elif neg > pos and neg > neu:
        news_sent = (
            f"News flow is cautionary — {neg} of {total} articles carry a "
            f"negative tone, which weighs on the short-term outlook."
        )
    elif pos > neg:                             # pos ≈ neu, no strong lean
        news_sent = (
            f"News flow is mixed but slightly positive ({pos} positive, "
            f"{neu} neutral, {neg} negative) — no strong directional signal."
        )
    elif neg > pos:
        news_sent = (
            f"News flow is mixed but slightly negative ({neg} negative, "
            f"{neu} neutral, {pos} positive) — no strong directional signal."
        )
    else:
        news_sent = (
            f"News flow is evenly mixed — {pos} positive, {neu} neutral, "
            f"{neg} negative — offering no clear directional edge."
        )

    # ── 4. Signal-specific action hint ──────────────────────────────────────
    if signal == "STRONG BUY":
        action = "both the forecast and sentiment align bullishly — a high-conviction entry signal"
    elif signal == "BUY":
        action = "conditions favour an entry; confirm with your own analysis before acting"
    elif signal == "HOLD":
        action = "no decisive edge either way — wait for a stronger catalyst before committing"
    elif signal == "REDUCE":
        action = "consider trimming exposure and reassessing if conditions deteriorate further"
    else:  # AVOID
        action = "both signals are bearish — avoid new positions until the outlook improves"

    coverage_str = f" {coverage_note}" if coverage_note else ""
    return (
        f"The model projects {price_phrase} over the next 7 trading days, "
        f"with the combined signal reading as <strong>{score_desc}</strong> "
        f"(score {score:+.2f}). "
        f"{news_sent}"
        f"{coverage_str} "
        f"Signal: <strong>{signal}</strong> — {action}."
    )


def render_detail_page(ticker: str) -> None:
    T = get_tokens()
    render_ticker_strip()
    render_nav(show_back=True)

    # ── Load data / cache ────────────────────────────────────────────────────
    cached = cache_manager.load(ticker)
    news_result = None
    if cached:
        df = cached["df"]
        info = cached["info"]
        result = cached["result"]
        news_result = cached.get("news_result")
    else:
        with st.spinner(f"Fetching 2-year data for {ticker}…"):
            try:
                df = fetch_stock_data(ticker)
                info = get_stock_info(ticker)
            except ValueError as e:
                st.error(str(e))
                return

        sentiment_context = get_ticker_sentiment_context(ticker, df.index)
        news_result = sentiment_context["news_result"]

        progress_bar = st.progress(0)
        progress_text = st.empty()

        def _on_epoch(epoch, total):
            progress_bar.progress(epoch / total)
            progress_text.caption(f"Training model... epoch {epoch}/{total}")

        result = run_prediction(
            df,
            future_days=7,
            epoch_callback=_on_epoch,
            sentiment_series=sentiment_context["sentiment_series"],
        )
        progress_bar.empty()
        progress_text.empty()
        cache_manager.save(
            ticker,
            {
                "df": df,
                "info": info,
                "result": result,
                "news_result": news_result,
            },
        )

    prices = df["Close"].to_numpy(dtype=float)

    if isinstance(df.index, pd.DatetimeIndex):
        if df.index.tz is not None:
            dates = df.index.tz_convert(None)
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
    st.plotly_chart(fig3, use_container_width=True)

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

    # ── Actual vs predicted (60d history + last 7-day backtest window) ────────
    rail_header("Model fit — actual vs predicted",
                icon("layers", 13, T["text_muted"]))

    bt_horizon = int(test_preds_7d.shape[1])
    bt_anchor_idx = len(dates) - bt_horizon - 1
    bt_anchor_date = dates[bt_anchor_idx]
    bt_anchor_price = prices[bt_anchor_idx]
    bt_dates_7d = dates[bt_anchor_idx + 1: bt_anchor_idx + 1 + bt_horizon]
    bt_actual_7d = y_test[-1]
    bt_pred_7d = result.get("backtest_preds_7d", test_preds_7d[-1])

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=dates[-60:], y=prices[-60:],
        mode="lines", name="Last 60 days",
        line=dict(color=T["accent_blue"], width=1.6),
        hovertemplate="<b>%{x|%b %d %Y}</b><br>%{y:.2f}<extra></extra>",
    ))
    fig2.add_trace(go.Scatter(
        x=[bt_anchor_date] + list(bt_dates_7d),
        y=[bt_anchor_price] + list(bt_actual_7d),
        mode="lines+markers", name="Actual (7d)",
        line=dict(color=T["accent_blue"], width=1.6),
        marker=dict(size=6, color=T["accent_blue"]),
        hovertemplate="<b>%{x|%b %d %Y}</b><br>Actual: %{y:.2f}<extra></extra>",
    ))
    fig2.add_trace(go.Scatter(
        x=[bt_anchor_date] + list(bt_dates_7d),
        y=[bt_anchor_price] + list(bt_pred_7d),
        mode="lines+markers", name="Predicted (7d)",
        line=dict(color=T["accent_green"], width=2.2, dash="dot"),
        marker=dict(size=8, symbol="circle", color=T["accent_green"],
                    line=dict(color=T["bg_base"], width=2)),
        hovertemplate="<b>%{x|%b %d %Y}</b><br>Predicted: %{y:.2f}<extra></extra>",
    ))
    fig2.add_shape(
        type="rect",
        x0=bt_anchor_date, x1=bt_dates_7d[-1],
        y0=0, y1=1, yref="paper",
        fillcolor=T["accent_green"], opacity=0.08,
        layer="below", line_width=0,
    )
    fig2.update_layout(**chart_layout(400))
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # ── K-line chart ─────────────────────────────────────────────────────────
    rail_header("K-line chart — OHLC with SMA overlays",
                icon("candlestick", 13, T["text_muted"]))
    st.plotly_chart(_build_candlestick(df),
                    use_container_width=True)

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
    st.plotly_chart(fig1, use_container_width=True)

    # ── News & sentiment ──────────────────────────────────────────────────────
    st.markdown("<hr/>", unsafe_allow_html=True)
    rail_header("News & sentiment analysis", icon(
        "newspaper", 13, T["text_muted"]))

    with st.spinner("Fetching latest news and analysing sentiment…"):
        if news_result is None:
            news_result = get_news_sentiment(ticker)
        if "error" in news_result:
            st.warning(
                f"News fetch failed: {news_result['error']}. Showing empty sentiment.")
        rec = generate_recommendation(
            current_price, list(future_preds), news_result)

    st.markdown(signal_badge_html(rec), unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Combined score",    f"{rec['combined_score']:+.2f}")
    c2.metric("Forecast return",   f"{rec['price_change_pct']:+.2f}%")
    c3.metric("News sentiment",    news_result["sentiment_label"])
    total_arts = (news_result["positive_count"]
                  + news_result["neutral_count"]
                  + news_result["negative_count"])
    c4.metric("Articles analysed", str(total_arts))

    confidence = float(news_result.get("sentiment_confidence", 0.0))
    conf_pct_f = min(confidence * 100, 100)
    coverage_note = (
        ""  # strong coverage — no need to call it out, let the news sentence speak
        if conf_pct_f >= 60 else
        f"Sentiment is based on a moderate sample ({total_arts} articles) — treat it as directional, not definitive."
        if conf_pct_f >= 30 else
        f"Only {total_arts} recent article{'s' if total_arts != 1 else ''} found — rely more on the price forecast for this signal."
    )

    narrative = _build_recommendation_text(rec, news_result, coverage_note)
    st.markdown(
        f'<div class="rec-box">{narrative}</div>', unsafe_allow_html=True)

    total = total_arts or 1
    pos_pct = news_result["positive_count"] / total * 100
    neu_pct = news_result["neutral_count"] / total * 100
    neg_pct = news_result["negative_count"] / total * 100

    pos_mid = max(6.0, min(94.0, pos_pct / 2))
    neu_mid = max(6.0, min(94.0, pos_pct + neu_pct / 2))
    neg_mid = max(6.0, min(94.0, pos_pct + neu_pct + neg_pct / 2))

    st.markdown(f"""
<div style="margin:0.75rem 0 1.75rem;">
  <div class="sbar-labels" style="position:relative;height:1.4rem;">
    <span style="position:absolute;left:{pos_mid:.2f}%;transform:translateX(-50%);white-space:nowrap;">{news_result["positive_count"]} positive</span>
    <span style="position:absolute;left:{neu_mid:.2f}%;transform:translateX(-50%);white-space:nowrap;">{news_result["neutral_count"]} neutral</span>
    <span style="position:absolute;left:{neg_mid:.2f}%;transform:translateX(-50%);white-space:nowrap;">{news_result["negative_count"]} negative</span>
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
        f"Foresight · ensemble forecasting · yfinance data · Educational use only"
        f"</div>",
        unsafe_allow_html=True,
    )
