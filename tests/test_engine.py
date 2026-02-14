import tempfile
import unittest
from pathlib import Path

import pandas as pd

from macd_regime import engine
from macd_regime.models import EntryRule, ExitRule, TickerRule


class EngineStateTests(unittest.TestCase):
    def _ohlc(self):
        idx = pd.date_range("2022-01-01", periods=900, freq="D")
        base = pd.Series(range(900), index=idx, dtype=float)
        return pd.DataFrame(
            {
                "Open": base + 100,
                "High": base + 101,
                "Low": base + 99,
                "Close": base + 100,
                "Volume": 1000,
            },
            index=idx,
        )

    def test_out_state_sticks_until_entry(self):
        rule = TickerRule(
            ticker="AAA",
            raw_result="",
            entry=EntryRule(timeframe="1M", signal="macd_state", direction="macd_above_signal"),
            exit=ExitRule(timeframe="1M", signal="macd_state", direction="macd_below_signal", gate=[]),
        )

        orig_fetch = engine.fetch_ohlc
        orig_spx = engine.compute_spx_gate_on
        orig_eval_signal = engine._eval_signal
        try:
            engine.fetch_ohlc = lambda t: self._ohlc()  # type: ignore[assignment]
            engine.compute_spx_gate_on = lambda: False  # type: ignore[assignment]

            calls = iter([False, False])
            engine._eval_signal = lambda *_args, **_kwargs: next(calls)  # type: ignore[assignment]

            with tempfile.TemporaryDirectory() as td:
                state = Path(td) / "state.csv"
                pd.DataFrame([{"Ticker": "AAA", "Position": "OUT"}]).to_csv(state, index=False)
                out = engine.evaluate_rules([rule], state_path=state)
                self.assertEqual(out.iloc[0]["NewPos"], "OUT")
                self.assertEqual(out.iloc[0]["Action"], "WAIT")
        finally:
            engine.fetch_ohlc = orig_fetch  # type: ignore[assignment]
            engine.compute_spx_gate_on = orig_spx  # type: ignore[assignment]
            engine._eval_signal = orig_eval_signal  # type: ignore[assignment]


if __name__ == "__main__":
    unittest.main()
