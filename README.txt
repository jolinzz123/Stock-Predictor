Foresight - Stock Price Predictor
=================================

A web app that predicts stock prices 7 days ahead using machine learning.
It pulls 2 years of data from Yahoo Finance, trains an ensemble model
(XGBoost + GRU + ARIMA), and also looks at recent news sentiment to
generate a buy/hold/avoid recommendation.


1. Requirements
---------------
- Python 3.10+
- Internet connection
- (Optional) Alpha Vantage API key for better news coverage.
  Without it the app still works, just uses yfinance for news instead.

Training is CPU-heavy (the GRU part). Expect 1-3 min per stock.


2. Setup & Run
--------------
1. Install dependencies:

    pip install -r requirements.txt

2. (Optional) Set up the Alpha Vantage API key:
   Copy .env.example to .env, put your key in there.
   Free key: https://www.alphavantage.co/support/#api-key

3. Start the app:

    streamlit run main.py

   Opens at http://localhost:8501 in your browser.

4. (Optional) Pre-train the watchlist so it loads faster next time:

    python pretrain.py


3. How it works
---------------
The pipeline goes like this:

  Data fetching (data_fetcher.py)
    Pulls OHLCV data from Yahoo Finance. Cleans up missing values -
    fills gaps in Open/High/Low from Close, sets missing Volume to 0,
    drops any row that has no Close price.

  Feature engineering (feature_engineer.py)
    Takes the clean price data and computes 37 features from it:
    returns, momentum, SMA ratios, volatility, RSI, MACD, ATR,
    volume indicators, candlestick patterns, and a sentiment score.

  Model training (model.py, predictor.py)
    Data gets split 70/10/20 in time order (no shuffling).
    First XGBoost runs on the 70%, then a GRU learns the residuals
    XGBoost missed. ARIMA runs separately as an independent forecast.
    A Ridge meta-learner (trained on the 10% slice) figures out the
    best way to combine all three. The final 20% is held out for
    evaluation. Everything predicts returns, not raw prices.

  News sentiment (news_analyzer.py)
    Grabs recent articles from Alpha Vantage (or yfinance as fallback),
    scores them with VADER, and outputs a sentiment label + confidence.

  Recommendation (recommendation.py)
    Mixes the predicted return with news sentiment into one signal:
    Strong Buy / Buy / Hold / Reduce / Avoid.

  Caching (cache_manager.py)
    Results get saved as .pkl files in cache/. They auto-expire after
    the next US market close (4 PM ET on weekdays).

  Comparison (comparator.py)
    Lets you compare two stocks across return, risk, confidence,
    sentiment, and trend. Picks a winner based on weighted scores.

  Charts (charts.py)
    All the Plotly figures - candlestick, forecast, backtest,
    historical close, radar, comparison overlay.

  Pages (page_watchlist.py, page_detail.py, page_compare.py)
    Each file is one page of the app.

  Entry point (main.py)
    Sets up the Streamlit config and routes between pages.

  Pre-training (pretrain.py)
    Batch trains all 20 watchlist tickers and caches the results.

  UI (theme/, ticker_strip.py)
    Theme tokens, CSS, icons, and the scrolling ticker bar.


4. Pages
--------
Watchlist (home):
  Shows 20 stocks with price, daily change, sparklines.
  Click a row to see the full analysis.

Detail page:
  Everything for one stock - forecast chart + table, backtest
  comparison, K-line with SMA overlays, 2Y history, news cards,
  sentiment breakdown, and the final recommendation signal.
  You can search any ticker from the search bar.

Compare page:
  Pick two stocks, get a side-by-side breakdown with scores,
  a radar chart, and an overlay of their 30-day history + 7-day
  forecast.


5. File overview
----------------
main.py               App entry point, page routing
data_fetcher.py       Stock data fetching (yfinance) and cleaning
feature_engineer.py   37 technical indicators
model.py              XGBoost, GRU, Ridge, ARIMA model code
predictor.py          Training pipeline, prediction logic
charts.py             Plotly chart builders
news_analyzer.py      News fetching + VADER sentiment
recommendation.py     Buy/Hold/Avoid signal generation
comparator.py         Two-stock comparison
cache_manager.py      Result caching with auto-expiry
pretrain.py           Batch pre-training script
ticker_strip.py       Scrolling ticker bar component
page_watchlist.py     Watchlist page
page_detail.py        Detail page
page_compare.py       Compare page
theme/                Colors, CSS, icons, UI components
cache/                Cached results (auto-generated)
.env                  API key config (see .env.example)
requirements.txt      Python dependencies


6. Tech stack
-------------
UI:          Streamlit
Charts:      Plotly
ML:          XGBoost, Keras/TensorFlow (GRU), statsmodels (ARIMA)
Stacking:    scikit-learn (RidgeCV)
Data:        yfinance (Yahoo Finance)
News:        Alpha Vantage + yfinance fallback
Sentiment:   VADER


7. Troubleshooting
------------------
"Missing ALPHAVANTAGE_API_KEY"
  -> Set up .env (see Setup step 2). Or just ignore it,
     the app falls back to yfinance.

"No data found for ticker 'XYZ'"
  -> Probably a wrong symbol. Use things like AAPL, MSFT, TSLA.

Training takes forever
  -> Normal on CPU, the GRU goes up to 120 epochs.
     Run pretrain.py ahead of time.

Port already in use
  -> streamlit run main.py --server.port 8502

