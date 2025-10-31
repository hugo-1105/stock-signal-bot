import time
import requests
import datetime
import pytz
import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials

# === CONFIG ===
STOCKS = ["NVDA", "TSLA", "AAPL", "MSFT"]  # top 4 only
API_KEY = os.getenv("TWELVEDATA_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SHEET_NAME = "Stock_Auto"

# Twelve Data free-tier limits
REQUEST_LIMIT = 8  # requests per minute
WAIT_INTERVAL = 60 / (REQUEST_LIMIT / len(STOCKS))  # pacing

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME)

# === HELPERS ===
def send_telegram(msg: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except Exception as e:
        print(f"[!] Telegram error: {e}")

def fetch_indicator(symbol, indicator, interval="1h", time_period=14):
    url = f"https://api.twelvedata.com/{indicator}?symbol={symbol}&interval={interval}&apikey={TWELVE_API_KEY}"
    if indicator in ["sma", "rsi"]:
        url += f"&time_period={time_period}"
    elif indicator == "bollinger_bands":
        url += f"&time_period={time_period}&stddev=2"
    try:
        r = requests.get(url)
        data = r.json()
        if "values" in data:
            return data["values"][0]
        return None
    except Exception as e:
        print(f"[!] Fetch error for {symbol}-{indicator}: {e}")
        return None

def fetch_price(symbol):
    url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={TWELVE_API_KEY}"
    try:
        r = requests.get(url)
        return float(r.json().get("price"))
    except Exception as e:
        print(f"[!] Price fetch error {symbol}: {e}")
        return None

def log_to_sheet(symbol, message):
    try:
        ws = sheet.worksheet(symbol)
    except gspread.WorksheetNotFound:
        ws = sheet.add_worksheet(title=symbol, rows=1000, cols=5)
    ws.append_row([datetime.datetime.now().isoformat(), message])

# === SIGNAL GENERATION ===
def get_signal(symbol):
    price = fetch_price(symbol)
    if not price:
        return None, None

    sma = fetch_indicator(symbol, "sma")
    rsi = fetch_indicator(symbol, "rsi")
    macd = fetch_indicator(symbol, "macd")
    bb = fetch_indicator(symbol, "bollinger_bands")

    if not all([sma, rsi, macd, bb]):
        return None, None

    sma_val = float(sma["sma"])
    rsi_val = float(rsi["rsi"])
    macd_val = float(macd["macd"])
    macd_signal = float(macd["macd_signal"])
    bb_upper = float(bb["upper_band"])
    bb_lower = float(bb["lower_band"])

    signal = "HOLD"

    # === DECISION LOGIC ===
    if (price > sma_val) and (macd_val > macd_signal) and (rsi_val < 70) and (price < bb_upper):
        signal = "STRONG BUY"
    elif (price > sma_val) and (rsi_val < 60):
        signal = "WEAK BUY"
    elif (price < sma_val) and (macd_val < macd_signal) and (rsi_val > 30) and (price > bb_lower):
        signal = "STRONG SELL"
    elif (price < sma_val) and (rsi_val > 40):
        signal = "WEAK SELL"

    message = f"{symbol}: {signal} @ ${price:.2f} | RSI={rsi_val:.1f} SMA={sma_val:.2f}"
    return signal, message

# === MARKET HOURS ===
def is_market_open():
    uk_time = datetime.datetime.now(pytz.timezone("Europe/London"))
    if uk_time.weekday() >= 5:
        return False
    return 14 <= uk_time.hour < 21  # 14:00–21:00 UK time

# === MAIN LOOP ===
def run_bot():
    print("Stock Signal Bot started (Render Background Service)")
    while True:
        if is_market_open():
            print("Market open — checking signals...")
            actionable_msgs = []
            for symbol in STOCKS:
                signal, message = get_signal(symbol)
                if not signal:
                    continue
                log_to_sheet(symbol, message)
                if "BUY" in signal or "SELL" in signal:
                    actionable_msgs.append(message)
                time.sleep(WAIT_INTERVAL)
            if actionable_msgs:
                send_telegram("📊 Stock Alerts:\n" + "\n".join(actionable_msgs))
        else:
            print("Market closed — sleeping 10 minutes.")
            time.sleep(600)

if __name__ == "__main__":
    run_bot()

