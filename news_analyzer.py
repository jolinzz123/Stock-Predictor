from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import yfinance as yf
from datetime import datetime, timezone

analyzer = SentimentIntensityAnalyzer()


def sentiment_label(score: float) -> str:
    if score >= 0.15:
        return "Very Positive"
    if score >= 0.05:
        return "Positive"
    if score <= -0.15:
        return "Very Negative"
    if score <= -0.05:
        return "Negative"
    return "Neutral"


def format_publish_time(timestamp) -> str:
    try:
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return "Unknown"


def get_news_sentiment(ticker: str, max_items: int = 10) -> dict:
    """
    Fetch recent news for `ticker` via yfinance and score each headline
    with VADER sentiment analysis.

    Returns
    -------
    {
        articles       : list[dict]   – per-article data + sentiment
        sentiment_score: float        – average compound score
        sentiment_label: str          – human-readable label
        positive_count : int
        negative_count : int
        neutral_count  : int
        aggregate_score: float        – alias for sentiment_score (legacy compat)
    }
    """
    try:
        stock = yf.Ticker(ticker)
        news_items = stock.news or []

        if not news_items:
            return _empty_result()

        articles = []
        scores = []
        positive = negative = neutral = 0

        for item in news_items[:max_items]:
            # yfinance ≥0.2.x may nest everything under "content"
            content = item.get("content", {})

            title = (
                item.get("title", "")
                or content.get("title", "")
            ).strip()

            publisher = (
                item.get("publisher", "")
                or content.get("provider", {}).get("displayName", "")
                or "Unknown"
            )

            url = (
                item.get("link", "")
                or content.get("canonicalUrl", {}).get("url", "")
                or content.get("clickThroughUrl", {}).get("url", "")
                or ""
            )

            publish_time = item.get("providerPublishTime", 0) or 0

            if not title:
                continue

            score = analyzer.polarity_scores(title)["compound"]
            label = sentiment_label(score)

            if score >= 0.05:
                positive += 1
            elif score <= -0.05:
                negative += 1
            else:
                neutral += 1

            scores.append(score)
            articles.append({
                "title":           title,
                "publisher":       publisher,
                "url":             url,
                "published_at":    format_publish_time(publish_time),
                "sentiment_score": score,
                "sentiment_label": label,
            })

        avg_score = sum(scores) / len(scores) if scores else 0.0

        return {
            "articles":        articles,
            "sentiment_score": avg_score,
            "aggregate_score": avg_score,   # legacy alias used by some callers
            "sentiment_label": sentiment_label(avg_score),
            "positive_count":  positive,
            "negative_count":  negative,
            "neutral_count":   neutral,
        }

    except Exception as e:
        return {**_empty_result(), "error": str(e)}


def _empty_result() -> dict:
    return {
        "articles":        [],
        "sentiment_score": 0.0,
        "aggregate_score": 0.0,
        "sentiment_label": "Neutral",
        "positive_count":  0,
        "negative_count":  0,
        "neutral_count":   0,
    }


def extract_market_drivers(news_result: dict, top_n: int = 5) -> list[dict]:
    """
    Return the `top_n` articles with the highest absolute sentiment score —
    these are the headlines that moved the needle most, in either direction.
    """
    return sorted(
        news_result.get("articles", []),
        key=lambda a: abs(a["sentiment_score"]),
        reverse=True,
    )[:top_n]


def generate_recommendation(
    current_price: float,
    future_predictions: list[float],
    news_result: dict,
) -> dict:
    """
    Combine LSTM forecast (70%) and news sentiment (30%) into a single signal.

    The `rationale` field is intentionally left empty — main.py builds a
    richer narrative via `_build_recommendation_text()` using the returned
    numeric fields, so we avoid duplicating that logic here.

    Returns
    -------
    {
        signal          : str    – STRONG BUY / BUY / HOLD / REDUCE / AVOID
        color           : str    – hex colour for the badge
        combined_score  : float
        price_change_pct: float  – LSTM-implied 7-day return (%)
        predicted_price : float  – day-7 price
        rationale       : str    – empty; narrative built in main.py
    }
    """
    predicted_price = future_predictions[-1]
    price_change_pct = (predicted_price - current_price) / current_price * 100

    # Normalise prediction score: 10 % move → score of 1.0
    prediction_score = price_change_pct / 10
    sentiment_score = news_result.get("sentiment_score", 0.0)
    combined_score = prediction_score * 0.7 + sentiment_score * 0.3

    if combined_score >= 0.60:
        signal, color = "STRONG BUY", "#2ECC71"
    elif combined_score >= 0.20:
        signal, color = "BUY",        "#58D68D"
    elif combined_score > -0.20:
        signal, color = "HOLD",       "#F4D03F"
    elif combined_score > -0.60:
        signal, color = "REDUCE",     "#F39C12"
    else:
        signal, color = "AVOID",      "#E74C3C"

    return {
        "signal":           signal,
        "color":            color,
        "combined_score":   combined_score,
        "price_change_pct": price_change_pct,
        "predicted_price":  predicted_price,
        "rationale":        "",   # narrative rendered by main.py
    }
