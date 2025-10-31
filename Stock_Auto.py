import time
import requests
import datetime
import pytz
from flask import Flask
import threading
import os

# --- CONFIGURATION ---
# ---------------- CONFIG ---------------- #
API_KEY = os.getenv("TWELVEDATA_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

STOCKS = ["AAPL", "MSFT", "NVDA", "GOOGL"]
INTERVAL = "1min"
SMA_PERIOD = 20
EMA_PERIOD = 10
RSI_PERIOD = 14
BBANDS_PERIOD = 20
BBANDS_STDDEV = 2

LOOP_INTERVAL = 10 * 60  # 10 minutes between each full round
MARKET_OPEN_UK = datetime.time(14, 30)
MARKET_CLOSE_UK = datetime.time(21, 0)

# --- HELPER FUNCTIONS ---
def td_request(endpoint, params):
    base = f"https://api.twelvedata.com/{endpoint}"
    params["apikey"] = API_KEY
    try:
        res = requests.get(base, params=params, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception:
        return {}

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except Exception:
        pass

# --- INDICATORS ---
def get_price(symbol):
    j = td_request("price", {"symbol": symbol})
    try:
        return float(j.get("price"))
    except:
        return None

def get_sma(symbol):
    j = td_request("sma", {"symbol": symbol, "interval": INTERVAL, "time_period": SMA_PERIOD})
    try:
        return float(j["values"][0]["sma"])
    except:
        return None

def get_ema_slope(symbol):
    j = td_request("ema", {"symbol": symbol, "interval": INTERVAL, "time_period": EMA_PERIOD, "outputsize": 30})
    try:
        vals = [float(v["ema"]) for v in j["values"]]
        return vals[0] - vals[-1] if len(vals) >= 2 else 0
    except:
        return 0

def get_rsi(symbol):
    j = td_request("rsi", {"symbol": symbol, "interval": INTERVAL, "time_period": RSI_PERIOD})
    try:
        return float(j["values"][0]["rsi"])
    except:
        return None

def get_bbands(symbol):
    j = td_request("bbands", {
        "symbol": symbol, "interval": INTERVAL,
        "time_period": BBANDS_PERIOD, "stddev": BBANDS_STDDEV
    })
    try:
        v = j["values"][0]
        return float(v["upper_band"]), float(v["middle_band"]), float(v["lower_band"])
    except:
        return None

# --- SIGNAL DECISION ---
def decide_signal(price, sma, rsi, bb, ema_slope):
    if None in (price, sma, rsi, bb):
        return "INSUFFICIENT_DATA", 0, []

    upper, mid, lower = bb
    score, reasons = 0, []

    if rsi < 30: score += 2; reasons.append("RSI oversold +2")
    elif rsi < 40: score += 1; reasons.append("RSI low +1")
    elif rsi > 70: score -= 2; reasons.append("RSI overbought -2")
    elif rsi > 60: score -= 1; reasons.append("RSI high -1")

    if ema_slope > 0: score += 1; reasons.append("EMA up +1")
    elif ema_slope < 0: score -= 1; reasons.append("EMA down -1")

    if price > sma: score += 1; reasons.append("Price above SMA +1")
    else: score -= 1; reasons.append("Price below SMA -1")

    if price >= upper: score -= 1; reasons.append("Near upper band -1")
    elif price <= lower: score += 1; reasons.append("Near lower band +1")

    if score >= 3: signal = "STRONG BUY"
    elif score == 2: signal = "WEAK BUY"
    elif score == -2: signal = "WEAK SELL"
    elif score <= -3: signal = "STRONG SELL"
    else: signal = "HOLD"

    return signal, score, reasons

# --- MARKET HOURS CHECK ---
def is_market_open():
    now = datetime.datetime.now(pytz.timezone("Europe/London")).time()
    return MARKET_OPEN_UK <= now <= MARKET_CLOSE_UK

# --- MAIN LOOP ---
def run_bot():
    while True:
        if not is_market_open():
            print("Market closed. Sleeping for 10 minutes.")
            time.sleep(600)
            continue

        print(f"Market open — checking stocks at {datetime.datetime.now()}")
        for symbol in STOCKS:
            price = get_price(symbol)
            sma = get_sma(symbol)
            rsi = get_rsi(symbol)
            bb = get_bbands(symbol)
            ema_slope = get_ema_slope(symbol)

            signal, score, reasons = decide_signal(price, sma, rsi, bb, ema_slope)

            if signal != "HOLD":
                msg = f"{symbol} — {signal} (Score {score})\nReasons: " + ", ".join(reasons)
                send_telegram(msg)
                print(f"Sent alert: {msg}")
            else:
                print(f"{symbol} HOLD, skipped alert.")

            time.sleep(5)

        print(f"Cycle complete, sleeping {LOOP_INTERVAL/60} min.\n")
        time.sleep(LOOP_INTERVAL)

# --- FLASK KEEP-ALIVE (Render requirement) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Stock Signal Bot is running!"

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)

