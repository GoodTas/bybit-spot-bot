import os
import time
from datetime import datetime, timezone

import pandas as pd
from pybit.unified_trading import HTTP

# This prototype intentionally does not submit orders or use private API endpoints.
DRY_RUN = os.getenv("DRY_RUN", "true").strip().lower() == "true"
SYMBOL = os.getenv("SYMBOL", "BTCUSDT").strip().upper()
INTERVAL = os.getenv("INTERVAL", "15").strip()
POLL_SECONDS = 60

if not DRY_RUN:
    raise SystemExit(
        "Safety stop: live execution is not implemented in this starter. "
        "Set DRY_RUN=true."
    )

session = HTTP(testnet=False)


def get_candles() -> pd.DataFrame:
    response = session.get_kline(
        category="spot",
        symbol=SYMBOL,
        interval=INTERVAL,
        limit=100,
    )
    if response.get("retCode") != 0:
        raise RuntimeError(f"Bybit market-data error: {response.get('retMsg')}")

    rows = response["result"]["list"]
    df = pd.DataFrame(
        rows,
        columns=["start", "open", "high", "low", "close", "volume", "turnover"],
    )
    df["start"] = pd.to_numeric(df["start"], errors="coerce")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["start", "close"]).sort_values("start")
    return df.reset_index(drop=True)


def calculate_signal(df: pd.DataFrame) -> tuple[str, float, float]:
    close = df["close"]
    ema_fast = close.ewm(span=9, adjust=False).mean()
    ema_slow = close.ewm(span=21, adjust=False).mean()

    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, float("nan"))
    rsi = 100 - (100 / (1 + rs))

    if len(df) < 30 or pd.isna(rsi.iloc[-1]):
        return "WAIT", float(close.iloc[-1]), float("nan")

    crossed_up = ema_fast.iloc[-2] <= ema_slow.iloc[-2] and ema_fast.iloc[-1] > ema_slow.iloc[-1]
    crossed_down = ema_fast.iloc[-2] >= ema_slow.iloc[-2] and ema_fast.iloc[-1] < ema_slow.iloc[-1]
    latest_rsi = float(rsi.iloc[-1])

    if crossed_up and latest_rsi < 70:
        signal = "BUY_CANDIDATE"
    elif crossed_down:
        signal = "EXIT_CANDIDATE"
    else:
        signal = "WAIT"

    return signal, float(close.iloc[-1]), latest_rsi


def main() -> None:
    print(f"Bybit spot signal prototype | {SYMBOL} | {INTERVAL}m | DRY_RUN={DRY_RUN}")
    while True:
        try:
            candles = get_candles()
            # Ignore the currently forming candle when evaluating a signal.
            if len(candles) > 2:
                candles = candles.iloc[:-1].reset_index(drop=True)
            signal, price, rsi = calculate_signal(candles)
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            rsi_text = f"{rsi:.2f}" if pd.notna(rsi) else "n/a"
            print(f"{now} UTC | {SYMBOL} | price={price:.6g} | RSI={rsi_text} | {signal}")
        except Exception as exc:
            print(f"Market-data check failed: {type(exc).__name__}: {exc}")
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
