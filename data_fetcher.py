import pandas as pd
import requests

_YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
_SESSION = requests.Session()
_SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json,text/plain,*/*",
    }
)


def fetch_chart(ticker: str, period: str = "2y") -> dict:
    response = _SESSION.get(
        _YAHOO_URL.format(ticker=ticker),
        params={
            "range": period,
            "interval": "1d",
            "includePrePost": "false",
            "events": "div,splits",
        },
        timeout=20,
    )
    if response.status_code != 200:
        raise ValueError(f"No data found for ticker '{ticker}'. Please check the symbol and try again.")
    payload = response.json()
    chart = payload.get("chart", {})
    if chart.get("error"):
        desc = chart["error"].get("description", "Unknown Yahoo Finance error")
        raise ValueError(f"Yahoo Finance returned an error for ticker '{ticker}': {desc}")
    results = chart.get("result") or []
    if not results:
        raise ValueError(f"No data found for ticker '{ticker}'. Please check the symbol and try again.")
    return results[0]


def fetch_stock_data(ticker: str, period: str = "2y") -> pd.DataFrame:
    chart = fetch_chart(ticker, period)
    timestamps = chart.get("timestamp") or []
    quote = (chart.get("indicators", {}).get("quote") or [{}])[0]
    adj_close = ((chart.get("indicators", {}).get("adjclose") or [{}])[0].get("adjclose") or [])
    closes = quote.get("close") or []
    if not timestamps or not closes:
        raise ValueError(f"No data found for ticker '{ticker}'. Please check the symbol and try again.")

    df = pd.DataFrame(
        {
            "Date": pd.to_datetime(timestamps, unit="s"),
            "Open": quote.get("open") or [],
            "High": quote.get("high") or [],
            "Low": quote.get("low") or [],
            "Close": closes,
            "Adj Close": adj_close or closes,
            "Volume": quote.get("volume") or [],
        }
    ).dropna(subset=["Close"])
    if df.empty:
        raise ValueError(f"No data found for ticker '{ticker}'. Please check the symbol and try again.")

    df = df.set_index("Date").sort_index()
    for col in ["Open", "High", "Low", "Adj Close"]:
        if col not in df:
            df[col] = df["Close"]
        df[col] = df[col].fillna(df["Close"])
    if "Volume" not in df:
        df["Volume"] = 0.0
    df["Volume"] = df["Volume"].fillna(0.0)
    return df[["Open", "High", "Low", "Close", "Adj Close", "Volume"]]


def get_stock_info(ticker: str) -> dict:
    try:
        chart = fetch_chart(ticker, "2y")
        meta = chart.get("meta", {})
        closes = ((chart.get("indicators", {}).get("quote") or [{}])[0].get("close") or [])
        current_price = next((price for price in reversed(closes) if price is not None), None)
        return {
            "name": meta.get("longName") or meta.get("shortName") or ticker,
            "currency": meta.get("currency", "USD"),
            "current_price": meta.get("regularMarketPrice") or current_price,
        }
    except Exception:
        return {"name": ticker, "currency": "USD", "current_price": None}
