import numpy as np
from model import prepare_data, train_model, LOOKBACK


def run_prediction(prices: np.ndarray, future_days: int = 7, epoch_callback=None) -> dict:
    X, y, scaler = prepare_data(prices)

    # 80% train, 20% test
    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train = y[:split]

    model = train_model(X_train, y_train, epoch_callback=epoch_callback)

    # Predictions on test portion only (true generalization)
    test_preds = scaler.inverse_transform(
        model.predict(X_test, verbose=0)
    ).flatten()

    # Index in the original price array where the test set begins
    test_start_idx = LOOKBACK + split

    # Autoregressive forecast for future_days
    scaled_all = scaler.transform(prices.reshape(-1, 1))
    seq = scaled_all[-LOOKBACK:].reshape(1, LOOKBACK, 1).copy()
    future_preds = []
    for _ in range(future_days):
        pred_scaled = model.predict(seq, verbose=0)[0, 0]
        future_preds.append(pred_scaled)
        seq = np.roll(seq, -1, axis=1)
        seq[0, -1, 0] = pred_scaled

    future_preds = scaler.inverse_transform(
        np.array(future_preds).reshape(-1, 1)
    ).flatten()

    return {
        "test_preds": test_preds,
        "test_start_idx": test_start_idx,
        "train_end_idx": test_start_idx,  # index where training ends and test begins
        "future_preds": future_preds,
    }
