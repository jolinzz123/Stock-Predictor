# app_web.py
# Flask web interface for the Stock Price Prediction System.
# Flask docs: https://flask.palletsprojects.com/
# News fetching via Google News RSS feed (no API key required):
# https://news.google.com/rss

import os
import io
import base64
import threading
from datetime import datetime

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from flask import Flask, render_template, request, jsonify
import numpy as np
import pandas as pd

from data_fetcher import (fetch_stock_data, preprocess_data, train_test_split_timeseries,
                          fetch_realtime_quotes, fetch_indices_data,
                          get_market_stocks, get_stock_metadata,
                          fetch_gainers_losers, fetch_sector_heatmap,
                          get_sector_groups, get_market_summary)
from news_fetcher import fetch_stock_news, fetch_market_news
from model import build_model, train_model, load_saved_model, MODEL_SAVE_PATH
from predictor import predict_on_test_set, predict_future, calculate_metrics, get_trend_signal
from visualizer import plot_prediction_results, plot_training_loss, plot_future_only

app = Flask(__name__)
_lock = threading.Lock()

LOOK_BACK   = 60
SPLIT_RATIO = 0.8

# ── Ticker resolution ────────────────────────────────────────
# Known tickers that need market suffixes for yfinance
_TICKER_SUFFIX_MAP = {
    # A-share Shanghai (.SS)
    "600519": "600519.SS", "601318": "601318.SS", "603259": "603259.SS",
    "600036": "600036.SS", "601899": "601899.SS", "600900": "600900.SS",
    "600276": "600276.SS", "600809": "600809.SS", "600030": "600030.SS",
    "601398": "601398.SS", "688256": "688256.SS",
    # A-share Shenzhen (.SZ)
    "000858": "000858.SZ", "300750": "300750.SZ", "002594": "002594.SZ",
    "000725": "000725.SZ", "000333": "000333.SZ", "002475": "002475.SZ",
    "300308": "300308.SZ", "300502": "300502.SZ", "300059": "300059.SZ",
    "002415": "002415.SZ", "000001": "000001.SZ", "002230": "002230.SZ",
    "300274": "300274.SZ", "002371": "002371.SZ", "000568": "000568.SZ",
    "300124": "300124.SZ",
    # HK stocks
    "0700": "0700.HK",   "9988": "9988.HK",   "3690": "3690.HK",
    "1810": "1810.HK",   "9618": "9618.HK",   "9999": "9999.HK",
    "1024": "1024.HK",   "2015": "2015.HK",   "1211": "1211.HK",
    "2318": "2318.HK",   "0388": "0388.HK",   "0005": "0005.HK",
    "0883": "0883.HK",   "0941": "0941.HK",   "1398": "1398.HK",
    "2269": "2269.HK",   "9863": "9863.HK",   "9992": "9992.HK",
    "1876": "1876.HK",
}


def _resolve_ticker(ticker: str) -> str:
    """Resolve short ticker codes to full yfinance symbols."""
    # If already has suffix, return as-is
    if "." in ticker:
        return ticker.upper()
    # Check known mappings
    ticker_upper = ticker.upper()
    if ticker_upper in _TICKER_SUFFIX_MAP:
        return _TICKER_SUFFIX_MAP[ticker_upper]
    # If all-numeric, try common suffixes
    if ticker.isdigit():
        if len(ticker) == 4:
            return ticker + ".HK"
        elif len(ticker) == 6:
            if ticker.startswith(("6", "5")):
                return ticker + ".SS"
            else:
                return ticker + ".SZ"
    # US stock or unknown — return as-is
    return ticker_upper


def chart_to_base64(filepath: str) -> str:
    if not os.path.exists(filepath):
        return ""
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")



@app.route("/")
def index():
    return render_template("index.html")


@app.route("/news/<ticker>")
def news(ticker: str):
    """Return latest news articles for a given ticker as JSON."""
    ticker = ticker.strip().upper()
    if len(ticker) > 12:
        return jsonify({"error": "Invalid ticker"}), 400
    articles = fetch_stock_news(ticker)
    return jsonify({"ticker": ticker, "articles": articles,
                    "updated_at": datetime.utcnow().isoformat() + "Z"})


@app.route("/api/news/market")
def api_market_news():
    """Return aggregated general market news from multiple RSS sources."""
    try:
        n = int(request.args.get("n", 20))
        n = max(1, min(n, 50))
    except (TypeError, ValueError):
        n = 20
    articles = fetch_market_news(max_articles=n)
    return jsonify({"articles": articles,
                    "updated_at": datetime.utcnow().isoformat() + "Z"})


@app.route("/predict", methods=["POST"])
def predict():
    data    = request.get_json()
    ticker  = str(data.get("ticker", "")).strip().upper()
    days    = int(data.get("days", 10))
    retrain = bool(data.get("retrain", True))

    if not ticker or len(ticker) < 1 or len(ticker) > 12:
        return jsonify({"error": "Invalid ticker symbol."}), 400
    if not (1 <= days <= 30):
        return jsonify({"error": "Forecast days must be 1–30."}), 400

    # Resolve ticker (e.g. "600519" -> "600519.SS")
    resolved_ticker = _resolve_ticker(ticker)

    with _lock:
        try:
            df = fetch_stock_data(resolved_ticker)
            last_price = float(df['Close'].iloc[-1])

            X, y, scaler = preprocess_data(df, look_back=LOOK_BACK)
            X_train, X_test, y_train, y_test = train_test_split_timeseries(X, y, SPLIT_RATIO)

            if retrain or not os.path.exists(MODEL_SAVE_PATH):
                model = build_model(look_back=LOOK_BACK)
                model, history = train_model(model, X_train, y_train, epochs=30)
                plot_training_loss(history, resolved_ticker)
            else:
                model = load_saved_model()

            test_predicted = predict_on_test_set(model, X_test, scaler)
            test_actual    = scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()
            metrics        = calculate_metrics(test_actual, test_predicted)

            future_prices = predict_future(model, df, scaler, days, LOOK_BACK)
            trend         = get_trend_signal(future_prices)

            assets_dir = os.path.join(os.path.dirname(__file__), "assets")
            plot_prediction_results(df, test_actual, test_predicted,
                                    future_prices, resolved_ticker, LOOK_BACK, SPLIT_RATIO)
            plot_future_only(df, future_prices, resolved_ticker)

            last_date    = pd.to_datetime(df.index[-1])
            future_dates = pd.bdate_range(
                start=last_date + pd.Timedelta(days=1), periods=days)

            forecast_table = []
            prev = last_price
            for i, (price, date) in enumerate(zip(future_prices.tolist(), future_dates), 1):
                change = price - prev
                forecast_table.append({
                    "day":    i,
                    "date":   date.strftime("%d %b %Y"),
                    "price":  f"${price:.2f}",
                    "change": f"+${change:.2f}" if change >= 0 else f"-${abs(change):.2f}",
                    "up":     change >= 0,
                })
                prev = price

            return jsonify({
                "ticker":         resolved_ticker,
                "current_price":  f"${last_price:.2f}",
                "target_price":   f"${future_prices[-1]:.2f}",
                "trend":          trend,
                "rmse":           metrics["RMSE"],
                "mae":            metrics["MAE"],
                "mape":           f"{metrics['MAPE']:.2f}%",
                "forecast":       forecast_table,
                "chart_pred":     chart_to_base64(os.path.join(assets_dir, f"{resolved_ticker}_prediction.png")),
                "chart_forecast": chart_to_base64(os.path.join(assets_dir, f"{resolved_ticker}_forecast.png")),
                "chart_loss":     chart_to_base64(os.path.join(assets_dir, f"{resolved_ticker}_loss.png")),
            })

        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


# ── Real-time data endpoints ──────────────────────────────────

@app.route("/api/quotes", methods=["POST"])
def api_quotes():
    """
    Batch fetch real-time quotes for a list of tickers.
    Request JSON: {"tickers": ["AAPL", "TSLA", ...]}
    Response: {ticker: {price, change, changePercent, name, sector}, ...}
    """
    data = request.get_json()
    tickers = data.get("tickers", []) if data else []

    if not tickers or not isinstance(tickers, list):
        return jsonify({"error": "Please provide a 'tickers' list."}), 400

    # Sanitize
    tickers = [str(t).strip() for t in tickers if isinstance(t, str) and 1 <= len(str(t).strip()) <= 20]
    if not tickers:
        return jsonify({"error": "No valid tickers provided."}), 400

    quotes = fetch_realtime_quotes(tickers)
    return jsonify({"quotes": quotes, "updated_at": datetime.utcnow().isoformat() + "Z"})


@app.route("/api/quote/<ticker>")
def api_single_quote(ticker: str):
    """Fetch real-time quote for a single ticker."""
    ticker = ticker.strip().upper()
    if not ticker or len(ticker) > 10:
        return jsonify({"error": "Invalid ticker"}), 400

    quotes = fetch_realtime_quotes([ticker])
    if ticker in quotes:
        return jsonify({"quote": quotes[ticker], "updated_at": datetime.utcnow().isoformat() + "Z"})
    else:
        return jsonify({"error": f"Could not fetch data for '{ticker}'."}), 404


@app.route("/api/indices")
def api_indices():
    """Fetch current global index values."""
    indices = fetch_indices_data()
    return jsonify({"indices": indices, "updated_at": datetime.utcnow().isoformat() + "Z"})


@app.route("/api/gainers")
def api_gainers():
    """
    Return top gainers and losers across all tracked markets.
    By default fetches real-time data for all tracked stocks.
    """
    all_tickers = []
    for mkt_list in get_market_stocks().values():
        all_tickers.extend(mkt_list)
    all_tickers = list(dict.fromkeys(all_tickers))  # dedup

    quotes = fetch_realtime_quotes(all_tickers)
    result = fetch_gainers_losers(quotes, top_n=10)
    return jsonify({
        **result,
        "updated_at": datetime.utcnow().isoformat() + "Z",
    })


@app.route("/api/sectors")
def api_sectors():
    """
    Return sector-level performance heatmap data.
    Aggregates average change across all stocks per sector.
    """
    all_tickers = []
    for mkt_list in get_market_stocks().values():
        all_tickers.extend(mkt_list)
    all_tickers = list(dict.fromkeys(all_tickers))

    quotes = fetch_realtime_quotes(all_tickers)
    heatmap = fetch_sector_heatmap(quotes)
    groups = get_sector_groups()
    return jsonify({
        "heatmap": heatmap,
        "groups": groups,
        "updated_at": datetime.utcnow().isoformat() + "Z",
    })


@app.route("/api/market-summary")
def api_market_summary():
    """Return a high-level market breadth summary."""
    all_tickers = []
    for mkt_list in get_market_stocks().values():
        all_tickers.extend(mkt_list)
    all_tickers = list(dict.fromkeys(all_tickers))

    quotes = fetch_realtime_quotes(all_tickers)
    summary = get_market_summary(quotes)
    return jsonify({
        **summary,
        "updated_at": datetime.utcnow().isoformat() + "Z",
    })


@app.route("/api/market-stocks")
def api_market_stocks():
    """Return market groupings with metadata."""
    markets = get_market_stocks()
    metadata = get_stock_metadata()
    return jsonify({"markets": markets, "metadata": metadata})


def run_web(host="127.0.0.1", port=5000, debug=False):
    print(f"\n  🌐  Web app running at: http://{host}:{port}")
    print("  Open the URL above in your browser.")
    print("  Press Ctrl+C to stop.\n")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_web()
