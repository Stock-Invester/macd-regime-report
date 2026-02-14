from __future__ import annotations

import re
from pathlib import Path


from .models import (
    DEFAULT_ENTRY_SIGNAL,
    DEFAULT_EXIT_SIGNAL,
    RuleSide,
    SignalSpec,
    TickerRule,
)

_ENTRY_RE = re.compile(r"매수\s*\((\d+)\s*달봉\)")
_EXIT_RE = re.compile(r"매도\s*\((\d+)\s*달봉\)")
_ZQ_TF_RE = re.compile(r"(\d+)\s*달봉\s*ZQ")


def _to_tf(months: int) -> str:
    return f"{months}M"


def parse_rule_text(ticker: str, text: str) -> TickerRule:
    cleaned = text.replace("중국", "")

    entry_m = _ENTRY_RE.search(cleaned)
    exit_m = _EXIT_RE.search(cleaned)
    entry_tf = _to_tf(int(entry_m.group(1))) if entry_m else "1M"
    exit_tf = _to_tf(int(exit_m.group(1))) if exit_m else "1M"

    has_osc = "오실" in cleaned
    has_gate = any(keyword in cleaned for keyword in ["침체", "금리인하", "SPX 기준"])
    has_zq = "ZQ" in cleaned

    entry_signal = DEFAULT_ENTRY_SIGNAL
    exit_signal = DEFAULT_EXIT_SIGNAL
    if has_osc:
        entry_signal = SignalSpec(kind="macd_hist_delta", direction="increasing")
        exit_signal = SignalSpec(kind="macd_hist_delta", direction="decreasing")

    entry_confirm: list[dict] = []
    if has_zq:
        zq_match = _ZQ_TF_RE.search(cleaned)
        zq_tf = _to_tf(int(zq_match.group(1))) if zq_match else entry_tf
        entry_confirm.append({"kind": "zqzmom_delta_positive", "timeframe": zq_tf})

    exit_gate = ["SPX_GATE_ON"] if has_gate else []

    return TickerRule(
        ticker=ticker,
        raw_text=text,
        entry=RuleSide(timeframe=entry_tf, signal=entry_signal, confirm=entry_confirm),
        exit=RuleSide(timeframe=exit_tf, signal=exit_signal, gate=exit_gate),
    )


def parse_bulk_rules(rows: list[tuple[str, str]]) -> list[TickerRule]:
    return [parse_rule_text(ticker=t, text=s) for t, s in rows]


def write_rules_yaml(rules: list[TickerRule], output_path: str | Path) -> None:
    import yaml

    payload = {
        "schema_version": 1,
        "rules": [r.to_dict() for r in rules],
    }
    Path(output_path).write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def load_rules_yaml(path: str | Path) -> list[TickerRule]:
    import yaml

    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    out: list[TickerRule] = []
    for item in raw.get("rules", []):
        out.append(
            TickerRule(
                ticker=item["ticker"],
                raw_text=item.get("raw_text", ""),
                entry=RuleSide(
                    timeframe=item["entry"]["timeframe"],
                    signal=SignalSpec(**item["entry"]["signal"]),
                    gate=item["entry"].get("gate", []),
                    confirm=item["entry"].get("confirm", []),
                ),
                exit=RuleSide(
                    timeframe=item["exit"]["timeframe"],
                    signal=SignalSpec(**item["exit"]["signal"]),
                    gate=item["exit"].get("gate", []),
                    confirm=item["exit"].get("confirm", []),
                ),
            )
        )
    return out
