from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class SignalSpec:
    kind: str
    direction: str | None = None


@dataclass
class RuleSide:
    timeframe: str
    signal: SignalSpec
    gate: list[str] = field(default_factory=list)
    confirm: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class TickerRule:
    ticker: str
    raw_text: str
    entry: RuleSide
    exit: RuleSide

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DEFAULT_ENTRY_SIGNAL = SignalSpec(kind="macd_state", direction="macd_above_signal")
DEFAULT_EXIT_SIGNAL = SignalSpec(kind="macd_state", direction="macd_below_signal")
