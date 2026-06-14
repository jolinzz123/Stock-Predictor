import yfinance as yf
import pandas as pd


def fetch_stock_data(ticker: str, period: str = "2y") -> pd.DataFrame:
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)
    if df.empty:
        raise ValueError(f"No data found for ticker '{ticker}'. Please check the symbol and try again.")
    return df[["Close"]]


def get_stock_info(ticker: str) -> dict:
    try:
        info = yf.Ticker(ticker).info
        return {
            "name": info.get("longName") or info.get("shortName") or ticker,
            "currency": info.get("currency", "USD"),
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
        }
    except Exception:
        return {"name": ticker, "currency": "USD", "current_price": None}
