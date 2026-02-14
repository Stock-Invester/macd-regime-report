from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .data_sources import fetch_fred_dfedtaru, fetch_ohlc
from .indicators import (
    latest_hist_delta_negative,
    latest_hist_delta_positive,
    latest_macd_above_signal,
    latest_macd_below_signal,
    latest_zq_delta_positive,
    macd,
    resample_to_k_months,
    timeframe_to_months,
)
from .models import EvalResult, Position, TickerRule


class StateStore:
    def __init__(self, path: str | Path = "state_store.csv"):
        self.path = Path(path)

    def load(self) -> dict[str, Position]:
        if not self.path.exists():
            return {}
        df = pd.read_csv(self.path)
        if df.empty:
            return {}
        return dict(zip(df["Ticker"], df["Position"]))

    def save(self, states: dict[str, Position]) -> None:
        df = pd.DataFrame({"Ticker": list(states.keys()), "Position": list(states.values())})
        df.sort_values("Ticker").to_csv(self.path, index=False)


def compute_spx_gate_on() -> bool:
    spx = fetch_ohlc("^GSPC")
    spx_1m = resample_to_k_months(spx, 1)
    mm = macd(spx_1m["Close"])
    spx_macd_below = bool(mm["macd"].iloc[-1] < mm["signal"].iloc[-1])

    rates = fetch_fred_dfedtaru()
    rate_cut_event = bool((rates.iloc[-1] - rates.iloc[-2]) < 0)
    return spx_macd_below and rate_cut_event


def _eval_signal(ohlc: pd.DataFrame, signal: str, direction: str | None) -> bool:
    close = ohlc["Close"]
    if signal == "hist_delta":
        if direction == "positive":
            return latest_hist_delta_positive(close)
        if direction == "negative":
            return latest_hist_delta_negative(close)
    if signal == "macd_state":
        if direction == "macd_above_signal":
            return latest_macd_above_signal(close)
        if direction == "macd_below_signal":
            return latest_macd_below_signal(close)
    raise ValueError(f"Unsupported signal config: {signal}/{direction}")


def _eval_confirms(rule: TickerRule, raw_ohlc: pd.DataFrame) -> tuple[bool, list[str]]:
    notes: list[str] = []
    for confirm in rule.entry.confirm:
        if confirm.startswith("zqzmom_delta_positive"):
            _, tf = confirm.split(":")
            k = timeframe_to_months(tf)
            tf_ohlc = resample_to_k_months(raw_ohlc, k)
            ok = latest_zq_delta_positive(tf_ohlc)
            notes.append(f"ZQ({tf})={'T' if ok else 'F'}")
            if not ok:
                return False, notes
    return True, notes


def evaluate_rules(rules: list[TickerRule], state_path: str | Path = "state_store.csv") -> pd.DataFrame:
    store = StateStore(state_path)
    prev = store.load()
    spx_gate = compute_spx_gate_on()

    states = dict(prev)
    rows: list[EvalResult] = []
    updated_at = datetime.now(timezone.utc).isoformat()

    for rule in rules:
        raw = fetch_ohlc(rule.ticker)
        entry_k = timeframe_to_months(rule.entry.timeframe)
        exit_k = timeframe_to_months(rule.exit.timeframe)
        entry_ohlc = resample_to_k_months(raw, entry_k)
        exit_ohlc = resample_to_k_months(raw, exit_k)

        entry_pass = _eval_signal(entry_ohlc, rule.entry.signal, rule.entry.direction)
        confirm_pass, note_bits = _eval_confirms(rule, raw)
        entry_pass = entry_pass and confirm_pass

        exit_pass = _eval_signal(exit_ohlc, rule.exit.signal, rule.exit.direction)
        if "SPX_GATE_ON" in rule.exit.gate:
            exit_pass = exit_pass and spx_gate
            note_bits.append(f"SPX_GATE={'T' if spx_gate else 'F'}")

        prev_pos: Position = prev.get(rule.ticker, "IN")
        if exit_pass:
            new_pos: Position = "OUT"
        elif prev_pos == "OUT" and entry_pass:
            new_pos = "IN"
        elif prev_pos == "OUT":
            new_pos = "OUT"
        else:
            new_pos = "IN"

        action_map = {
            ("OUT", "IN"): "BUY",
            ("IN", "OUT"): "SELL",
            ("IN", "IN"): "HOLD",
            ("OUT", "OUT"): "WAIT",
        }
        action = action_map[(prev_pos, new_pos)]
        states[rule.ticker] = new_pos

        rows.append(
            EvalResult(
                ticker=rule.ticker,
                entry_tf=rule.entry.timeframe,
                entry_pass=entry_pass,
                exit_tf=rule.exit.timeframe,
                exit_pass=exit_pass,
                spx_gate=spx_gate,
                prev_pos=prev_pos,
                new_pos=new_pos,
                action=action,  # type: ignore[arg-type]
                notes="; ".join(note_bits),
                updated_at=updated_at,
            )
        )

    store.save(states)
    df = pd.DataFrame([asdict(r) for r in rows])
    return df.rename(
        columns={
            "ticker": "Ticker",
            "entry_tf": "EntryTF",
            "entry_pass": "EntryPass",
            "exit_tf": "ExitTF",
            "exit_pass": "ExitPass",
            "spx_gate": "SPX_Gate",
            "prev_pos": "PrevPos",
            "new_pos": "NewPos",
            "action": "Action",
            "notes": "Notes",
            "updated_at": "UpdatedAt",
        }
    )
