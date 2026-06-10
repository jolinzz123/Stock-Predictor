========================================================
  STOCK PRICE PREDICTION SYSTEM
  AIT102 — Python and TensorFlow Programming
  Group Final Project
========================================================

DESCRIPTION
-----------
This application uses a deep learning LSTM (Long Short-Term Memory)
neural network, built with TensorFlow/Keras, to predict future stock
closing prices. Historical price data is fetched live from Yahoo Finance.

The program accepts a stock ticker symbol and a forecast horizon from
the user, trains an LSTM model on 2 years of data, evaluates it on a
held-out test set, and outputs both numerical forecasts and saved charts.


HOW TO RUN
----------
1. Make sure Python 3.9 or later is installed.

2. Install all required packages by running:

       pip install -r requirements.txt

3. Start the program:

       python main.py

4. Follow the on-screen prompts:
   - Enter a stock ticker (e.g. AAPL, TSLA, GOOG, MSFT, AMZN)
   - Enter the number of days to forecast (1–30)
   - Optionally reuse a previously saved model

5. When the program finishes, charts are saved in the 'assets/' folder.


FILE STRUCTURE
--------------
stock_predictor/
│
├── main.py            — Program entry point; run this file
│                        (lets user choose Desktop or Web interface)
│
├── app_desktop.py     — Tkinter desktop GUI window
├── app_web.py         — Flask web backend and news API
│
├── data_fetcher.py    — Downloads and preprocesses stock data (yfinance)
├── model.py           — Defines, trains, and saves the LSTM model
├── predictor.py       — Generates test-set and future predictions
├── visualizer.py      — Creates and saves matplotlib charts
│
├── templates/
│   └── index.html     — Web interface frontend (HTML/CSS/JS)
│
├── static/            — Static assets folder (reserved for future use)
│
├── saved_model/       — Trained model is stored here (auto-created)
├── assets/            — Output charts are saved here (auto-created)
│
├── requirements.txt   — Python package dependencies
└── README.txt         — This file



REQUIREMENTS
------------
- Python >= 3.9
- Internet connection (required to fetch stock data from Yahoo Finance)
- Minimum ~500MB disk space (for TensorFlow and model files)
- Webcam / GPU not required; CPU training is fully supported


SAMPLE TICKERS TO TRY
----------------------
  AAPL    Apple Inc.
  TSLA    Tesla Inc.
  GOOG    Alphabet (Google)
  MSFT    Microsoft Corporation
  AMZN    Amazon.com
  NVDA    NVIDIA Corporation
  META    Meta Platforms
  BABA    Alibaba Group


OUTPUT FILES
------------
After each prediction run, the following files are saved in assets/:

  <TICKER>_prediction.png  — Full chart: training history, test predictions,
                              and future forecast overlay
  <TICKER>_forecast.png    — Zoomed chart: last 90 days + future forecast
  <TICKER>_loss.png        — Model training/validation loss curve


DISCLAIMER
----------
This application is built for educational purposes as part of an
academic coursework project. All predictions are outputs of a machine
learning model and do NOT constitute financial advice. Do not make
real investment decisions based on this tool.


KNOWN LIMITATIONS
-----------------
- Prediction accuracy degrades beyond ~10 days (compounding error in
  recursive forecasting is expected behaviour for LSTM models).
- Stocks with less than 100 days of trading history are not supported.
- Model training takes 1–3 minutes on CPU depending on hardware.
- Weekend and public holiday dates are automatically skipped in forecasts
  (business-day calendar is used).
========================================================
