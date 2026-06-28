import time

import pandas as pd
import yfinance as yf

_MAX_RETRIES = 3
_RETRY_DELAY = 2


class TickerNotFoundError(ValueError):
    pass


def clean_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    close = df["Close"].astype(float)
    for col in ["Open", "High", "Low", "Adj Close"]:
        if col not in df:
            df[col] = close
        df[col] = df[col].astype(float).fillna(close)
    if "Volume" not in df:
        df["Volume"] = 0.0
    df["Volume"] = df["Volume"].astype(float).fillna(0.0)
    return df[["Open", "High", "Low", "Close", "Adj Close", "Volume"]].dropna(subset=["Close"])


def fetch_stock_data(ticker: str, period: str = "2y") -> pd.DataFrame:
    ticker = ticker.strip().upper()
    last_err = None
    for attempt in range(_MAX_RETRIES):
        try:
            df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=False)
            if df.empty:
                raise TickerNotFoundError(f"No data found for ticker '{ticker}'. Please check the symbol.")
            if isinstance(df.columns, pd.MultiIndex):
                df = df.droplevel("Ticker", axis=1)
            return clean_ohlcv(df)
        except TickerNotFoundError:
            raise
        except Exception as e:
            last_err = e
            if attempt < _MAX_RETRIES - 1:
                time.sleep(_RETRY_DELAY * (attempt + 1))
    raise ValueError(
        f"Failed to fetch data for '{ticker}' after {_MAX_RETRIES} attempts."
    ) from last_err


def get_stock_info(ticker: str) -> dict:
    ticker = ticker.strip().upper()
    result = {"name": ticker, "currency": "USD", "current_price": None}

    t = yf.Ticker(ticker)

    try:
        fi = t.fast_info
        result["currency"] = fi.get("currency", "USD")
        result["current_price"] = fi.get("lastPrice") or fi.get("regularMarketPrice")
    except Exception:
        pass

    try:
        info = t.info or {}
        name = info.get("longName") or info.get("shortName")
        if name:
            result["name"] = name
    except Exception:
        pass

    return result
