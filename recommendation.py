from __future__ import annotations

_SIGNAL_TIERS = [
    (0.60, "STRONG BUY", "#2ECC71"),
    (0.20, "BUY",        "#58D68D"),
    (-0.20, "HOLD",       "#F4D03F"),
    (-0.60, "REDUCE",     "#F39C12"),
]
_AVOID = ("AVOID", "#E74C3C")


def _resolve_signal(combined_score: float) -> tuple[str, str]:
    """Map a combined score to (signal label, hex colour)."""
    for threshold, label, color in _SIGNAL_TIERS:
        if combined_score >= threshold:
            return label, color
    return _AVOID


def generate_recommendation(
    current_price: float,
    future_predictions: list[float],
    news_result: dict,
    alpha: float = 0.7,   # forecast weight; sentiment weight = (1 - alpha)
) -> dict:
    """Combine XGBoost forecast and news sentiment into a single trading signal."""
    if not future_predictions:
        return {
            "signal":           "HOLD",
            "color":            "#F4D03F",
            "combined_score":   0.0,
            "prediction_score": 0.0,
            "sentiment_score":  0.0,
            "price_change_pct": 0.0,
            "predicted_price":  current_price,
            "alpha":            alpha,
            "rationale":        "",
        }

    predicted_price = future_predictions[-1]
    price_change_pct = (predicted_price - current_price) / current_price * 100

    # Normalise: a 10% price move maps to a score of ±1.0
    prediction_score = price_change_pct / 10
    sentiment_score = news_result.get("sentiment_score", 0.0)

    # α controls forecast vs sentiment contribution (https://arxiv.org/pdf/2603.05917)
    combined_score = prediction_score * alpha + sentiment_score * (1 - alpha)

    signal, color = _resolve_signal(combined_score)

    return {
        "signal":           signal,
        "color":            color,
        "combined_score":   round(combined_score, 4),
        "prediction_score": round(prediction_score, 4),
        "sentiment_score":  round(sentiment_score, 4),
        "price_change_pct": round(price_change_pct, 2),
        "predicted_price":  predicted_price,
        "alpha":            alpha,
        "rationale":        "",   # narrative built in page_detail.py
    }


def sensitivity_analysis(
    current_price: float,
    future_predictions: list[float],
    news_result: dict,
    alphas: list[float] | None = None,
) -> list[dict]:
    """Run generate_recommendation across a range of alpha values to study how the forecast/sentiment balance affects the final signal."""
    if alphas is None:
        alphas = [0.5, 0.6, 0.7, 0.8, 0.9]

    return [
        generate_recommendation(
            current_price, future_predictions, news_result, alpha=a)
        for a in alphas
    ]
