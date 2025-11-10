import time
import requests
from datetime import datetime
import pytz
import os

# === CONFIG ===
STOCKS = ["V", "NVDA", "GOOGL", "AAPL"]  # top 4 only
TWELVE_API_KEY = os.getenv("TWELVEDATA_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
INTERVAL = "15min"

# Indicator settings
SMA_PERIOD = 20
RSI_PERIOD = 14
BBANDS_PERIOD = 20
BBANDS_STDDEV = 2
ADX_PERIOD = 14
MFI_PERIOD = 14
ADX_THRESHOLD = 25  # typical value for strong trend


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


def get_macd(symbol):
    j = td_request("macd", {
        "symbol": symbol, "interval": INTERVAL,
        "short_period": 12, "long_period": 26, "signal_period": 9
    })
    try:
        v = j["values"][0]
        return float(v["macd"]), float(v["macd_signal"]), float(v["macd_hist"])
    except:
        return None, None, None


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


def get_adx(symbol):
    j = td_request("adx", {
        "symbol": symbol,
        "interval": INTERVAL,
        "time_period": ADX_PERIOD
    })
    try:
        v = j["values"][0]
        adx = float(v["adx"])
        plus_di = float(v["+di"])
        minus_di = float(v["-di"])
        return adx, plus_di, minus_di
    except:
        return None, None, None


def get_mfi(symbol):
    j = td_request("mfi", {"symbol": symbol, "interval": INTERVAL, "time_period": MFI_PERIOD})
    try:
        return float(j["values"][0]["mfi"])
    except:
        return None


# ---------- Signal Decision ----------

def decide_signal(price, sma, rsi, bb, macd, macd_sig, macd_hist, adx, plus_di, minus_di, mfi):
    # --- safer unpacking of Bollinger Bands ---
    if bb is None or len(bb) != 3:
        upper = mid = lower = None
    else:
        upper, mid, lower = bb

    # --- validate data availability (explicit per indicator) ---
    missing = []
    if price is None: missing.append("price")
    if sma is None: missing.append("sma")
    if rsi is None: missing.append("rsi")
    if upper is None or mid is None or lower is None: missing.append("bbands")
    if macd is None or macd_sig is None or macd_hist is None: missing.append("macd")
    if adx is None or plus_di is None or minus_di is None: missing.append("adx")
    if mfi is None: missing.append("mfi")

    if missing:
        print(f"⚠️ Missing data for: {', '.join(missing)}")
        return "INSUFFICIENT_DATA", 0, [f"Missing: {', '.join(missing)}"]

    # --- scoring begins ---
    score, reasons = 0, []

    # RSI
    if rsi < 30: score += 2; reasons.append("RSI oversold +2")
    elif rsi < 40: score += 1; reasons.append("RSI low +1")
    elif rsi > 70: score -= 2; reasons.append("RSI overbought -2")
    elif rsi > 60: score -= 1; reasons.append("RSI high -1")

    # MACD
    if macd_hist > 0: score += 1; reasons.append("MACD bullish +1")
    elif macd_hist < 0: score -= 1; reasons.append("MACD bearish -1")

    # SMA trend
    if price > sma: score += 1; reasons.append("Price above SMA +1")
    else: score -= 1; reasons.append("Price below SMA -1")

    # Bollinger Bands
    if price >= upper: score -= 1; reasons.append("Near upper band -1")
    elif price <= lower: score += 1; reasons.append("Near lower band +1")

    # ADX logic
    if adx > ADX_THRESHOLD:
        if plus_di > minus_di:
            score += 1
            reasons.append("ADX strong bullish trend +1")
        elif minus_di > plus_di:
            score -= 1
            reasons.append("ADX strong bearish trend -1")
    else:
        reasons.append("ADX trend weak (no score)")

    # MFI
    if mfi < 20: score += 1; reasons.append("MFI oversold +1")
    elif mfi > 80: score -= 1; reasons.append("MFI overbought -1")

    # Final classification
    if score >= 4: signal = "STRONG BUY ❇️❇️"
    elif score == 3: signal = "WEAK BUY ❇️"
    elif score == -3: signal = "WEAK SELL 🈹"
    elif score <= -4: signal = "STRONG SELL 🈹🈹"
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
    macd, macd_sig, macd_hist = get_macd(symbol)
    rsi = get_rsi(symbol)
    bb = get_bbands(symbol)
    adx, plus_di, minus_di = get_adx(symbol)
    mfi = get_mfi(symbol)

    signal, score, reasons = decide_signal(price, sma, rsi, bb, macd, macd_sig, macd_hist, adx, plus_di, minus_di, mfi)

    print(f"[{ts}] {symbol} — Signal: {signal} ({score}) — {', '.join(reasons)}")

    if signal not in ("HOLD", "INSUFFICIENT_DATA"):
        msg = (
            f"📊 {symbol} ({ts} UK)\n"
            f"Decision: {signal}\nScore: {score}\n"
            f"Price: {price}\nRSI: {rsi}\nSMA: {sma}\n"
            f"MACD hist: {macd_hist}\nADX: {adx}\nMFI: {mfi}\nBB: {bb}"
        )
        send_telegram(msg)


def main_loop():
    print("🚀 Multi-Stock Signal Bot — ADX+MFI Enhanced Mode")

    while True:
        if market_open_now():
            for i, symbol in enumerate(STOCKS):
                print(f"\n=== Checking {symbol} ===")
                process_stock(symbol)
                if i < len(STOCKS) - 1:
                    print("Sleeping 70s before next stock to respect API limits...")
                    time.sleep(70)
            print("Cycle complete. Waiting 9 minutes before next round.\n")
            time.sleep(540)
        else:
            now = datetime.now(UK_TZ).strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{now}] Market closed — sleeping 10 min.")
            time.sleep(600)


if __name__ == "__main__":
    main_loop()





