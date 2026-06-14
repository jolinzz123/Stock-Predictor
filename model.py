import numpy as np
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

LOOKBACK = 60
EPOCHS = 30
BATCH_SIZE = 32


def prepare_data(prices: np.ndarray, lookback: int = LOOKBACK):
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled = scaler.fit_transform(prices.reshape(-1, 1))

    X, y = [], []
    for i in range(lookback, len(scaled)):
        X.append(scaled[i - lookback:i, 0])
        y.append(scaled[i, 0])

    X = np.array(X).reshape(-1, lookback, 1)
    y = np.array(y)
    return X, y, scaler


def build_model(lookback: int = LOOKBACK) -> Sequential:
    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=(lookback, 1)),
        Dropout(0.2),
        LSTM(64, return_sequences=False),
        Dropout(0.2),
        Dense(32, activation="relu"),
        Dense(1),
    ])
    model.compile(optimizer="adam", loss="mean_squared_error")
    return model


class _ProgressCallback(tf.keras.callbacks.Callback):
    def __init__(self, total_epochs, fn):
        super().__init__()
        self._total = total_epochs
        self._fn = fn

    def on_epoch_end(self, epoch, logs=None):
        self._fn(epoch + 1, self._total)


def train_model(X, y, epochs: int = EPOCHS, batch_size: int = BATCH_SIZE, epoch_callback=None):
    model = build_model(X.shape[1])
    callbacks = [EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True)]
    if epoch_callback:
        callbacks.append(_ProgressCallback(epochs, epoch_callback))

    model.fit(
        X, y,
        epochs=epochs,
        batch_size=batch_size,
        validation_split=0.1,
        callbacks=callbacks,
        verbose=0,
    )
    return model
