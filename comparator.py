import math
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error

from data_fetcher import fetch_stock_data
from predictor import run_prediction
from news_analyzer import get_news_sentiment


def get_comparison_data(ticker_a, ticker_b):
    """Compare two stocks by fetching their data."""

    if not ticker_a or not ticker_b:
        return None

    ticker_a = ticker_a.upper()
    ticker_b = ticker_b.upper()

    data_a = get_stock_data(ticker_a)
    data_b = get_stock_data(ticker_b)

    if data_a is None and data_b is None:
        return None

    return {ticker_a: data_a, ticker_b: data_b}


def get_stock_data(ticker):
    """Get all comparison data for a single stock."""

    stock_data = {}
    history = None

    try:
        history = fetch_stock_data(ticker)
        if history is not None and len(history) > 0:
            stock_data["current_price"] = float(history["Close"].iloc[-1])
            stock_data["historical_prices_30d"] = history["Close"].tail(30).tolist()
        else:
            stock_data["current_price"] = None
            stock_data["historical_prices_30d"] = None
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        stock_data["current_price"] = None
        stock_data["historical_prices_30d"] = None

    try:
        if history is not None and len(history) > 0:
            result = run_prediction(history, future_days=7)

            future_preds = result.get("future_preds")
            if future_preds is not None:
                pred_list = future_preds.tolist() if isinstance(future_preds, np.ndarray) else list(future_preds)
                stock_data["predicted_price_7d"] = pred_list[:7]
            else:
                stock_data["predicted_price_7d"] = None

            y_test = result.get("y_test")
            test_preds = result.get("test_preds")
            if y_test is not None and test_preds is not None and len(y_test) > 0:
                stock_data["backtest_mse"] = float(mean_squared_error(y_test[:, 0], test_preds))
            else:
                stock_data["backtest_mse"] = None
        else:
            stock_data["predicted_price_7d"] = None
            stock_data["backtest_mse"] = None
    except Exception as e:
        print(f"Error running prediction for {ticker}: {e}")
        stock_data["predicted_price_7d"] = None
        stock_data["backtest_mse"] = None

    try:
        sentiment = get_news_sentiment(ticker)
        if sentiment is not None:
            stock_data["sentiment_score"] = float(sentiment.get("aggregate_score", 0.0))
        else:
            stock_data["sentiment_score"] = None
    except Exception as e:
        print(f"Error getting sentiment for {ticker}: {e}")
        stock_data["sentiment_score"] = None

    return stock_data


def _norm_pct(value, lo=-10, hi=10):
    if value is None:
        return None
    clamped = max(lo, min(hi, value))
    return round((clamped - lo) / (hi - lo) * 100, 1)

def _norm_inverse(value, lo=0, hi=5):
    if value is None:
        return None
    clamped = max(lo, min(hi, value))
    return round((hi - clamped) / (hi - lo) * 100, 1)

def _to_stars(score100):
    if score100 is None:
        return chr(8212)
    filled = max(1, min(5, round(score100 / 20)))
    return chr(9733) * filled + chr(9734) * (5 - filled)


def _calc_volatility(prices):

    """Calculate standard deviation of daily returns from a price list."""
    if prices is None or len(prices) < 2:
        return None
    returns = [(prices[i] - prices[i-1]) / prices[i-1] * 100 for i in range(1, len(prices))]
    if len(returns) < 2:
        return None
    mr = sum(returns) / len(returns)
    var = sum((r - mr)**2 for r in returns) / (len(returns) - 1)
    return math.sqrt(var)


def _calc_price_trend(prices):
    """Calculate slope of recent prices using simple linear regression."""
    if prices is None or len(prices) < 2:
        return None
    n = len(prices)
    xs = list(range(n))
    ys = prices
    sx = sum(xs)
    sy = sum(ys)
    sxy = sum(x * y for x, y in zip(xs, ys))
    sx2 = sum(x * x for x in xs)
    d = n * sx2 - sx * sx
    if d == 0:
        return 0.0
    return (n * sxy - sx * sy) / d


def compute_scores(data_a, data_b):
    """Compare two stocks across 5 dimensions and return which one wins each."""
    scores = {}

    # Predicted Return (higher is better)
    try:
        aok = data_a.get("predicted_price_7d") is not None and data_a.get("current_price") is not None
        bok = data_b.get("predicted_price_7d") is not None and data_b.get("current_price") is not None
        if aok and bok:
            ra = (data_a["predicted_price_7d"][-1] - data_a["current_price"]) / data_a["current_price"] * 100
            rb = (data_b["predicted_price_7d"][-1] - data_b["current_price"]) / data_b["current_price"] * 100
            w = "a" if ra > rb else ("b" if rb > ra else "tie")
            scores["predicted_return"] = {"a": round(ra, 2), "b": round(rb, 2), "winner": w, "label": "Predicted Return (7d)", "norm_a": _norm_pct(ra), "norm_b": _norm_pct(rb), "stars_a": _to_stars(_norm_pct(ra)), "stars_b": _to_stars(_norm_pct(rb))}
        else:
            scores["predicted_return"] = {"a": "N/A", "b": "N/A", "winner": "tie", "label": "Predicted Return (7d)"}
    except Exception as e:
        print(f"Error: {e}")
        scores["predicted_return"] = {"a": "N/A", "b": "N/A", "winner": "tie", "label": "Predicted Return (7d)"}

    # Risk / Volatility (lower is better)
    try:
        va = _calc_volatility(data_a.get("historical_prices_30d"))
        vb = _calc_volatility(data_b.get("historical_prices_30d"))
        if va is not None and vb is not None:
            w = "a" if va < vb else ("b" if vb < va else "tie")
            scores["volatility"] = {"a": round(va, 3), "b": round(vb, 3), "winner": w, "label": "Risk (Volatility)", "norm_a": _norm_inverse(va), "norm_b": _norm_inverse(vb), "stars_a": _to_stars(_norm_inverse(va)), "stars_b": _to_stars(_norm_inverse(vb))}
        else:
            scores["volatility"] = {"a": "N/A", "b": "N/A", "winner": "tie", "label": "Risk (Volatility)"}
    except Exception as e:
        print(f"Error: {e}")
        scores["volatility"] = {"a": "N/A", "b": "N/A", "winner": "tie", "label": "Risk (Volatility)"}

    # Model Confidence (lower MSE is better)
    try:
        ma = data_a.get("backtest_mse")
        mb = data_b.get("backtest_mse")
        if ma is not None and mb is not None:
            w = "a" if ma < mb else ("b" if mb < ma else "tie")
            scores["model_confidence"] = {"a": round(ma, 4), "b": round(mb, 4), "winner": w, "label": "Model Confidence (MSE)"}
            ref = max(ma, mb) * 2
            if ref > 0:
                scores["model_confidence"]["norm_a"] = round(max(0, (1 - ma / ref)) * 100, 1)
                scores["model_confidence"]["norm_b"] = round(max(0, (1 - mb / ref)) * 100, 1)
            else:
                scores["model_confidence"]["norm_a"] = 50.0
                scores["model_confidence"]["norm_b"] = 50.0
            scores["model_confidence"]["stars_a"] = _to_stars(scores["model_confidence"]["norm_a"])
            scores["model_confidence"]["stars_b"] = _to_stars(scores["model_confidence"]["norm_b"])
        else:
            scores["model_confidence"] = {"a": "N/A", "b": "N/A", "winner": "tie", "label": "Model Confidence (MSE)"}
    except Exception as e:
        print(f"Error: {e}")
        scores["model_confidence"] = {"a": "N/A", "b": "N/A", "winner": "tie", "label": "Model Confidence (MSE)"}

    # News Sentiment (higher is better)
    try:
        sa = data_a.get("sentiment_score")
        sb = data_b.get("sentiment_score")
        if sa is not None and sb is not None:
            w = "a" if sa > sb else ("b" if sb > sa else "tie")
            scores["sentiment"] = {"a": round(sa, 3), "b": round(sb, 3), "winner": w, "label": "News Sentiment", "norm_a": _norm_pct(sa, lo=-1, hi=1), "norm_b": _norm_pct(sb, lo=-1, hi=1), "stars_a": _to_stars(_norm_pct(sa, lo=-1, hi=1)), "stars_b": _to_stars(_norm_pct(sb, lo=-1, hi=1))}
        else:
            scores["sentiment"] = {"a": "N/A", "b": "N/A", "winner": "tie", "label": "News Sentiment"}
    except Exception as e:
        print(f"Error: {e}")
        scores["sentiment"] = {"a": "N/A", "b": "N/A", "winner": "tie", "label": "News Sentiment"}

    # Price Trend (higher slope is better)
    try:
        ta = _calc_price_trend(data_a.get("historical_prices_30d"))
        tb = _calc_price_trend(data_b.get("historical_prices_30d"))
        if ta is not None and tb is not None:
            w = "a" if ta > tb else ("b" if tb > ta else "tie")
            scores["price_trend"] = {"a": round(ta, 4), "b": round(tb, 4), "winner": w, "label": "Price Trend (Momentum)", "norm_a": _norm_pct(ta, lo=-2, hi=2), "norm_b": _norm_pct(tb, lo=-2, hi=2), "stars_a": _to_stars(_norm_pct(ta, lo=-2, hi=2)), "stars_b": _to_stars(_norm_pct(tb, lo=-2, hi=2))}
        else:
            scores["price_trend"] = {"a": "N/A", "b": "N/A", "winner": "tie", "label": "Price Trend (Momentum)"}
    except Exception as e:
        print(f"Error: {e}")
        scores["price_trend"] = {"a": "N/A", "b": "N/A", "winner": "tie", "label": "Price Trend (Momentum)"}

    return scores


def determine_winner(ticker_a, ticker_b, scores):
    """Weight each dimension and return the stock with the highest total score."""

    wmap = {"predicted_return": 3, "volatility": 2, "model_confidence": 2, "sentiment": 2, "price_trend": 1}

    sa = 0
    sb = 0
    total = 0
    breakdown = []

    for dk, dd in scores.items():
        w = wmap.get(dk, 1)
        total += w
        ww = dd.get("winner")

        if ww == "a":
            sa += w
            breakdown.append(f"  +{w} {dd['label']}: {ticker_a} wins ({dd['a']} vs {dd['b']})")
        elif ww == "b":
            sb += w
            breakdown.append(f"  +{w} {dd['label']}: {ticker_b} wins ({dd['a']} vs {dd['b']})")
        else:
            sa += w / 2
            sb += w / 2
            breakdown.append(f"  +{w/2} {dd['label']}: Tie ({dd['a']} vs {dd['b']})")

    if sa > sb:
        winner = ticker_a
        reason = f"{ticker_a} scores {sa:.1f}/{total} vs {ticker_b} scores {sb:.1f}/{total}. {ticker_a} outperforms in enough dimensions to be the better pick."
        return {"winner": winner, "score_a": sa, "score_b": sb, "total": total, "reason": reason, "breakdown": breakdown}
    elif sb > sa:
        winner = ticker_b
        reason = f"{ticker_b} scores {sb:.1f}/{total} vs {ticker_a} scores {sa:.1f}/{total}. {ticker_b} outperforms in enough dimensions to be the better pick."
        return {"winner": winner, "score_a": sa, "score_b": sb, "total": total, "reason": reason, "breakdown": breakdown}
    else:
        winner = None
        advices = []
        vol = scores.get("volatility", {})
        ret = scores.get("predicted_return", {})
        sent = scores.get("sentiment", {})
        mse = scores.get("model_confidence", {})

        if vol.get("winner") == "a" and isinstance(vol.get("a"), (int, float)):
            advices.append(f"{ticker_a} has lower volatility, suitable for conservative investors.")
        elif vol.get("winner") == "b" and isinstance(vol.get("b"), (int, float)):
            advices.append(f"{ticker_b} has lower volatility, suitable for conservative investors.")

        if ret.get("winner") == "a" and isinstance(ret.get("a"), (int, float)):
            advices.append(f"{ticker_a} has stronger growth forecast, better for growth-oriented investors.")
        elif ret.get("winner") == "b" and isinstance(ret.get("b"), (int, float)):
            advices.append(f"{ticker_b} has stronger growth forecast, better for growth-oriented investors.")

        if sent.get("winner") == "a" and isinstance(sent.get("a"), (int, float)):
            advices.append(f"{ticker_a} has more positive news sentiment.")
        elif sent.get("winner") == "b" and isinstance(sent.get("b"), (int, float)):
            advices.append(f"{ticker_b} has more positive news sentiment.")

        if mse.get("winner") == "a" and isinstance(mse.get("a"), (int, float)):
            advices.append(f"{ticker_a} has more reliable model predictions.")
        elif mse.get("winner") == "b" and isinstance(mse.get("b"), (int, float)):
            advices.append(f"{ticker_b} has more reliable model predictions.")
        reason = "Both stocks score equally. " + (" ".join(advices) if advices else "Consider your own risk preference.")
        return {"winner": winner, "score_a": sa, "score_b": sb, "total": total, "reason": reason, "breakdown": breakdown}
    

def compare_stocks(ticker_a, ticker_b):
    """Fetch two stocks, compare across multiple dimensions, and recommend the better one."""

    print(f"Fetching data for {ticker_a} and {ticker_b}...")
    cd = get_comparison_data(ticker_a, ticker_b)
    if cd is None:
        print("Could not get data for one or both stocks.")
        return None

    tickers = list(cd.keys())
    ta, tb = tickers[0], tickers[1]
    da, db = cd[ta], cd[tb]
    if da is None:
        print(f"No data available for {ta}")
        return None
    if db is None:
        print(f"No data available for {tb}")
        return None

    print("Comparing across dimensions...")
    scores = compute_scores(da, db)
    print("Calculating final recommendation...")
    wr = determine_winner(ta, tb, scores)

    result = {
        "ticker_a": ta, "ticker_b": tb,
        "data_a": da, "data_b": db,
        "scores": scores,
        "winner": wr if wr else None,
    }
    result["score_a"] = wr.get("score_a", 0) if wr else 0
    result["score_b"] = wr.get("score_b", 0) if wr else 0
    result["total"] = wr.get("total", 1) if wr else 1
    result["reason"] = wr.get("reason", "") if wr else ""
    result["breakdown"] = wr.get("breakdown", []) if wr else []

    return result


def print_comparison_report(report):
    """Print a formatted comparison report to the console."""

    if report is None:
        print("No comparison report available.")
        return

    ta = report["ticker_a"]
    tb = report["ticker_b"]
    scores = report["scores"]
    wr = report["winner"]

    print("=" * 60)
    print("          STOCK COMPARISON REPORT")
    print("=" * 60)
    print()

    print(f"Comparing:  {ta}  vs  {tb}")
    print()

    pa = report["data_a"].get("current_price", "N/A")
    pb = report["data_b"].get("current_price", "N/A")
    print(f"  {ta:>6}  Current Price:  {pa}")
    print(f"  {tb:>6}  Current Price:  {pb}")
    print()

    print("-" * 60)
    print("  Dimension Comparison")
    print("-" * 60)
    print(f"  {'Dimension':<30} {ta:>12} {tb:>12} {'Winner':>8}")
    print("  " + "-" * 62)

    for dk, dd in scores.items():
        lab = dd["label"]
        av = dd["a"]; bv = dd["b"]; w = dd["winner"]
        as_ = f"{av:>12}" if isinstance(av, (int, float)) else f"{str(av):>12}"
        bs_ = f"{bv:>12}" if isinstance(bv, (int, float)) else f"{str(bv):>12}"
        ws_ = f"  {ta}" if w == "a" else (f"  {tb}" if w == "b" else "   Tie")
        print(f"  {lab:<30} {as_} {bs_} {ws_:>8}")

    print()

    print("=" * 60)
    print("  FINAL RECOMMENDATION")
    print("=" * 60)
    if wr["winner"] is not None:
        print(f"  Recommended Stock:  {wr['winner']}")
        print(f"  Score:             {wr['score_a']:.1f} / {wr['total']} (Stock A)")
        print(f"                     {wr['score_b']:.1f} / {wr['total']} (Stock B)")
    else:
        print(f"  Result: It is a tie!")
        print(f"  Score:  {wr['score_a']:.1f} / {wr['total']} each")
    print()

    print(f"  Reason:")
    print(f"    {wr['reason']}")
    print()

    print("  Scoring Breakdown:")
    for line in wr["breakdown"]:
        print(line)

    print()
    print("  Disclaimer: This is for educational purposes only.")
    print("=" * 60)
