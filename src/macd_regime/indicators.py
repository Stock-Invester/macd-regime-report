from __future__ import annotations

import numpy as np
import pandas as pd


def resample_to_k_month(df: pd.DataFrame, k_months: int) -> pd.DataFrame:
    if k_months < 1 or k_months > 12:
        raise ValueError("k_months must be between 1 and 12")
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("df index must be DatetimeIndex")

    m = df.copy().sort_index().resample("M").agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    )
    m = m.dropna(subset=["Close"])
    bucket = ((m.index.year * 12 + m.index.month - 1) // k_months).astype(int)
    out = m.groupby(bucket).agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    )
    out.index = m.groupby(bucket).tail(1).index
    return out


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    sig = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - sig
    return pd.DataFrame({"macd": macd_line, "signal": sig, "hist": hist})


def _rolling_linreg_endpoint(series: pd.Series, window: int) -> pd.Series:
    x = np.arange(window)

    def _endpoint(y: np.ndarray) -> float:
        if np.isnan(y).any():
            return np.nan
        slope, intercept = np.polyfit(x, y, 1)
        return slope * x[-1] + intercept

    return series.rolling(window).apply(lambda y: _endpoint(np.asarray(y)), raw=True)


def zqzmom(df: pd.DataFrame, length: int = 20, mult: float = 1.5) -> pd.Series:
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    highest = high.rolling(length).max()
    lowest = low.rolling(length).min()
    avg_hl = (highest + lowest) / 2
    avg_close = close.rolling(length).mean()
    mean = (avg_hl + avg_close) / 2
    value = close - mean

    tr = pd.concat(
        [(high - low), (high - close.shift()).abs(), (low - close.shift()).abs()],
        axis=1,
    ).max(axis=1)
    _ = tr.rolling(length).mean() * mult

    return _rolling_linreg_endpoint(value, window=length)


def eval_signal(df: pd.DataFrame, kind: str, direction: str | None) -> bool:
    if kind == "macd_state":
        ind = macd(df["Close"])
        last = ind.iloc[-1]
        if direction == "macd_above_signal":
            return bool(last["macd"] > last["signal"])
        if direction == "macd_below_signal":
            return bool(last["macd"] < last["signal"])
    elif kind == "macd_hist_delta":
        ind = macd(df["Close"])
        delta = ind["hist"].diff().iloc[-1]
        if direction == "increasing":
            return bool(delta > 0)
        if direction == "decreasing":
            return bool(delta < 0)
    raise ValueError(f"Unsupported signal {kind}/{direction}")


def eval_confirm(df: pd.DataFrame, kind: str) -> bool:
    if kind == "zqzmom_delta_positive":
        val = zqzmom(df)
        return bool(val.diff().iloc[-1] > 0)
    raise ValueError(f"Unsupported confirm kind: {kind}")
