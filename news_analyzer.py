from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from pandas import DatetimeIndex
import requests
import yfinance as yf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Constants
ALPHAVANTAGE_BASE_URL = "https://www.alphavantage.co/query"
ALPHAVANTAGE_TIMEOUT_SECONDS = int(os.getenv("AV_TIMEOUT", "20"))
CONFIDENCE_ARTICLE_BASELINE = int(os.getenv("CONFIDENCE_BASELINE", "10"))

# Scorer
_vader = SentimentIntensityAnalyzer()


def _score_article(title: str, summary: str = "") -> float:
    """Score a news article using VADER. Blends title (60%) and summary (40%) when a summary is available."""
    title_score = _vader.polarity_scores(title)["compound"] if title else 0.0
    if not summary or not summary.strip():
        return title_score
    summary_score = _vader.polarity_scores(summary)["compound"]
    return title_score * 0.6 + summary_score * 0.4


# Shared helpers (https://digitalenvironment.org/natural-language-processing-vader-sentiment-analysis-with-nltk/)
def sentiment_label(score: float) -> str:
    if score >= 0.15:       # strongly positive
        return "Very Positive"
    if score >= 0.05:       # mildly positive
        return "Positive"
    if score <= -0.15:      # strongly negative
        return "Very Negative"
    if score <= -0.05:      # mildly negative
        return "Negative"
    return "Neutral"        # -0.05 < score < 0.05


def format_publish_time(timestamp) -> str:
    """Accept either a Unix timestamp (int/float) or an AV-style string."""
    try:
        if isinstance(timestamp, str) and "T" in timestamp:
            dt = datetime.strptime(timestamp, "%Y%m%dT%H%M%S").replace(
                tzinfo=timezone.utc)
        else:
            dt = datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return "Unknown"


def get_time_weight(timestamp: int | float) -> float:
    """Decay weight based on how many hours ago an article was published. (https://arxiv.org/pdf/2412.07587)"""
    try:
        published = datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
        hours_old = (datetime.now(timezone.utc) -
                     published).total_seconds() / 3600
        if hours_old <= 24:     # within last day → full weight
            return 1.0
        if hours_old <= 72:     # 1–3 days old → 80%
            return 0.8
        if hours_old <= 168:    # 3–7 days old → 50%
            return 0.5
        return 0.2              # older than 7 days → minimal weight
    except Exception:
        return 0.2


def _normalize_datetime_index(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Ensure index is a tz-naive DatetimeIndex, converting if needed."""
    if not isinstance(index, pd.DatetimeIndex):
        index = pd.to_datetime(index)
    if index.tz is not None:
        index = index.tz_convert(None)
    return pd.DatetimeIndex(index)


def _empty_result() -> dict:
    return {
        "articles":             [],
        "sentiment_score":      0.0,
        "aggregate_score":      0.0,
        "sentiment_label":      "Neutral",
        "positive_count":       0,
        "negative_count":       0,
        "neutral_count":        0,
        "article_count":        0,
        "sentiment_confidence": 0.0,
        "source":               "none",
    }


# Alpha Vantage
def get_alphavantage_api_key() -> str | None:
    """Read the AV API key from the environment."""
    return (
        os.getenv("ALPHAVANTAGE_API_KEY")
        or os.getenv("ALPHA_VANTAGE_API_KEY")
        or None
    )


def _alpha_vantage_query(**params) -> dict:
    api_key = get_alphavantage_api_key()
    if not api_key:
        raise RuntimeError("Missing ALPHAVANTAGE_API_KEY.")
    response = requests.get(
        ALPHAVANTAGE_BASE_URL,
        params={**params, "apikey": api_key},
        timeout=ALPHAVANTAGE_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    message = data.get("Information") or data.get(
        "Note") or data.get("Error Message")
    if message:
        raise RuntimeError(str(message))
    return data


def fetch_alpha_vantage_news_feed(
    ticker: str,
    *,
    limit: int = 50,
    start: pd.Timestamp | None = None,
    end: pd.Timestamp | None = None,
    sort: str = "LATEST",
) -> list[dict]:
    """Fetch raw AV news feed for *ticker*."""
    params: dict = {
        "function": "NEWS_SENTIMENT",
        "tickers":  ticker.upper(),
        "limit":    int(limit),
        "sort":     sort,
    }
    if start is not None:
        params["time_from"] = pd.Timestamp(start).strftime("%Y%m%dT%H%M")
    if end is not None:
        params["time_to"] = pd.Timestamp(end).strftime("%Y%m%dT%H%M")
    return list(_alpha_vantage_query(**params).get("feed", []))


def _extract_ticker_score(article: dict, ticker: str) -> tuple[float, float]:
    """Return (score, relevance_weight) for *ticker* from an AV article.
    Falls back to the article-level overall score with weight=1.0."""
    for item in article.get("ticker_sentiment", []):
        if str(item.get("ticker", "")).upper() == ticker.upper():
            score = float(item.get("ticker_sentiment_score", 0.0))
            weight = float(item.get("relevance_score", 1.0))
            return score, max(weight, 1e-6)
    return float(article.get("overall_sentiment_score", 0.0)), 1.0


def _parse_published_at(article: dict) -> pd.Timestamp | None:
    raw = article.get("time_published")
    if not raw:
        return None
    try:
        return pd.Timestamp(datetime.strptime(raw, "%Y%m%dT%H%M%S"))
    except Exception:
        return None


def _summarize_alpha_vantage_feed(
    ticker: str,
    feed: list[dict],
    max_items: int = 10,
) -> dict:
    """Summarise an AV feed into the standard result dict."""
    if not feed:
        return _empty_result()

    articles = []
    scores: list[float] = []
    positive = negative = neutral = 0

    for article in feed[:max_items]:
        title = str(article.get("title", "")).strip()
        if not title:
            continue

        score, _ = _extract_ticker_score(article, ticker)
        summary = str(article.get("summary", "")).strip()
        if summary:
            # AV ticker score (60%) + VADER summary score (40%)
            score = score * 0.6 + \
                _vader.polarity_scores(summary)["compound"] * 0.4
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
            "publisher":       article.get("source", "Unknown"),
            "url":             article.get("url", ""),
            "published_at":    format_publish_time(article.get("time_published", "")),
            "sentiment_score": score,
            "sentiment_label": label,
            "summary":         summary,
        })

    avg_score = sum(scores) / len(scores) if scores else 0.0
    confidence = abs(avg_score) * min(len(scores) /
                                      CONFIDENCE_ARTICLE_BASELINE, 1.0)

    return {
        "articles":             articles,
        "sentiment_score":      avg_score,
        "aggregate_score":      avg_score,
        "sentiment_label":      sentiment_label(avg_score),
        "positive_count":       positive,
        "negative_count":       negative,
        "neutral_count":        neutral,
        "article_count":        len(scores),
        "sentiment_confidence": round(confidence, 4),
        "source":               "alphavantage",
    }


# Historical sentiment series (used by predictor)
def _build_daily_sentiment_series_from_feed(
    ticker: str,
    feed: list[dict],
    price_index: pd.DatetimeIndex,
) -> pd.Series:
    aligned_index = pd.DatetimeIndex(
        _normalize_datetime_index(price_index)).normalize()
    if len(aligned_index) == 0:
        return pd.Series(dtype=float)
    if not feed:
        return pd.Series(0.0, index=aligned_index, dtype=float)

    rows = []
    for article in feed:
        published_at = _parse_published_at(article)
        if published_at is None:
            continue
        score, weight = _extract_ticker_score(article, ticker)
        rows.append({"date": published_at.normalize(),
                    "weighted_score": score * weight, "weight": weight})

    if not rows:
        return pd.Series(0.0, index=aligned_index, dtype=float)

    daily = pd.DataFrame(rows).groupby("date").sum()
    series = daily["weighted_score"] / daily["weight"].replace(0, pd.NA)
    series = series.fillna(0.0).astype(float)
    series = series.reindex(aligned_index, fill_value=0.0)
    series = series.ewm(span=3, adjust=False).mean()
    return series.clip(-1.0, 1.0)


def get_historical_sentiment_series(
    ticker: str,
    price_index: pd.DatetimeIndex,
    article_limit: int = 1000,
) -> pd.Series:
    """Daily sentiment series aligned to price_index — used as a model feature."""
    aligned_index = _normalize_datetime_index(price_index)
    if len(aligned_index) == 0:
        return pd.Series(dtype=float)
    if not get_alphavantage_api_key():
        return pd.Series(0.0, index=aligned_index.normalize(), dtype=float)

    start = aligned_index.min().normalize()
    end = (aligned_index.max().normalize() +
           timedelta(days=1)).replace(hour=23, minute=59)
    try:
        feed = fetch_alpha_vantage_news_feed(
            ticker, limit=article_limit, start=start, end=end)
        return _build_daily_sentiment_series_from_feed(ticker, feed, aligned_index)
    except Exception:
        return pd.Series(0.0, index=aligned_index.normalize(), dtype=float)


def get_ticker_sentiment_context(
    ticker: str,
    price_index: pd.DatetimeIndex,
    max_items: int = 10,
    article_limit: int = 1000,
) -> dict:
    """Return both a news_result dict and a sentiment_series for the predictor."""
    aligned_index = _normalize_datetime_index(price_index)

    if len(aligned_index) == 0 or not get_alphavantage_api_key():
        return {
            "news_result":      get_news_sentiment(ticker, max_items=max_items),
            "sentiment_series": pd.Series(0.0, index=DatetimeIndex(aligned_index.normalize()), dtype=float),
        }

    start = aligned_index.min().normalize()
    end = (aligned_index.max().normalize() +
           timedelta(days=1)).replace(hour=23, minute=59)
    try:
        feed = fetch_alpha_vantage_news_feed(
            ticker, limit=article_limit, start=start, end=end)
        return {
            "news_result":      _summarize_alpha_vantage_feed(ticker, feed, max_items=max_items),
            "sentiment_series": _build_daily_sentiment_series_from_feed(ticker, feed, aligned_index),
        }
    except Exception:
        return {
            "news_result":      get_news_sentiment(ticker, max_items=max_items),
            "sentiment_series": pd.Series(0.0, index=DatetimeIndex(aligned_index.normalize()), dtype=float),
        }


# yfinance fallback
def _get_yfinance_news_sentiment(ticker: str, max_items: int = 10) -> dict:
    """Score yfinance headlines with VADER, applying time-decay weights."""
    news_items = yf.Ticker(ticker).news or []
    if not news_items:
        return _empty_result()

    articles = []
    weighted_sum = 0.0
    total_weight = 0.0
    raw_scores: list[float] = []
    positive = negative = neutral = 0

    for item in news_items[:max_items]:
        content = item.get("content", {})
        title = (item.get("title", "") or content.get("title", "")).strip()
        if not title:
            continue

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
        summary = (item.get("summary", "") or content.get(
            "summary", "") or "").strip()

        score = _score_article(title, summary)  # title 60% + summary 40%
        label = sentiment_label(score)

        if score >= 0.05:
            positive += 1
        elif score <= -0.05:
            negative += 1
        else:
            neutral += 1

        weight = get_time_weight(publish_time)
        weighted_sum += score * weight
        total_weight += weight
        raw_scores.append(score)

        articles.append({
            "title":           title,
            "publisher":       publisher,
            "url":             url,
            "published_at":    format_publish_time(publish_time),
            "sentiment_score": score,
            "sentiment_label": label,
        })

    avg_score = weighted_sum / total_weight if total_weight > 0 else 0.0
    confidence = abs(avg_score) * min(len(raw_scores) /
                                      CONFIDENCE_ARTICLE_BASELINE, 1.0)

    return {
        "articles":             articles,
        "sentiment_score":      avg_score,
        "aggregate_score":      avg_score,
        "sentiment_label":      sentiment_label(avg_score),
        "positive_count":       positive,
        "negative_count":       negative,
        "neutral_count":        neutral,
        "article_count":        len(raw_scores),
        "sentiment_confidence": round(confidence, 4),
        "source":               "yfinance+vader",
    }


# Public API
def get_news_sentiment(ticker: str, max_items: int = 10) -> dict:
    """Return sentiment data for the most recent news articles on *ticker*. """
    if get_alphavantage_api_key():
        try:
            feed = fetch_alpha_vantage_news_feed(
                ticker, limit=max(max_items, 20))
            if feed:
                return _summarize_alpha_vantage_feed(ticker, feed, max_items=max_items)
        except Exception:
            pass

    try:
        return _get_yfinance_news_sentiment(ticker, max_items=max_items)
    except Exception as exc:
        return {
            **_empty_result(),
            "error":        "News fetch failed. Try again later.",
            "error_detail": str(exc),
        }


def extract_market_drivers(news_result: dict, top_n: int = 5) -> list[dict]:
    """Return the top_n headlines with the strongest absolute sentiment score."""
    return sorted(
        news_result.get("articles", []),
        key=lambda a: abs(a["sentiment_score"]),
        reverse=True,
    )[:top_n]
