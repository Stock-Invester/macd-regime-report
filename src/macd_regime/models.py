from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal

Position = Literal["IN", "OUT"]
Action = Literal["BUY", "SELL", "HOLD", "WAIT"]


@dataclass
class SignalRule:
    timeframe: str
    signal: str
    direction: str | None = None


@dataclass
class EntryRule(SignalRule):
    confirm: list[str] = field(default_factory=list)


@dataclass
class ExitRule(SignalRule):
    gate: list[str] = field(default_factory=list)


@dataclass
class TickerRule:
    ticker: str
    raw_result: str
    entry: EntryRule
    exit: ExitRule

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class EvalResult:
    ticker: str
    entry_tf: str
    entry_pass: bool
    exit_tf: str
    exit_pass: bool
    spx_gate: bool
    prev_pos: Position
    new_pos: Position
    action: Action
    notes: str
    updated_at: str
