from __future__ import annotations

from datetime import date

import pandas as pd
import yfinance as yf

FRED_DFEDTARU_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFEDTARU"


def fetch_ohlc(ticker: str, start: str = "2000-01-01", end: str | None = None) -> pd.DataFrame:
    end_date = end or date.today().isoformat()
    df = yf.download(ticker, start=start, end=end_date, interval="1d", auto_adjust=False, progress=False)
    if df.empty:
        raise ValueError(f"No price data for {ticker}")
    return df[["Open", "High", "Low", "Close", "Volume"]].dropna()


def fetch_fred_dfedtaru() -> pd.Series:
    df = pd.read_csv(FRED_DFEDTARU_CSV, parse_dates=["DATE"])
    s = df.set_index("DATE")["DFEDTARU"].dropna()
    return s
