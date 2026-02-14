from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class SignalSpec:
    kind: str
    direction: str | None = None


@dataclass
class RuleSide:
    timeframe: str
    signal: SignalSpec | str
    gate: list[str] = field(default_factory=list)
    confirm: list[dict[str, Any]] = field(default_factory=list)
    direction: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.signal, str):
            direction = self.direction
            if direction is None:
                direction = "macd_above_signal" if self.signal == "macd_state" else None
            self.signal = SignalSpec(kind=self.signal, direction=direction)
        elif self.direction is not None:
            self.signal.direction = self.direction


@dataclass
class EntryRule(RuleSide):
    pass


@dataclass
class ExitRule(RuleSide):
    pass


@dataclass
class TickerRule:
    ticker: str
    raw_text: str = ""
    entry: RuleSide = field(default_factory=lambda: EntryRule(timeframe="1M", signal=SignalSpec("macd_state", "macd_above_signal")))
    exit: RuleSide = field(default_factory=lambda: ExitRule(timeframe="1M", signal=SignalSpec("macd_state", "macd_below_signal")))
    raw_result: str = ""

    def __post_init__(self) -> None:
        if self.raw_result and not self.raw_text:
            self.raw_text = self.raw_result
        if self.raw_text and not self.raw_result:
            self.raw_result = self.raw_text

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("raw_result", None)
        return payload


DEFAULT_ENTRY_SIGNAL = SignalSpec(kind="macd_state", direction="macd_above_signal")
DEFAULT_EXIT_SIGNAL = SignalSpec(kind="macd_state", direction="macd_below_signal")
