from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import yfinance as yf
from datetime import datetime, timezone

_analyzer = SentimentIntensityAnalyzer()


def _sentiment_label(score: float) -> str:
    if score >= 0.15:
        return "Very Positive"
    if score >= 0.05:
        return "Positive"
    if score <= -0.15:
        return "Very Negative"
    if score <= -0.05:
        return "Negative"
    return "Neutral"


def get_news_sentiment(ticker: str, max_items: int = 10) -> dict:
    """
    Fetch recent news via yfinance and compute aggregate VADER sentiment.

    Returns:
        articles: list of {title, publisher, url, published_at, sentiment_label, sentiment_score}
        aggregate_score: float in [-1, 1]
        sentiment_label: str
    """
    try:
        news = yf.Ticker(ticker).news or []
    except Exception:
        news = []

    articles = []
    scores = []

    for item in news[:max_items]:
        # yfinance >=0.2.x may nest content under a 'content' key
        content = item.get("content", item)
        title = content.get("title") or item.get("title", "")
        publisher = (
            content.get("provider", {}).get("displayName")
            or content.get("publisher")
            or item.get("publisher", "")
        )
        url = (
            content.get("canonicalUrl", {}).get("url")
            or content.get("link")
            or item.get("link", "")
        )

        ts = content.get("pubDate") or item.get("providerPublishTime")
        if isinstance(ts, (int, float)):
            published_at = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        elif isinstance(ts, str):
            published_at = ts[:16]
        else:
            published_at = "Unknown"

        if not title:
            continue

        compound = _analyzer.polarity_scores(title)["compound"]
        scores.append(compound)
        articles.append({
            "title": title,
            "publisher": publisher,
            "url": url,
            "published_at": published_at,
            "sentiment_label": _sentiment_label(compound),
            "sentiment_score": compound,
        })

    avg = sum(scores) / len(scores) if scores else 0.0
    return {
        "articles": articles,
        "aggregate_score": avg,
        "sentiment_label": _sentiment_label(avg),
    }


def generate_recommendation(
    current_price: float | None,
    future_preds: list,
    sentiment_result: dict,
) -> dict:
    """
    Combine LSTM 7-day forecast direction with news sentiment to produce a signal.

    Weighting: 60 % price model signal + 40 % news sentiment score.
    Price signal is clamped to ±10 % as a ±1 normalisation range.
    """
    if current_price and current_price > 0 and future_preds:
        price_change_pct = (future_preds[-1] - current_price) / current_price * 100
    else:
        price_change_pct = 0.0

    sentiment_score = sentiment_result.get("aggregate_score", 0.0)
    price_signal = max(-1.0, min(1.0, price_change_pct / 10.0))
    combined = 0.6 * price_signal + 0.4 * sentiment_score

    if combined >= 0.20:
        signal, color = "Strong Buy", "#2ECC71"
    elif combined >= 0.05:
        signal, color = "Buy", "#82E0AA"
    elif combined <= -0.20:
        signal, color = "Strong Sell", "#E74C3C"
    elif combined <= -0.05:
        signal, color = "Sell", "#F0B27A"
    else:
        signal, color = "Hold", "#ABB2B9"

    rationale = (
        f"LSTM model forecasts **{price_change_pct:+.2f}%** over 7 trading days; "
        f"news sentiment is **{sentiment_result.get('sentiment_label', 'Neutral')}** "
        f"(score: {sentiment_score:+.2f})."
    )

    return {
        "signal": signal,
        "color": color,
        "combined_score": combined,
        "price_change_pct": price_change_pct,
        "rationale": rationale,
    }
