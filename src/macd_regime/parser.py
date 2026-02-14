from __future__ import annotations

import re
from pathlib import Path

import yaml

from .models import EntryRule, ExitRule, TickerRule

DEFAULT_ENTRY_SIGNAL = "macd_state"
DEFAULT_EXIT_SIGNAL = "macd_state"
DEFAULT_ENTRY_DIRECTION = "macd_above_signal"
DEFAULT_EXIT_DIRECTION = "macd_below_signal"


def _extract_tf(text: str, keyword: str) -> str:
    m = re.search(rf"{keyword}\s*\((\d+)달봉\)", text)
    if m:
        return f"{int(m.group(1))}M"
    return "1M"


def _extract_zq_tf(text: str, fallback_tf: str) -> str:
    m = re.search(r"(\d+)달봉\s*ZQ", text)
    if m:
        return f"{int(m.group(1))}M"
    return fallback_tf


def build_rule_from_result(ticker: str, result_text: str) -> TickerRule:
    normalized = result_text.replace("중국", "")
    entry_tf = _extract_tf(normalized, "매수")
    exit_tf = _extract_tf(normalized, "매도")

    entry = EntryRule(
        timeframe=entry_tf,
        signal=DEFAULT_ENTRY_SIGNAL,
        direction=DEFAULT_ENTRY_DIRECTION,
        confirm=[],
    )
    exit_rule = ExitRule(
        timeframe=exit_tf,
        signal=DEFAULT_EXIT_SIGNAL,
        direction=DEFAULT_EXIT_DIRECTION,
        gate=[],
    )

    if "오실" in normalized:
        entry.signal = "hist_delta"
        entry.direction = "positive"
        exit_rule.signal = "hist_delta"
        exit_rule.direction = "negative"

    if any(tok in normalized for tok in ["침체", "금리인하", "SPX 기준"]):
        exit_rule.gate.append("SPX_GATE_ON")

    if "ZQ" in normalized:
        zq_tf = _extract_zq_tf(normalized, entry_tf)
        entry.confirm.append(f"zqzmom_delta_positive:{zq_tf}")

    return TickerRule(ticker=ticker, raw_result=result_text, entry=entry, exit=exit_rule)


def build_rules(ticker_results: list[tuple[str, str]]) -> list[TickerRule]:
    return [build_rule_from_result(t, r) for t, r in ticker_results]


def save_rules_yaml(rules: list[TickerRule], out_path: str | Path) -> None:
    path = Path(out_path)
    data = {
        "schema_version": 1,
        "defaults": {
            "entry_signal": {"signal": DEFAULT_ENTRY_SIGNAL, "direction": DEFAULT_ENTRY_DIRECTION},
            "exit_signal": {"signal": DEFAULT_EXIT_SIGNAL, "direction": DEFAULT_EXIT_DIRECTION},
        },
        "rules": [r.to_dict() for r in rules],
    }
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def load_rules_yaml(path: str | Path) -> list[TickerRule]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    out: list[TickerRule] = []
    for row in raw.get("rules", []):
        entry = EntryRule(**row["entry"])
        exit_rule = ExitRule(**row["exit"])
        out.append(
            TickerRule(
                ticker=row["ticker"],
                raw_result=row.get("raw_result", ""),
                entry=entry,
                exit=exit_rule,
            )
        )
    return out
