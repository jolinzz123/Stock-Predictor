# Stock Price Predictor

A Streamlit web app that uses an LSTM neural network to predict stock prices.

## Features

- Search any stock by ticker symbol (US stocks, A-shares, etc.)
- Display 2-year historical closing price chart
- Train an LSTM model on the historical data with a live progress bar
- Compare actual vs predicted prices on the test set
- Forecast the next 7 trading days using autoregressive prediction

## Setup

```bash
python -m venv .venv
.venv\Scripts\Activate           # Windows
source .venv/bin/activate        # macOS / Linux

pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Tech Stack

| Layer | Library |
|---|---|
| UI | Streamlit |
| Charts | Plotly |
| Model | TensorFlow / Keras (LSTM) |
| Data | yfinance |
| Preprocessing | scikit-learn |
