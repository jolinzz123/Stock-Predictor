import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.linear_model import RidgeCV
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
from tensorflow.keras.models import Sequential
from sklearn.preprocessing import MinMaxScaler

LOOKBACK = 36
FUTURE_DAYS = 7
EPOCHS = 45
BATCH_SIZE = 16

FEATURE_COLUMNS = [
    "Open",
    "High",
    "Low",
    "Close",
    "Adj Close",
    "Volume",
    "Return_1",
    "Return_2",
    "Return_3",
    "Return_5",
    "Delta_1",
    "Delta_2",
    "Delta_3",
    "Delta_5",
    "Momentum_3",
    "Momentum_5",
    "Momentum_10",
    "CloseToSMA_5",
    "CloseToSMA_10",
    "CloseToSMA_20",
    "Volatility_5",
    "Volatility_10",
    "Volatility_20",
    "Position_10",
    "Position_20",
    "RangePct",
    "BodyPct",
    "GapPct",
    "RSI_14",
    "MACD",
    "MACDSignal",
    "MACDHist",
    "ATR_14",
    "VolumeChange_1",
    "VolumeToSMA_5",
    "VolumeToSMA_20",
]


def _safe_div(numerator, denominator):
    return numerator / denominator.replace(0, np.nan)


def _rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = (-delta.clip(upper=0)).rolling(window).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def build_feature_frame(data) -> pd.DataFrame:
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

    df = df.sort_index()
    close = df["Close"].astype(float)
    for col in ["Open", "High", "Low", "Adj Close"]:
        if col not in df:
            df[col] = close
        df[col] = df[col].astype(float).fillna(close)
    if "Volume" not in df:
        df["Volume"] = 0.0
    df["Volume"] = df["Volume"].astype(float).fillna(0.0)

    high = df["High"]
    low = df["Low"]
    open_ = df["Open"]
    volume = df["Volume"]

    features = df[["Open", "High", "Low", "Close", "Adj Close", "Volume"]].copy()
    for period in [1, 2, 3, 5]:
        features[f"Return_{period}"] = close.pct_change(period)
        features[f"Delta_{period}"] = close.diff(period)

    for period in [3, 5, 10]:
        features[f"Momentum_{period}"] = _safe_div(close - close.shift(period), close.shift(period))

    for period in [5, 10, 20]:
        sma = close.rolling(period).mean()
        features[f"CloseToSMA_{period}"] = _safe_div(close - sma, sma)
        features[f"Volatility_{period}"] = close.pct_change().rolling(period).std()

    for period in [10, 20]:
        rolling_high = high.rolling(period).max()
        rolling_low = low.rolling(period).min()
        features[f"Position_{period}"] = _safe_div(close - rolling_low, rolling_high - rolling_low)

    features["RangePct"] = _safe_div(high - low, close)
    features["BodyPct"] = _safe_div(close - open_, open_)
    features["GapPct"] = _safe_div(open_ - close.shift(1), close.shift(1))
    features["RSI_14"] = _rsi(close)

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    features["MACD"] = ema12 - ema26
    features["MACDSignal"] = features["MACD"].ewm(span=9, adjust=False).mean()
    features["MACDHist"] = features["MACD"] - features["MACDSignal"]

    true_range = pd.concat(
        [(high - low), (high - close.shift(1)).abs(), (low - close.shift(1)).abs()],
        axis=1,
    ).max(axis=1)
    features["ATR_14"] = true_range.rolling(14).mean()
    features["VolumeChange_1"] = volume.pct_change()
    features["VolumeToSMA_5"] = _safe_div(volume, volume.rolling(5).mean()) - 1
    features["VolumeToSMA_20"] = _safe_div(volume, volume.rolling(20).mean()) - 1

    features = features.replace([np.inf, -np.inf], np.nan)
    features = features.ffill().fillna(0.0)
    return features[FEATURE_COLUMNS]


def make_supervised_data(feature_frame: pd.DataFrame, lookback: int = LOOKBACK, future_days: int = FUTURE_DAYS):
    features = feature_frame[FEATURE_COLUMNS].astype(float)
    target = feature_frame["Close"].astype(float).to_numpy()

    X_seq, X_flat, y = [], [], []
    for i in range(lookback, len(features) - future_days + 1):
        window = features.iloc[i - lookback:i]
        X_seq.append(window.to_numpy())

        latest = window.iloc[-1].to_numpy()
        short_mean = window.tail(5).mean().to_numpy()
        medium_mean = window.tail(12).mean().to_numpy()
        short_std = window.tail(5).std(ddof=0).to_numpy()
        raw_close_window = window["Close"].tail(10).to_numpy()
        X_flat.append(np.concatenate([latest, short_mean, medium_mean, short_std, raw_close_window]))
        y.append(target[i:i + future_days])

    return np.asarray(X_seq), np.asarray(X_flat), np.asarray(y)


class _ProgressCallback(tf.keras.callbacks.Callback):
    def __init__(self, total_epochs, fn):
        super().__init__()
        self._total = total_epochs
        self._fn = fn

    def on_epoch_end(self, epoch, logs=None):
        self._fn(epoch + 1, self._total)


def train_linear_model(X_flat: np.ndarray, y: np.ndarray):
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_flat)
    model = RidgeCV(alphas=np.logspace(-4, 3, 24))
    model.fit(X_scaled, y)
    return model, scaler


def predict_linear_model(model, scaler, X_flat: np.ndarray) -> np.ndarray:
    return model.predict(scaler.transform(X_flat))


def train_residual_lstm(
    X_seq: np.ndarray,
    residuals: np.ndarray,
    epochs: int = EPOCHS,
    batch_size: int = BATCH_SIZE,
    epoch_callback=None,
):
    future_days = residuals.shape[1]

    feature_scaler = StandardScaler()
    flat = X_seq.reshape(-1, X_seq.shape[-1])
    scaled = feature_scaler.fit_transform(flat).reshape(X_seq.shape)

    residual_scaler = StandardScaler()
    y = residual_scaler.fit_transform(residuals.reshape(-1, 1)).reshape(-1, future_days)

    model = Sequential(
        [
            Input(shape=(X_seq.shape[1], X_seq.shape[2])),
            LSTM(48, return_sequences=True),
            Dropout(0.12),
            LSTM(24),
            Dense(16, activation="relu"),
            Dense(future_days),
        ]
    )
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), loss="huber")

    callbacks = [
        EarlyStopping(monitor="val_loss", patience=7, restore_best_weights=True),
        ReduceLROnPlateau(monitor="val_loss", patience=3, factor=0.5, min_lr=0.0001),
    ]
    if epoch_callback:
        callbacks.append(_ProgressCallback(epochs, epoch_callback))

    model.fit(
        scaled,
        y,
        epochs=epochs,
        batch_size=batch_size,
        validation_split=0.15,
        callbacks=callbacks,
        verbose=0,
        shuffle=False,
    )
    return model, feature_scaler, residual_scaler


def predict_residual_lstm(model, feature_scaler, residual_scaler, X_seq: np.ndarray) -> np.ndarray:
    flat = X_seq.reshape(-1, X_seq.shape[-1])
    scaled = feature_scaler.transform(flat).reshape(X_seq.shape)
    pred_scaled = model.predict(scaled, verbose=0)  # (N, future_days)
    n, fd = pred_scaled.shape
    return residual_scaler.inverse_transform(pred_scaled.reshape(-1, 1)).reshape(n, fd)


def train_predict_arima(close_prices: np.ndarray, future_days: int = FUTURE_DAYS) -> np.ndarray:
    import warnings
    from statsmodels.tsa.arima.model import ARIMA

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = ARIMA(close_prices, order=(5, 1, 0)).fit()
        forecast = result.forecast(steps=future_days)
    return np.asarray(forecast)


def prepare_data(data, lookback: int = LOOKBACK):
    if isinstance(data, pd.DataFrame):
        close = data["Close"].to_numpy(dtype=float)
    else:
        close = np.asarray(data, dtype=float).reshape(-1)

    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled = scaler.fit_transform(close.reshape(-1, 1))

    X, y = [], []
    for i in range(lookback, len(scaled)):
        X.append(scaled[i - lookback:i, 0])
        y.append(scaled[i, 0])

    X = np.asarray(X).reshape(-1, lookback, 1)
    y = np.asarray(y)
    return X, y, scaler


def build_model(lookback: int = LOOKBACK) -> Sequential:
    model = Sequential(
        [
            Input(shape=(lookback, 1)),
            LSTM(64, return_sequences=True),
            Dropout(0.2),
            LSTM(64),
            Dropout(0.2),
            Dense(32, activation="relu"),
            Dense(1),
        ]
    )
    model.compile(optimizer="adam", loss="mean_squared_error")
    return model


def train_model(X, y, epochs: int = EPOCHS, batch_size: int = BATCH_SIZE, epoch_callback=None):
    model = build_model(X.shape[1])
    callbacks = [EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True)]
    if epoch_callback:
        callbacks.append(_ProgressCallback(epochs, epoch_callback))

    model.fit(
        X,
        y,
        epochs=epochs,
        batch_size=batch_size,
        validation_split=0.1,
        callbacks=callbacks,
        verbose=0,
        shuffle=False,
    )
    return model
