# Stock Price Prediction Web App

A machine learning web application that forecasts future stock closing prices using an **LSTM (Long Short-Term Memory)** neural network built with TensorFlow/Keras. Historical price data is fetched live from Yahoo Finance, and results are displayed in a browser-based interface built with Flask.

---

## How It Works

1. The user enters a stock ticker symbol (e.g. `AAPL`, `300750`) and selects a forecast horizon (1–30 days).
2. The app downloads 2 years of historical closing price data from Yahoo Finance.
3. An LSTM model is trained on 80% of the data and evaluated on the remaining 20%.
4. The model recursively predicts future prices and displays charts and a forecast table.
5. A news feed pulls the latest headlines related to the selected stock.

---

## Requirements

- Python >= 3.9
- Internet connection (required to fetch live stock data)
- ~500 MB disk space (for TensorFlow and saved model files)
- No GPU required — CPU training is fully supported

---

## Getting Started

### Step 1 — Download the code

Go to the GitHub repository and click **Code → Download ZIP**, then extract it.  
Or clone it directly:

```bash
git clone https://github.com/jolinzz123/stock_prediction
cd stock_prediction
```

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Run the web app

```bash
python main.py
```

Then open your browser at **http://127.0.0.1:5000**

---

## File Structure

```
stock_predictor/
│
├── main.py            — Entry point; launches the Flask web server
├── app_web.py         — Flask backend, API routes, and news feed
│
├── data_fetcher.py    — Downloads and preprocesses stock data (yfinance)
├── model.py           — Defines, trains, and saves the LSTM model
├── predictor.py       — Generates test-set and future price predictions
├── visualizer.py      — Creates and saves matplotlib charts
├── news_fetcher.py    — Fetches stock and market news via RSS
├── constants.py       — Shared constants and configuration
│
├── templates/
│   └── index.html     — Web frontend (HTML / CSS / JavaScript)
│
├── saved_model/       — Trained model saved here (auto-created)
├── assets/            — Output charts saved here (auto-created)
│
├── requirements.txt   — Python package dependencies
└── README.md          — This file
```

---

## Supported Tickers

| Market | Examples |
|--------|---------|
| US | `AAPL` `TSLA` `GOOG` `MSFT` `NVDA` `META` |
| A-share (Shanghai) | `600519` `601318` `600036` |
| A-share (Shenzhen) | `300750` `000858` `002594` |
| Hong Kong | `0700` `9988` `1810` |

---

## Output

After each prediction run, the following files are saved in `assets/`:

| File | Description |
|------|-------------|
| `<TICKER>_prediction.png` | Full chart: training history, test predictions, and future forecast |
| `<TICKER>_forecast.png` | Zoomed chart: last 90 days + future forecast with price annotations |
| `<TICKER>_loss.png` | Model training and validation loss curve across epochs |

---

## For Teammates — Pushing Changes to GitHub

```bash
# 1. Check what you changed
git status

# 2. Stage your files
git add .

# 3. Commit with a clear message
git commit -m "Describe what you changed"

# 4. Pull latest changes first (important!)
git pull origin main

# 5. Push your changes
git push origin main
```

> **Note:** `git push` will ask for your GitHub username and a **Personal Access Token** (not your password).  
> Generate one at: GitHub → Settings → Developer settings → Personal access tokens

---

## Disclaimer

This application is built for educational purposes as part of an academic coursework project. All predictions are outputs of a machine learning model and **do not constitute financial advice**. Do not make real investment decisions based on this tool.

---

## Known Limitations

- Prediction accuracy degrades beyond ~10 days due to compounding error in recursive forecasting.
- Stocks with fewer than 100 days of trading history are not supported.
- Model training takes 1–3 minutes on CPU depending on hardware.
- Weekend and public holiday dates are automatically skipped in forecasts (business-day calendar).
