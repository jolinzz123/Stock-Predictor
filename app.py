import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import timedelta

from data_fetcher import fetch_stock_data, get_stock_info
from predictor import run_prediction

st.set_page_config(page_title="Stock Predictor", page_icon="📈", layout="wide")

st.title("📈 Stock Price Predictor")
st.markdown("Powered by LSTM · 2-year training window · 7-day forecast")

# ── Input ──────────────────────────────────────────────
col_input, col_btn = st.columns([4, 1])
with col_input:
    ticker = st.text_input(
        "Ticker",
        value="AAPL",
        placeholder="e.g. AAPL, TSLA, 600519.SS, 000858.SZ",
        label_visibility="collapsed",
    ).strip().upper()
with col_btn:
    run = st.button("Predict", type="primary", use_container_width=True)

if not run:
    st.info("Enter a ticker symbol and click Predict.")
    st.stop()

if not ticker:
    st.error("Please enter a ticker symbol.")
    st.stop()

# ── Fetch data ─────────────────────────────────────────
with st.spinner(f"Fetching 2-year data for {ticker}..."):
    try:
        df = fetch_stock_data(ticker)
        info = get_stock_info(ticker)
    except ValueError as e:
        st.error(str(e))
        st.stop()

prices = df["Close"].values.astype(float)
dates = df.index.tz_localize(None) if df.index.tzinfo else df.index

currency = info["currency"]
current_price = info["current_price"]

# ── Metric cards ───────────────────────────────────────
st.subheader(f"{info['name']}  ({ticker})")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Current Price", f"{currency} {current_price:.2f}" if current_price else "N/A")
m2.metric("Data Points", f"{len(prices)} days")
m3.metric("2Y High", f"{currency} {prices.max():.2f}")
m4.metric("2Y Low", f"{currency} {prices.min():.2f}")

# ── Chart 1: Historical closing price ──────────────────
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

# ── Train model ────────────────────────────────────────
st.markdown("### Training LSTM Model")
progress_bar = st.progress(0)
status_text = st.empty()

def on_epoch(epoch, total):
    progress_bar.progress(epoch / total)
    status_text.text(f"Epoch {epoch}/{total}")

result = run_prediction(prices, future_days=7, epoch_callback=on_epoch)

progress_bar.progress(1.0)
status_text.success("Model training complete!")

test_preds = result["test_preds"]
test_start = result["test_start_idx"]
train_end = result["train_end_idx"]
future_preds = result["future_preds"]

test_dates = dates[test_start:]

# ── Chart 2: Actual vs Predicted ───────────────────────
fig2 = go.Figure()
fig2.add_trace(go.Scatter(
    x=dates, y=prices,
    mode="lines", name="Actual",
    line=dict(color="#4C9BE8", width=1.5),
))
fig2.add_trace(go.Scatter(
    x=test_dates, y=test_preds,
    mode="lines", name="Predicted (test set)",
    line=dict(color="#FF7F50", width=1.5, dash="dash"),
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

# ── Chart 3: 7-day future forecast ────────────────────
last_date = pd.Timestamp(dates[-1])
future_dates = pd.bdate_range(start=last_date + timedelta(days=1), periods=7)

fig3 = go.Figure()
fig3.add_trace(go.Scatter(
    x=dates[-60:], y=prices[-60:],
    mode="lines", name="Last 60 Days (Actual)",
    line=dict(color="#4C9BE8", width=1.5),
))
# Bridge line connecting last actual to first forecast point
fig3.add_trace(go.Scatter(
    x=[dates[-1], future_dates[0]],
    y=[prices[-1], future_preds[0]],
    mode="lines", showlegend=False,
    line=dict(color="#2ECC71", width=1, dash="dot"),
))
fig3.add_trace(go.Scatter(
    x=future_dates, y=future_preds,
    mode="lines+markers", name="7-Day Forecast",
    line=dict(color="#2ECC71", width=2, dash="dot"),
    marker=dict(size=8, symbol="circle"),
))
fig3.update_layout(
    title="7-Day Price Forecast",
    xaxis_title="Date", yaxis_title=f"Price ({currency})",
    template="plotly_dark", height=380,
    margin=dict(l=0, r=0, t=40, b=0),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig3, use_container_width=True)

# ── Forecast table ─────────────────────────────────────
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
