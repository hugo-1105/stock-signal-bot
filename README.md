# 📈 Multi-Stock Signal Bot — Twelve Data + Telegram

An automated **multi-stock trading signal bot** that analyzes top US stocks using multiple technical indicators and sends real-time alerts via **Telegram**.  
Optimized for **Render + Docker deployment**, designed to stay within the **Twelve Data 800 requests/day** free-tier limit.

---

## 🚀 Features

- **Multi-Stock Scanning** — Monitors 4 selected US stocks in rotation.  
- **Real-Time Alerts** — Sends buy/sell/hold signals directly to your Telegram chat.  
- **Smart Indicator Fusion** — Uses a balanced scoring system from 5 proven technical indicators:
  - RSI (Relative Strength Index)
  - SMA (Simple Moving Average)
  - Bollinger Bands
  - MACD (Histogram-based momentum)
  - MFI (Money Flow Index)
- **Market-Aware Scheduler** — Runs only during US market hours (adjusted for UK time zone).  
- **Render-Friendly** — Background process runs continuously via Docker, no Flask or web endpoints required.

---

## 🧠 How It Works

Every cycle, the bot checks each stock sequentially (e.g., NVDA, GOOGL, AAPL, V):

1. Fetches latest data from the **Twelve Data API**.  
2. Computes each indicator.  
3. Applies a scoring system to decide the signal:  
   - `STRONG BUY ❇️❇️`
   - `WEAK BUY ❇️`
   - `HOLD`
   - `WEAK SELL 🈹`
   - `STRONG SELL 🈹🈹`
4. Logs output in Render console and sends Telegram alerts for actionable signals.

---

## 📊 Indicator Logic Summary

| Indicator | Logic | Contribution |
|------------|--------|---------------|
| **RSI** | Detects overbought/oversold conditions | ±1 to ±2 |
| **SMA** | Confirms trend direction vs. price | ±1 |
| **Bollinger Bands** | Evaluates price position in volatility range | ±1 |
| **MACD (Histogram)** | Detects momentum and crossover | ±1 |
| **MFI** | Volume-weighted overbought/oversold check | ±1 |
| **CCI** | Measures momentum deviation from typical price (like RSI but more sensitive). | ±1 |
---

## ⚙️ Environment Setup

### 1️⃣ Required API Keys
You’ll need:
- [Twelve Data API Key](https://twelvedata.com)
- [Telegram Bot Token](https://core.telegram.org/bots)
- Telegram **Chat ID**

---

### 2️⃣ Environment Variables

Create a `.env` file (or configure environment variables in Render):

```env
TWELVEDATA_API_KEY=your_twelve_data_api_key
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```
🕓 Runtime Logic

Runs only during US market hours (14:30–21:00 UK time).

Sleeps 70 seconds between each stock to respect API limits.

Sleeps 9 minutes between full cycles to complete 15-min intervals.

Sleeps 10 minutes when the market is closed.

API Limit Calculation

4 stocks × 7 requests per stock ≈ 28 requests per cycle

Each full 15-min cycle = 28 requests

≈ 96 cycles/day (6.5 hours × 4 cycles/hour)

≈ 728 requests/day ✅ within 800 limit

🧱 Deployment (Render)

Push your code to GitHub.

Create a new Render Web Service → connect your repo.

Choose Python + Docker environment.

Set environment variables (API keys).

Deploy — your bot will start running automatically.

📦 License

MIT License © 2025 — Created by Hugo Pook
You may freely use, modify, and deploy with attribution.

💡 Future Improvements

Add CCI or Stochastic Oscillator for better volatility detection

Store daily performance logs in CSV (for backtesting)

Implement auto-tuning of indicator thresholds

Add Telegram commands to query live status (/status, /last_signal)

📬 Telegram Output Example
📊 NVDA (2025-11-09 18:15:00 UK)
Decision: STRONG BUY ❇️❇️
Score: 4
Price: 132.45
RSI: 28.4
SMA: 129.9
MACD hist: 0.16
MFI: 18.7
BB: (133.2, 130.5, 127.8)

