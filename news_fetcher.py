# news_fetcher.py
# Fetches financial news for individual stocks and the broader market
# using publicly available RSS feeds (no API key required).

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone


# RSS feeds used for general market news
_MARKET_NEWS_FEEDS = [
    {
        "name": "Reuters Business",
        "url": "https://feeds.reuters.com/reuters/businessNews",
    },
    {
        "name": "CNBC Finance",
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
    },
    {
        "name": "MarketWatch",
        "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    },
    {
        "name": "Investing.com",
        "url": "https://www.investing.com/rss/news.rss",
    },
]

_DATE_FORMATS = (
    "%a, %d %b %Y %H:%M:%S %Z",
    "%a, %d %b %Y %H:%M:%S %z",
)

_REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0"}
_TIMEOUT = 6


def _parse_pub_date(raw: str) -> tuple:
    """Return (timestamp_float, formatted_string) for a RSS pubDate string."""
    for fmt in _DATE_FORMATS:
        try:
            dt = datetime.strptime(raw.strip(), fmt)
            ts = dt.replace(tzinfo=timezone.utc).timestamp() if dt.tzinfo is None else dt.timestamp()
            return ts, dt.strftime("%d %b %Y, %H:%M")
        except ValueError:
            continue
    return 0.0, raw[:16] if raw else "-"


def fetch_stock_news(ticker: str, company_name: str = "", max_articles: int = 6) -> list:
    """
    Fetch recent news for a single stock ticker via Google News RSS.

    Parameters:
        ticker (str): Ticker symbol; market suffix (.SS, .HK, etc.) is stripped
                      before searching.
        company_name (str): Optional display name to refine the search query.
        max_articles (int): Maximum number of articles to return.

    Returns:
        list[dict]: Articles with keys: title, link, source, published.
                    Empty list if the feed cannot be reached.
    """
    base_term = ticker.split(".")[0] if "." in ticker else ticker

    if company_name:
        query = f"{base_term} {company_name} stock"
    else:
        query = f"{base_term} stock"

    url = (
        "https://news.google.com/rss/search"
        f"?q={urllib.parse.quote(query)}&hl=en-US&gl=US&ceid=US:en"
    )

    articles = []
    try:
        req = urllib.request.Request(url, headers=_REQUEST_HEADERS)
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            root = ET.fromstring(resp.read())

        for item in root.findall(".//item")[:max_articles]:
            title   = item.findtext("title", "").strip()
            link    = item.findtext("link", "").strip()
            pub_raw = item.findtext("pubDate", "")
            source  = item.findtext("source", "Google News")

            if not title or not link:
                continue

            _, published = _parse_pub_date(pub_raw)
            articles.append({
                "title":     title,
                "link":      link,
                "source":    source,
                "published": published,
            })

    except Exception:
        pass

    return articles


def fetch_market_news(max_articles: int = 20) -> list:
    """
    Fetch general financial market news from multiple RSS feeds.

    Aggregates Reuters, CNBC, MarketWatch, and Investing.com, deduplicates
    by title, and returns results sorted newest-first.

    Parameters:
        max_articles (int): Total articles to return across all sources.

    Returns:
        list[dict]: Articles with keys: title, link, source, published.
    """
    seen: set = set()
    articles = []

    for feed in _MARKET_NEWS_FEEDS:
        try:
            req = urllib.request.Request(feed["url"], headers=_REQUEST_HEADERS)
            with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
                root = ET.fromstring(resp.read())

            for item in root.findall(".//item"):
                title   = item.findtext("title", "").strip()
                link    = item.findtext("link", "").strip()
                pub_raw = item.findtext("pubDate", "")

                if not title or not link:
                    continue

                key = title.lower()[:80]
                if key in seen:
                    continue
                seen.add(key)

                ts, published = _parse_pub_date(pub_raw)
                articles.append({
                    "title":     title,
                    "link":      link,
                    "source":    feed["name"],
                    "published": published,
                    "_ts":       ts,
                })

        except Exception:
            continue

    articles.sort(key=lambda x: x["_ts"], reverse=True)
    for a in articles:
        del a["_ts"]

    return articles[:max_articles]
