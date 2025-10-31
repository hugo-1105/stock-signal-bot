import time
import requests
from datetime import datetime
import pytz
import os

# === CONFIG ===
STOCKS = ["JBL", "GOOGL", "AAPL", "SMCI"]  # top 4 only
TWELVE_API_KEY = os.getenv("TWELVEDATA_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
INTERVAL = "15min"

# Indicator settings
SMA_PERIOD = 20
RSI_PERIOD = 14
EMA_PERIOD = 20
BBANDS_PERIOD = 20
BBANDS_STDDEV = 2


# Market hours (UK)
UK_TZ = pytz.timezone("Europe/London")
MARKET_OPEN = (14, 30)
MARKET_CLOSE = (21, 0)
# ============================


def send_telegram(msg: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": msg}
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"⚠️ Telegram error: {e}")


def td_request(endpoint, params):
    base = "https://api.twelvedata.com"
    params["apikey"] = TWELVE_API_KEY
    try:
        r = requests.get(f"{base}/{endpoint}", params=params, timeout=10)
        j = r.json()
        if "status" in j and j["status"] == "error":
            print(f"⚠️ Error {endpoint}: {j.get('message')}")
            return None
        return j
    except Exception as e:
        print(f"⚠️ Request exception for {endpoint}: {e}")
        return None


# ---------- Indicators ----------

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
        if len(vals) < 2:
            return 0
        return vals[0] - vals[-1]
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


# ---------- Signal Decision ----------

def decide_signal(price, sma, rsi, bb, ema_slope):
    if None in (price, sma, rsi, bb):
        return "INSUFFICIENT_DATA", 0, []

    upper, mid, lower = bb
    score, reasons = 0, []

    # RSI influence
    if rsi < 30: score += 2; reasons.append("RSI oversold +2")
    elif rsi < 40: score += 1; reasons.append("RSI low +1")
    elif rsi > 70: score -= 2; reasons.append("RSI overbought -2")
    elif rsi > 60: score -= 1; reasons.append("RSI high -1")

    # MACD or EMA fallback
    if ema_slope > 0: score += 1; reasons.append("EMA up +1 (fallback)")
    elif ema_slope < 0: score -= 1; reasons.append("EMA down -1 (fallback)")

    # SMA trend
    if price > sma: score += 1; reasons.append("Price above SMA +1")
    else: score -= 1; reasons.append("Price below SMA -1")

    # Bollinger Band position
    if price >= upper: score -= 1; reasons.append("Near upper band -1")
    elif price <= lower: score += 1; reasons.append("Near lower band +1")

    # Final classification
    if score >= 3: signal = "STRONG BUY ❇️❇️"
    elif score == 2: signal = "WEAK BUY ❇️"
    elif score == -2: signal = "WEAK SELL 🈹"
    elif score <= -3: signal = "STRONG SELL 🈹🈹"
    else: signal = "HOLD"

    return signal, score, reasons


# ---------- Market Check ----------

def market_open_now():
    now = datetime.now(UK_TZ)
    if now.weekday() >= 5:
        return False
    h, m = now.hour, now.minute
    if (h, m) < MARKET_OPEN or (h, m) >= MARKET_CLOSE:
        return False
    return True


# ---------- Main ----------

def process_stock(symbol):
    ts = datetime.now(UK_TZ).strftime("%Y-%m-%d %H:%M:%S")

    price = get_price(symbol)
    sma = get_sma(symbol)
    ema_slope = get_ema_slope(symbol)
    rsi = get_rsi(symbol)
    bb = get_bbands(symbol)

    signal, score, reasons = decide_signal(price, sma, rsi, bb, ema_slope)

    print(f"[{ts}] {symbol} — Signal: {signal} ({score}) — {', '.join(reasons)}")

    if signal not in ("HOLD", "INSUFFICIENT_DATA"):
        msg = (
            f"📊 {symbol} ({ts} UK)\n"
            f"Decision: {signal}\nScore: {score}\n"
            f"Price: {price}\nRSI: {rsi}\nSMA: {sma}\n"
            f"EMA slope: {ema_slope:.4f}\nBB: {bb}"
        )
        send_telegram(msg)


def main_loop():
    # Inside main_loop()

    print("🚀 Multi-Stock Signal Bot started — running every 15 min cycle.")

    while True:
        if market_open_now():
            for i, symbol in enumerate(STOCKS):
                print(f"\n=== Checking {symbol} ===")
                process_stock(symbol)
                if i < len(STOCKS) - 1:
                    print("Sleeping 2 minutes before next stock...")
                    time.sleep(2 * 60)  # 2-min gap between each stock
            print("Cycle complete. Waiting 4 minutes before next round.\n")
            time.sleep(7 * 60)  # Remaining part of 15-min total cycle
        else:
            now = datetime.now(UK_TZ).strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{now}] Market closed — sleeping 10 min.")
            time.sleep(600)



if __name__ == "__main__":
    main_loop()












