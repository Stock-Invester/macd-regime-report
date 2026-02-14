from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf
from tabulate import tabulate

from .indicators import eval_confirm, eval_signal, resample_to_k_month
from .models import TickerRule
from .spx_gate import compute_spx_gate
from .state_store import StateStore, transition


def _parse_tf(tf: str) -> int:
    return int(tf.replace("M", ""))


def _download_daily_ohlcv(ticker: str, years: int = 20) -> pd.DataFrame:
    end = datetime.now(tz=timezone.utc)
    start = end - timedelta(days=365 * years)
    df = yf.download(ticker, start=start, end=end, interval="1d", auto_adjust=False, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    if df.empty:
        raise RuntimeError(f"No data for {ticker}")
    return df[["Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Close"])


def _eval_side(df_daily: pd.DataFrame, side) -> tuple[bool, str]:
    tf_k = _parse_tf(side.timeframe)
    tf_df = resample_to_k_month(df_daily, tf_k)
    base = eval_signal(tf_df, side.signal.kind, side.signal.direction)

    confirm_notes = []
    for conf in side.confirm:
        conf_tf_k = _parse_tf(conf.get("timeframe", side.timeframe))
        conf_df = resample_to_k_month(df_daily, conf_tf_k)
        c_ok = eval_confirm(conf_df, conf["kind"])
        base = base and c_ok
        confirm_notes.append(f"{conf['kind']}={c_ok}")

    return base, "; ".join(confirm_notes)


def run_engine(
    rules: list[TickerRule],
    state_path: str = "state_store.json",
    report_csv_path: str = "report.csv",
) -> pd.DataFrame:
    state_store = StateStore(state_path)
    state = state_store.load()

    spx_gate, spx_meta = compute_spx_gate()

    rows = []
    for rule in rules:
        daily = _download_daily_ohlcv(rule.ticker)
        entry_pass, entry_note = _eval_side(daily, rule.entry)
        exit_pass, _ = _eval_side(daily, rule.exit)

        if "SPX_GATE_ON" in rule.exit.gate:
            exit_pass = exit_pass and spx_gate

        prev_pos = state.get(rule.ticker, "OUT")
        new_pos, action = transition(prev_pos, entry_pass, exit_pass)
        state[rule.ticker] = new_pos

        notes = "; ".join(filter(None, [entry_note, f"spx={spx_meta}"]))
        rows.append(
            {
                "Ticker": rule.ticker,
                "EntryTF": rule.entry.timeframe,
                "EntryPass": entry_pass,
                "ExitTF": rule.exit.timeframe,
                "ExitPass": exit_pass,
                "SPX_Gate": spx_gate,
                "PrevPos": prev_pos,
                "NewPos": new_pos,
                "Action": action,
                "Notes": notes,
                "UpdatedAt": datetime.now(tz=timezone.utc).isoformat(),
            }
        )

    out = pd.DataFrame(rows)
    out.to_csv(report_csv_path, index=False)
    state_store.save(state)

    print(tabulate(out, headers="keys", tablefmt="github", showindex=False))
    md_path = Path(report_csv_path).with_suffix(".md")
    md_path.write_text(tabulate(out, headers="keys", tablefmt="github", showindex=False), encoding="utf-8")
    return out
