import time
import threading
import requests
import pytz
from datetime import datetime
from flask import Flask

# --- Flask keepalive web server ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Stock Signal Bot is running ✅"

# --- Telegram + Twelve Data Config ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.twelvedata.com"

STOCKS = ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL"]

UK_TZ = pytz.timezone("Europe/London")
MARKET_OPEN_HOUR = 14
MARKET_CLOSE_HOUR = 21


def send_telegram(message):
    """Send alert to Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})


def get_indicator(symbol):
    """Fetch and calculate trading signals"""
    params = {"symbol": symbol, "interval": "1min", "apikey": API_KEY}

    rsi = requests.get(f"{BASE_URL}/rsi", params=params).json()
    macd = requests.get(f"{BASE_URL}/macd", params=params).json()
    bb = requests.get(f"{BASE_URL}/bbands", params=params).json()

    try:
        rsi_value = float(rsi["values"][0]["rsi"])
        macd_value = float(macd["values"][0]["macd"])
        macd_signal = float(macd["values"][0]["signal"])
        price = float(macd["values"][0]["close"])
        upper = float(bb["values"][0]["upper_band"])
        lower = float(bb["values"][0]["lower_band"])
    except (KeyError, IndexError, ValueError):
        return f"{symbol}: Data unavailable"

    signal = "Hold"
    if rsi_value < 30 and macd_value > macd_signal and price < lower:
        signal = "Strong Buy"
    elif rsi_value < 45 and macd_value > macd_signal:
        signal = "Buy"
    elif rsi_value > 70 and macd_value < macd_signal and price > upper:
        signal = "Strong Sell"
    elif rsi_value > 55 and macd_value < macd_signal:
        signal = "Sell"

    return f"{symbol}: {signal} (RSI {rsi_value:.1f}, MACD {macd_value:.2f})"


def market_open():
    """Check if current UK time is during US market hours"""
    now = datetime.now(UK_TZ)
    return MARKET_OPEN_HOUR <= now.hour < MARKET_CLOSE_HOUR


def stock_bot():
    """Main bot loop"""
    print("Starting Stock Signal Bot...")
    while True:
        if market_open():
            for symbol in STOCKS:
                message = get_indicator(symbol)
                print(f"[{datetime.now(UK_TZ).strftime('%H:%M:%S')}] {message}")
                send_telegram(message)
                time.sleep(60)
        else:
            print("Market closed. Sleeping for 30 minutes.")
            time.sleep(1800)


if __name__ == "__main__":
    # Run bot in background
    threading.Thread(target=stock_bot, daemon=True).start()
    # Keep Render alive with Flask server
    app.run(host="0.0.0.0", port=8080)

