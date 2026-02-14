from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf
from pandas_datareader import data as pdr

from .indicators import macd


def fetch_spx_monthly(period_years: int = 15) -> pd.DataFrame:
    end = datetime.utcnow()
    start = end - timedelta(days=365 * period_years)
    spx = yf.download("^GSPC", start=start, end=end, interval="1d", auto_adjust=False, progress=False)
    if spx.empty:
        raise RuntimeError("No SPX data downloaded")
    if isinstance(spx.columns, pd.MultiIndex):
        spx.columns = spx.columns.get_level_values(0)
    monthly = spx.resample("M").agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    )
    return monthly.dropna(subset=["Close"])


def fetch_fed_target_upper(period_years: int = 15) -> pd.Series:
    end = datetime.utcnow()
    start = end - timedelta(days=365 * period_years)
    series = pdr.DataReader("DFEDTARU", "fred", start, end)["DFEDTARU"]
    m = series.resample("M").last().ffill()
    return m


def compute_spx_gate() -> tuple[bool, dict[str, bool]]:
    spx_m = fetch_spx_monthly()
    rate = fetch_fed_target_upper()
    spx_ind = macd(spx_m["Close"])

    macd_below = bool(spx_ind["macd"].iloc[-1] < spx_ind["signal"].iloc[-1])
    rate_cut_event = bool((rate.diff().iloc[-1]) < 0)
    gate = macd_below and rate_cut_event
    return gate, {"spx_1m_macd_below_signal": macd_below, "rate_cut_event": rate_cut_event}
