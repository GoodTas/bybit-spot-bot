# Bybit Spot Bot — safe starter

This repository starts in **DRY_RUN mode**. It reads public spot candles and prints signals; it does not place orders and does not need API keys.

## Strategy prototype
- Market: BTCUSDT spot
- Candle interval: 15 minutes
- Signal idea: EMA 9 / EMA 21 crossover, with RSI filter
- DRY_RUN is mandatory for this starter. Live order execution is intentionally not implemented.

## Run
Python 3.11+
```bash
python -m pip install -r requirements.txt
python bot.py
```

## Before any live trading
1. Test the signal logic and order sizing independently.
2. Add stop-loss / exit logic, duplicate-order protection, exchange precision/minimum-size checks, logging, and a kill switch.
3. Keep API credentials in a secret manager or environment variables — never commit them.
4. Use a dedicated Bybit API key with only the permissions needed. Withdrawals must remain disabled.
5. Do not assume a 2% account-risk target means each trade can lose only 2%; gaps, slippage, fees, and execution failures can increase losses.

This is a starter scaffold, not a profitable or production-ready trading system.
