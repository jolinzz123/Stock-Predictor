import numpy as np
import pandas as pd

from model import (
    LOOKBACK,
    FUTURE_DAYS,
    build_feature_frame,
    make_supervised_data,
    predict_linear_model,
    predict_residual_lstm,
    train_linear_model,
    train_residual_lstm,
    train_predict_arima,
)


def _as_price_frame(data) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        close = np.asarray(data, dtype=float).reshape(-1)
        df = pd.DataFrame(
            {
                "Open": close,
                "High": close,
                "Low": close,
                "Close": close,
                "Adj Close": close,
                "Volume": 0.0,
            }
        )

    close = df["Close"].astype(float)
    for col in ["Open", "High", "Low", "Adj Close"]:
        if col not in df:
            df[col] = close
        df[col] = df[col].astype(float).fillna(close)
    if "Volume" not in df:
        df["Volume"] = 0.0
    df["Volume"] = df["Volume"].astype(float).fillna(0.0)
    return df[["Open", "High", "Low", "Close", "Adj Close", "Volume"]].dropna(subset=["Close"])


def _flat_from_window(window: pd.DataFrame) -> np.ndarray:
    latest = window.iloc[-1].to_numpy()
    short_mean = window.tail(5).mean().to_numpy()
    medium_mean = window.tail(12).mean().to_numpy()
    short_std = window.tail(5).std(ddof=0).to_numpy()
    raw_close_window = window["Close"].tail(10).to_numpy()
    return np.concatenate([latest, short_mean, medium_mean, short_std, raw_close_window])


def _forecast_future(
    df: pd.DataFrame,
    linear_model,
    linear_scaler,
    residual_model,
    residual_feature_scaler,
    residual_target_scaler,
) -> np.ndarray:
    feature_frame = build_feature_frame(df)
    window = feature_frame.tail(LOOKBACK)
    X_seq = window.to_numpy().reshape(1, LOOKBACK, -1)
    X_flat = _flat_from_window(window).reshape(1, -1)

    baseline = predict_linear_model(linear_model, linear_scaler, X_flat)[0]   # (future_days,)
    residual = predict_residual_lstm(
        residual_model, residual_feature_scaler, residual_target_scaler, X_seq
    )[0]   # (future_days,)
    return baseline + residual


def run_prediction(data, future_days: int = FUTURE_DAYS, epoch_callback=None) -> dict:
    df = _as_price_frame(data)
    if len(df) < LOOKBACK + 30:
        raise ValueError("Not enough historical data to train the model.")

    feature_frame = build_feature_frame(df)
    X_seq, X_flat, y = make_supervised_data(feature_frame, future_days=future_days)

    split = int(len(y) * 0.8)
    X_seq_train, X_seq_test = X_seq[:split], X_seq[split:]
    X_flat_train, X_flat_test = X_flat[:split], X_flat[split:]
    y_train = y[:split]

    linear_model, linear_scaler = train_linear_model(X_flat_train, y_train)
    train_baseline = predict_linear_model(linear_model, linear_scaler, X_flat_train)
    test_baseline = predict_linear_model(linear_model, linear_scaler, X_flat_test)

    residual_model, residual_feature_scaler, residual_target_scaler = train_residual_lstm(
        X_seq_train,
        y_train - train_baseline,
        epoch_callback=epoch_callback,
    )
    test_residual = predict_residual_lstm(
        residual_model,
        residual_feature_scaler,
        residual_target_scaler,
        X_seq_test,
    )
    test_preds_7d = test_baseline + test_residual  # (N_test, 7)
    test_preds = test_preds_7d[:, 0]              # (N_test,) for historical chart
    y_test = y[split:]                             # (N_test, 7) actual values

    lstm_ridge_preds = _forecast_future(
        df,
        linear_model,
        linear_scaler,
        residual_model,
        residual_feature_scaler,
        residual_target_scaler,
    )
    arima_preds = train_predict_arima(df["Close"].to_numpy(), future_days=future_days)
    future_preds = 0.5 * lstm_ridge_preds + 0.5 * arima_preds

    test_start_idx = LOOKBACK + split
    return {
        "test_preds": test_preds,
        "test_preds_7d": test_preds_7d,
        "y_test": y_test,
        "test_start_idx": test_start_idx,
        "train_end_idx": test_start_idx,
        "future_preds": future_preds,
    }
