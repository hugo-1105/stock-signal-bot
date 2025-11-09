📈 US Multi-Stock Signal Bot (Twelve Data + Telegram)

This project is an automated stock signal bot that analyzes multiple U.S. stocks using technical indicators from the Twelve Data API
, generates buy/sell/hold signals, and sends live alerts to Telegram.

The bot is designed for 24/7 deployment on Render as a background service (using Docker), running continuously during U.S. market hours.

🧠 Features

✅ Multi-stock support (currently 4 U.S. stocks: V, NVDA, GOOGL, AAPL)

✅ Uses 5 technical indicators:

SMA (Simple Moving Average)

RSI (Relative Strength Index)

MACD (Moving Average Convergence Divergence)

Bollinger Bands

EMA (Exponential Moving Average) as a fallback

✅ Dynamic scoring system (integrates all indicators)

✅ Telegram alerts only when a BUY/SELL signal is detected

✅ Respects Twelve Data’s free-tier limits
(≤ 8 requests/min, ≤ 800 requests/day)

✅ Automatic handling of U.S. market hours (14:30–21:00 UK time)

✅ Docker-based — perfect for Render background services

🧩 Signal Logic Overview
Indicator	Logic	Score Impact
RSI	Oversold (<30) → +2, Overbought (>70) → -2	±2
MACD Line	Above signal → +1, Below → -1	±1
MACD Histogram	Positive → +1, Negative → -1	±1
SMA	Price above SMA → +1, below → -1	±1
Bollinger Bands	Near lower band → +1, upper band → -1	±1
EMA (fallback)	Slope up → +1, slope down → -1	±1
🔹 Signal Classification
Total Score	Decision
≥ +4	STRONG BUY ❇️❇️
+3	WEAK BUY ❇️
-3	WEAK SELL 🈹
≤ -4	STRONG SELL 🈹🈹
Otherwise	HOLD
⚙️ Configuration

Edit or set these environment variables in Render or your .env file:

Variable	Description
TWELVEDATA_API_KEY	Your Twelve Data
 API key
TELEGRAM_TOKEN	Telegram bot token from @BotFather

TELEGRAM_CHAT_ID	Your Telegram user or group chat ID
(Optional)	Modify stock list, intervals, or thresholds in Stock_Auto_Test.py
🐳 Docker Setup
Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "Stock_Auto_Test.py"]

requirements.txt
requests==2.31.0
pandas==2.2.2
numpy==1.26.4
pytz==2024.1
twelvedata==1.2.7

🚀 Deploy on Render

Push your code to GitHub.

Create a new Background Service on Render.com
.

Connect your GitHub repo.

Choose your branch (main) and runtime: Docker.

Add environment variables:

TWELVEDATA_API_KEY

TELEGRAM_TOKEN

TELEGRAM_CHAT_ID

Deploy — Render will automatically build your Docker image.

Once deployed, your bot will:

Run continuously.

Sleep 10 minutes when the market is closed.

Loop through stocks every ~15 minutes during open hours.

🧮 API Usage Calculation

Each stock uses ~5 API requests per cycle (price, SMA, RSI, MACD, BBANDS).

For 4 stocks:

≈ 20 requests per full cycle

Run safely every 15 minutes to stay within:

8 requests/min limit

800 requests/day limit

If you reduce the stock count to 3, you can increase frequency to every 10 minutes safely.

🧠 Example Log Output
🚀 Multi-Stock Signal Bot started — running every 15 min cycle.

=== Checking NVDA ===
[2025-11-09 14:30:15] NVDA — Signal: STRONG BUY (5) — 
RSI oversold +2, MACD bullish +1, Price above SMA +1, Near lower band +1
📊 Telegram alert sent.

🧾 License

This project is open source and available under the MIT License.

💡 Tips

To debug API behavior, test indicators individually using Stock_Auto_Test.py.

Ensure your Render plan supports continuous background tasks (free plans may sleep after inactivity).

You can adjust INTERVAL, scoring weights, or stock list freely.
