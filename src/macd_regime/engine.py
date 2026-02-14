from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from .models import TickerRule
from .state_store import StateStore, transition

if TYPE_CHECKING:
    import pandas as pd


def _pd():
    import pandas as pd

    return pd


def _parse_tf(tf: str) -> int:
    return int(tf.replace("M", ""))


def fetch_ohlc(ticker: str, years: int = 20):
    pd = _pd()
    import yfinance as yf

    end = datetime.now(tz=timezone.utc)
    start = end - timedelta(days=365 * years)
    df = yf.download(ticker, start=start, end=end, interval="1d", auto_adjust=False, progress=False)
    multi_index_cls = getattr(pd, "MultiIndex", tuple)
    if isinstance(df.columns, multi_index_cls):
        df.columns = df.columns.get_level_values(0)
    if df.empty:
        raise RuntimeError(f"No data for {ticker}")
    return df[["Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Close"])


def _eval_signal(df, signal_kind: str, direction: str | None) -> bool:
    from .indicators import eval_signal

    return eval_signal(df, signal_kind, direction)


def compute_spx_gate_on() -> bool:
    try:
        from .spx_gate import compute_spx_gate

        gate, _meta = compute_spx_gate()
        return gate
    except Exception:
        return False


def _eval_side(df_daily, side) -> tuple[bool, str]:
    tf_k = _parse_tf(side.timeframe)
    if tf_k == 1:
        tf_df = df_daily
    else:
        from .indicators import resample_to_k_month

        tf_df = resample_to_k_month(df_daily, tf_k)
    base = _eval_signal(tf_df, side.signal.kind, side.signal.direction)

    confirm_notes = []
    for conf in side.confirm:
        conf_tf_k = _parse_tf(conf.get("timeframe", side.timeframe))
        if conf_tf_k == 1:
            conf_df = df_daily
        else:
            from .indicators import resample_to_k_month

            conf_df = resample_to_k_month(df_daily, conf_tf_k)
        from .indicators import eval_confirm

        c_ok = eval_confirm(conf_df, conf["kind"])
        base = base and c_ok
        confirm_notes.append(f"{conf['kind']}={c_ok}")

    return base, "; ".join(confirm_notes)


def evaluate_rules(rules: list[TickerRule], state_path: str | Path = "state_store.json"):
    pd = _pd()
    state_store = StateStore(str(state_path))
    state = state_store.load()

    spx_gate = compute_spx_gate_on()
    spx_meta = str(spx_gate)

    rows = []
    for rule in rules:
        prev_pos = state.get(rule.ticker, "OUT")
        try:
            daily = fetch_ohlc(rule.ticker)
            entry_pass, entry_note = _eval_side(daily, rule.entry)
            exit_pass, _ = _eval_side(daily, rule.exit)

            if "SPX_GATE_ON" in rule.exit.gate:
                exit_pass = exit_pass and spx_gate

            new_pos, action = transition(prev_pos, entry_pass, exit_pass)
            state[rule.ticker] = new_pos
            notes = "; ".join(filter(None, [entry_note, f"spx={spx_meta}"]))
        except Exception as exc:
            entry_pass = False
            exit_pass = False
            new_pos, action = transition(prev_pos, entry_pass, exit_pass)
            state[rule.ticker] = new_pos
            notes = f"error={type(exc).__name__}: {exc}; spx={spx_meta}"

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
    state_store.save(state)
    return out


def _render_table(out) -> str:
    try:
        from tabulate import tabulate

        return tabulate(out, headers="keys", tablefmt="github", showindex=False)
    except Exception:
        rows = getattr(out, "_rows", None)
        if isinstance(rows, list) and rows:
            headers = list(rows[0].keys())
            lines = [" | ".join(headers)]
            lines.append(" | ".join(["---"] * len(headers)))
            for row in rows:
                lines.append(" | ".join(str(row.get(h, "")) for h in headers))
            return "\n".join(lines)
        return str(out)


def run_engine(
    rules: list[TickerRule],
    state_path: str = "state_store.json",
    report_csv_path: str = "report.csv",
):
    out = evaluate_rules(rules=rules, state_path=state_path)
    out.to_csv(report_csv_path, index=False)

    table = _render_table(out)
    print(table)
    md_path = Path(report_csv_path).with_suffix(".md")
    md_path.write_text(table, encoding="utf-8")
    return out
