📈 Multi-Stock Signal Bot (Twelve Data + Telegram)

This Python bot automatically analyzes multiple US stocks using Twelve Data indicators and sends buy/sell alerts via Telegram.
It runs continuously (24/7) but only requests data during US market hours (adjusted for UK time).

🚀 Features

✅ Tracks multiple US stocks (default: JBL, GOOGL, AAPL, SMCI)
✅ Uses Twelve Data API to fetch:

Price

Simple Moving Average (SMA)

Exponential Moving Average (EMA slope)

Relative Strength Index (RSI)

Bollinger Bands

✅ Combines these into a weighted decision model
✅ Sends Buy/Sell/Hold alerts directly to your Telegram chat
✅ Automatically throttles requests to respect free-tier API limits
✅ Prints detailed reasoning for every signal in the console

⚙️ Indicators & Logic
Indicator	Purpose	Effect
RSI	Momentum / overbought-oversold	<30 = +2, >70 = -2
EMA slope	Trend direction (fallback for MACD)	Up = +1, Down = -1
SMA	Trend confirmation	Price > SMA = +1
Bollinger Bands	Volatility extremes	Near lower band = +1, near upper = -1
🧠 Scoring Rules
Total Score	Signal
≥ +3	STRONG BUY ❇️❇️
+2	WEAK BUY ❇️
-2	WEAK SELL 🈹
≤ -3	STRONG SELL 🈹🈹
Otherwise	HOLD
🕒 Schedule

Runs every 15 minutes while market is open (14:30–21:00 UK time).

Sleeps when market is closed (weekends, or outside hours).

Adds 2-minute gaps between each stock to stay under API rate limits.

📩 Telegram Setup

Create a bot via @BotFather
.

Copy your bot token.

Send a message to your bot, then visit

https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates


to find your chat_id.

Store them as environment variables (recommended) or replace directly in the code:

set TELEGRAM_TOKEN=your_bot_token
set TELEGRAM_CHAT_ID=your_chat_id

🔑 Twelve Data Setup

Sign up at https://twelvedata.com

Get your free API key.

Save it as an environment variable:

set TWELVEDATA_API_KEY=your_twelvedata_key

🧩 Environment Variables
Variable	Description
TWELVEDATA_API_KEY	Twelve Data API key
TELEGRAM_TOKEN	Telegram bot token
TELEGRAM_CHAT_ID	Telegram chat ID
▶️ Run Instructions

Install dependencies:

pip install requests pytz


Save your file (e.g., Stock_Signal_Bot.py)

Run in Spyder or terminal:

python Stock_Signal_Bot.py


You should see console output like:

🚀 Multi-Stock Signal Bot started — running every 15 min cycle.
=== Checking GOOGL ===
[2025-10-31 14:45:02] GOOGL — Signal: STRONG BUY (3) — RSI oversold +2, Price above SMA +1
📊 GOOGL (2025-10-31 14:45 UK)
Decision: STRONG BUY ❇️❇️

🧠 Signal Decision Example

Example reasoning output in console:

[2025-10-31 15:00:00] AAPL — Signal: WEAK SELL (-2) — RSI high -1, EMA down -1 (fallback), Price below SMA -1


Telegram notification:

📊 AAPL (2025-10-31 15:00 UK)
Decision: WEAK SELL 🈹
Score: -2
Price: 231.45
RSI: 67.8
SMA: 229.3
EMA slope: -0.0256
BB: (232.1, 228.9, 225.6)

⚠️ Notes

Twelve Data free tier allows 8 requests per minute — this bot stays safely under that.

Runs 24/7, but fetches data only during US trading hours.

Prints warnings if the API or Telegram request fails.

You can add/remove stocks easily by editing:

STOCKS = ["JBL", "GOOGL", "AAPL", "SMCI"]

🧾 License

MIT License — Free for personal and educational use.
