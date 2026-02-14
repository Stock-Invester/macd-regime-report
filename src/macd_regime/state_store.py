from __future__ import annotations

import json
from pathlib import Path


class StateStore:
    def __init__(self, path: str = "state_store.json") -> None:
        self.path = Path(path)

    def load(self) -> dict[str, str]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, state: dict[str, str]) -> None:
        self.path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def transition(prev_pos: str, entry_pass: bool, exit_pass: bool) -> tuple[str, str]:
    prev = prev_pos if prev_pos in {"IN", "OUT"} else "OUT"

    if exit_pass:
        new_pos = "OUT"
    elif prev == "OUT" and entry_pass:
        new_pos = "IN"
    else:
        new_pos = prev

    action_map = {
        ("OUT", "IN"): "BUY",
        ("IN", "OUT"): "SELL",
        ("IN", "IN"): "HOLD",
        ("OUT", "OUT"): "WAIT",
    }
    return new_pos, action_map[(prev, new_pos)]
