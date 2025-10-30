import threading
import time
import requests
import pandas as pd
import numpy as np
import pytz
from datetime import datetime
from flask import Flask

# ------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------
API_KEY = "d3251l1r01qn0gi2ens0d3251r01qn0gi2ensg"
STOCKS = ["NVDA", "AAPL", "TSLA"]
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"
GOOGLE_SHEETS_WEBAPP_URL = "YOUR_GOOGLE_SHEETS_WEBAPP_URL"

# Market hours (UK time)
MARKET_OPEN = (14, 30)
MARKET_CLOSE = (21, 0)

# Flask app for Render health check
app = Flask(__name__)


# ------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------
def get_stock_data(symbol):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1h&apikey={API_KEY}&outputsize=100"
    response = requests.get(url)
    data = response.json()
    if "values" not in data:
        raise ValueError(f"Error fetching {symbol}: {data}")
    df = pd.DataFrame(data["values"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime")
    df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].astype(float)
    return df


def calculate_indicators(df):
    # SMA
    df["SMA20"] = df["close"].rolling(window=20).mean()
    df["SMA50"] = df["close"].rolling(window=50).mean()

    # RSI
    delta = df["close"].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=14).mean()
    avg_loss = pd.Series(loss).rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    exp1 = df["close"].ewm(span=12, adjust=False).mean()
    exp2 = df["close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = exp1 - exp2
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    # Bollinger Bands
    df["MiddleBand"] = df["close"].rolling(window=20).mean()
    df["UpperBand"] = df["MiddleBand"] + 2 * df["close"].rolling(window=20).std()
    df["LowerBand"] = df["MiddleBand"] - 2 * df["close"].rolling(window=20).std()
    return df


def analyze_signals(df):
    last = df.iloc[-1]
    signals = []

    if last["RSI"] < 30 and last["close"] < last["LowerBand"]:
        signals.append("Strong Buy")
    elif last["RSI"] < 40 and last["SMA20"] > last["SMA50"]:
        signals.append("Weak Buy")
    elif last["RSI"] > 70 and last["close"] > last["UpperBand"]:
        signals.append("Strong Sell")
    elif last["RSI"] > 60 and last["SMA20"] < last["SMA50"]:
        signals.append("Weak Sell")
    else:
        signals.append("Hold")

    return signals[-1]


def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Error sending Telegram alert:", e)


def log_to_google_sheets(symbol, signal, price):
    payload = {"symbol": symbol, "signal": signal, "price": price}
    try:
        requests.post(GOOGLE_SHEETS_WEBAPP_URL, json=payload)
    except Exception as e:
        print("Error logging to Google Sheets:", e)


def is_market_open():
    now = datetime.now(pytz.timezone("Europe/London"))
    open_time = now.replace(hour=MARKET_OPEN[0], minute=MARKET_OPEN[1], second=0)
    close_time = now.replace(hour=MARKET_CLOSE[0], minute=MARKET_CLOSE[1], second=0)
    return open_time <= now <= close_time


# ------------------------------------------------------
# MAIN BOT LOOP
# ------------------------------------------------------
def run_stock_bot():
    while True:
        if is_market_open():
            print("🟢 Market open — checking signals...")
            summary = []

            for stock in STOCKS:
                try:
                    df = get_stock_data(stock)
                    df = calculate_indicators(df)
                    signal = analyze_signals(df)
                    price = df["close"].iloc[-1]
                    log_to_google_sheets(stock, signal, price)
                    summary.append(f"{stock}: {signal}")

                except Exception as e:
                    print(f"Error with {stock}:", e)

            if summary:
                alert_message = "📊 Stock Signals:\n" + "\n".join(summary)
                send_telegram_alert(alert_message)
                print(alert_message)
        else:
            print("🔴 Market closed — sleeping...")

        time.sleep(3600)  # check every hour


# ------------------------------------------------------
# FLASK APP (RENDER HEALTH CHECK)
# ------------------------------------------------------
@app.route("/")
def home():
    return "✅ Stock Signal Bot is running on Render."


# ------------------------------------------------------
# ENTRY POINT
# ------------------------------------------------------
if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_stock_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # Keep web server running for Render
    app.run(host="0.0.0.0", port=8080)
