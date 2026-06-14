import random
import yfinance as yf
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from constants import _STOCK_NAMES, _STOCK_SECTORS, _SECTOR_GROUPS, _INDICES, _MARKETS

def fetch_stock_data(ticker: str, period: str = "2y") -> pd.DataFrame:
    df = yf.download(ticker, period=period, progress=False, auto_adjust=True)

    if df.empty:
        raise ValueError(f"No data found for ticker '{ticker}'.")

    close_df = df[["Close"]].copy()
    close_df.dropna(inplace=True)

    if len(close_df) < 100:
        raise ValueError(
            f"Insufficient data for '{ticker}'. "
            f"Only {len(close_df)} records found (minimum 100 required)."
        )

    return close_df


def preprocess_data(df: pd.DataFrame, look_back: int = 60):
    """
    Normalize data and create sliding-window sequences for LSTM training.

    Parameters:
        df (pd.DataFrame): Raw closing price DataFrame.
        look_back (int): Number of past days used as input features.

    Returns:
        tuple: (X, y, scaler)
            X (np.ndarray): Input sequences of shape (samples, look_back, 1).
            y (np.ndarray): Target values of shape (samples, 1).
            scaler (MinMaxScaler): Fitted scaler for inverse transformation.
    """
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(df.values)

    X, y = [], []
    for i in range(look_back, len(scaled_data)):
        X.append(scaled_data[i - look_back:i, 0])
        y.append(scaled_data[i, 0])

    X = np.array(X)
    y = np.array(y)
    X = X.reshape((X.shape[0], X.shape[1], 1))

    return X, y, scaler


def train_test_split_timeseries(X: np.ndarray, y: np.ndarray, split_ratio: float = 0.8):
    """
    Split data into training and testing sets while preserving time order.

    Parameters:
        X (np.ndarray): Input sequences.
        y (np.ndarray): Target values.
        split_ratio (float): Proportion of data for training (default: 80%).

    Returns:
        tuple: (X_train, X_test, y_train, y_test)
    """
    split_index = int(len(X) * split_ratio)

    X_train = X[:split_index]
    X_test  = X[split_index:]
    y_train = y[:split_index]
    y_test  = y[split_index:]

    return X_train, X_test, y_train, y_test


# ── Real-time quote fetching ─────────────────────────────────

def fetch_realtime_quotes(tickers: list) -> dict:
    """
    Fetch current real-time quotes for a list of ticker symbols.

    Uses yfinance fast_info for near-real-time data (may be delayed ~15 min
    for non-US markets). Falls back to latest close if real-time data is
    unavailable.

    Parameters:
        tickers (list): List of yfinance ticker symbols.

    Returns:
        dict: {ticker: {price, change, changePercent, name, sector}}
    """
    if not tickers:
        return {}

    results = {}
    try:
        yt = yf.Tickers(" ".join(tickers))

        for sym in tickers:
            try:
                tk = yt.tickers.get(sym)
                if tk is None:
                    continue

                info = tk.fast_info
                price      = getattr(info, "last_price", None) or getattr(info, "regular_market_previous_close", None)
                prev_close = getattr(info, "regular_market_previous_close", None) or getattr(info, "previous_close", None)

                if price is None or price <= 0:
                    hist = tk.history(period="2d")
                    if not hist.empty:
                        price      = float(hist["Close"].iloc[-1])
                        prev_close = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else price

                if price is None or price <= 0:
                    continue

                change_val = price - prev_close if prev_close else 0
                change_pct = (change_val / prev_close * 100) if prev_close and prev_close != 0 else 0

                results[sym] = {
                    "price":         round(float(price), 2),
                    "change":        round(float(change_val), 2),
                    "changePercent": round(float(change_pct), 2),
                    "name":          _STOCK_NAMES.get(sym, sym),
                    "sector":        _STOCK_SECTORS.get(sym, "Other"),
                }
            except Exception:
                continue

    except Exception:
        for sym in tickers:
            try:
                tk         = yf.Ticker(sym)
                info       = tk.fast_info
                price      = getattr(info, "last_price", None) or getattr(info, "regular_market_previous_close", None)
                prev_close = getattr(info, "regular_market_previous_close", None) or getattr(info, "previous_close", None)

                if price is None or price <= 0:
                    hist = tk.history(period="2d")
                    if not hist.empty:
                        price      = float(hist["Close"].iloc[-1])
                        prev_close = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else price

                if price is None or price <= 0:
                    continue

                change_val = price - prev_close if prev_close else 0
                change_pct = (change_val / prev_close * 100) if prev_close and prev_close != 0 else 0

                results[sym] = {
                    "price":         round(float(price), 2),
                    "change":        round(float(change_val), 2),
                    "changePercent": round(float(change_pct), 2),
                    "name":          _STOCK_NAMES.get(sym, sym),
                    "sector":        _STOCK_SECTORS.get(sym, "Other"),
                }
            except Exception:
                continue

    return results


def fetch_indices_data() -> list:
    """
    Fetch current values for global market indices.

    Returns:
        list: Dicts with keys: region, name, price, change, changePercent, up, trend.
    """
    results = []
    tickers = [idx["ticker"] for idx in _INDICES]

    try:
        yt = yf.Tickers(" ".join(tickers))

        for idx_def in _INDICES:
            sym = idx_def["ticker"]
            try:
                tk = yt.tickers.get(sym)
                if tk is None:
                    continue

                info       = tk.fast_info
                price      = getattr(info, "last_price", None) or getattr(info, "regular_market_previous_close", None)
                prev_close = getattr(info, "regular_market_previous_close", None) or getattr(info, "previous_close", None)

                if price is None or price <= 0:
                    hist = tk.history(period="2d")
                    if not hist.empty:
                        price      = float(hist["Close"].iloc[-1])
                        prev_close = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else price

                if price is None or price <= 0:
                    continue

                change_val = price - prev_close if prev_close else 0
                change_pct = (change_val / prev_close * 100) if prev_close and prev_close != 0 else 0

                results.append({
                    "region":        idx_def["region"],
                    "name":          idx_def["name"],
                    "price":         f"{price:,.2f}",
                    "change":        f"{change_val:+.2f}",
                    "changePercent": f"{change_pct:+.2f}%",
                    "up":            change_val >= 0,
                    "trend":         _gen_mini_trend(change_val >= 0, 20),
                })
            except Exception:
                continue

    except Exception:
        pass

    return results


def get_market_stocks() -> dict:
    """Return the market stock groupings."""
    return dict(_MARKETS)


def get_stock_metadata() -> dict:
    """Return name and sector metadata for all known stocks."""
    return {
        sym: {"name": name, "sector": _STOCK_SECTORS.get(sym, "Other")}
        for sym, name in _STOCK_NAMES.items()
    }


def _gen_mini_trend(up: bool, length: int = 20) -> list:
    """Generate a deterministic sparkline based on direction."""
    random.seed(abs(hash(up)) % (2 ** 31))
    arr = []
    v    = 5.0
    bias = 0.15 if up else -0.15
    for _ in range(length):
        v += (random.random() - 0.45) * 2.0 + bias
        arr.append(round(v, 1))
    return arr


# ── Sector / Ranking / Market Summary ────────────────────────

def get_sector_groups() -> dict:
    """Return sector grouping definitions."""
    return dict(_SECTOR_GROUPS)


def fetch_gainers_losers(quotes: dict, top_n: int = 10) -> dict:
    """
    Compute top gainers and losers from real-time quotes.

    Parameters:
        quotes (dict): Output from fetch_realtime_quotes().
        top_n (int): Number of entries per list.

    Returns:
        dict: {'gainers': [...], 'losers': [...]}
    """
    entries = [
        {
            "ticker":        sym,
            "name":          q.get("name", sym),
            "price":         q["price"],
            "changePercent": q["changePercent"],
            "change":        q["change"],
        }
        for sym, q in quotes.items()
    ]

    entries.sort(key=lambda x: x["changePercent"], reverse=True)

    gainers = [e for e in entries if e["changePercent"] > 0][:top_n]
    losers  = sorted(
        [e for e in entries if e["changePercent"] < 0],
        key=lambda x: x["changePercent"]
    )[:top_n]

    return {"gainers": gainers, "losers": losers}


def fetch_sector_heatmap(quotes: dict) -> list:
    """
    Aggregate sector performance from real-time quotes.

    Returns:
        list: Sector dicts with {name, changePercent, stockCount, upCount, downCount}.
    """
    sector_data: dict = {}
    for sym, q in quotes.items():
        sector = _STOCK_SECTORS.get(sym)
        if not sector:
            continue
        if sector not in sector_data:
            sector_data[sector] = {"total_change": 0.0, "count": 0, "up": 0, "down": 0}
        sd = sector_data[sector]
        sd["total_change"] += q["changePercent"]
        sd["count"] += 1
        if q["changePercent"] >= 0:
            sd["up"] += 1
        else:
            sd["down"] += 1

    result = []
    for name, data in sector_data.items():
        if data["count"] == 0:
            continue
        avg_change = data["total_change"] / data["count"]
        result.append({
            "name":          name,
            "changePercent": round(avg_change, 2),
            "stockCount":    data["count"],
            "upCount":       data["up"],
            "downCount":     data["down"],
        })

    result.sort(key=lambda x: x["changePercent"], reverse=True)
    return result


def get_market_summary(quotes: dict = None) -> dict:
    """
    Build a high-level market breadth summary.

    Returns:
        dict: total_stocks, advancing, declining, unchanged, average_change, sentiment.
    """
    if not quotes:
        return {
            "total_stocks": 0, "advancing": 0, "declining": 0,
            "unchanged": 0, "average_change": 0, "sentiment": "N/A",
        }

    adv     = sum(1 for q in quotes.values() if q["changePercent"] >  0.05)
    dec     = sum(1 for q in quotes.values() if q["changePercent"] < -0.05)
    unch    = len(quotes) - adv - dec
    avg_chg = sum(q["changePercent"] for q in quotes.values()) / max(len(quotes), 1)

    if avg_chg > 0.5:
        sentiment = "BULLISH"
    elif avg_chg < -0.5:
        sentiment = "BEARISH"
    else:
        sentiment = "MIXED"

    return {
        "total_stocks":  len(quotes),
        "advancing":     adv,
        "declining":     dec,
        "unchanged":     unch,
        "average_change": round(avg_chg, 2),
        "sentiment":     sentiment,
    }
