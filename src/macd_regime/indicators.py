from __future__ import annotations

import numpy as np
import pandas as pd


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return pd.DataFrame({"macd": macd_line, "signal": signal_line, "hist": hist})


def timeframe_to_months(tf: str) -> int:
    if not tf.endswith("M"):
        raise ValueError(f"Unsupported timeframe: {tf}")
    return int(tf[:-1])


def resample_to_k_months(ohlc: pd.DataFrame, months: int) -> pd.DataFrame:
    monthly = (
        ohlc.resample("MS")
        .agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"})
        .dropna(subset=["Close"])
    )
    if months == 1:
        return monthly
    grouped = monthly.resample(f"{months}MS", origin="start").agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    )
    return grouped.dropna(subset=["Close"])


def _linreg_last(values: pd.Series) -> float:
    x = np.arange(len(values), dtype=float)
    y = values.values.astype(float)
    if len(values) < 2 or np.isnan(y).any():
        return np.nan
    slope, intercept = np.polyfit(x, y, 1)
    return slope * x[-1] + intercept


def zqzmom(ohlc: pd.DataFrame, length: int = 20) -> pd.Series:
    high = ohlc["High"]
    low = ohlc["Low"]
    close = ohlc["Close"]
    basis = ((high.rolling(length).max() + low.rolling(length).min()) / 2 + close.rolling(length).mean()) / 2
    val = close - basis
    return val.rolling(length).apply(_linreg_last, raw=False)


def latest_hist_delta_positive(close: pd.Series) -> bool:
    m = macd(close)
    d = m["hist"].diff()
    return bool(d.iloc[-1] > 0)


def latest_hist_delta_negative(close: pd.Series) -> bool:
    m = macd(close)
    d = m["hist"].diff()
    return bool(d.iloc[-1] < 0)


def latest_macd_above_signal(close: pd.Series) -> bool:
    m = macd(close)
    return bool(m["macd"].iloc[-1] > m["signal"].iloc[-1])


def latest_macd_below_signal(close: pd.Series) -> bool:
    m = macd(close)
    return bool(m["macd"].iloc[-1] < m["signal"].iloc[-1])


def latest_zq_delta_positive(ohlc: pd.DataFrame) -> bool:
    z = zqzmom(ohlc)
    return bool(z.diff().iloc[-1] > 0)
