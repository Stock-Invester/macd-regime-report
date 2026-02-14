from macd_regime.parser import parse_rule_text
from macd_regime.state_store import transition


def test_parser_maps_fields():
    r = parse_rule_text("AAPL", "매수 (3달봉) 오실 1달봉 ZQ / 매도 (1달봉) 금리인하 중국")
    assert r.entry.timeframe == "3M"
    assert r.exit.timeframe == "1M"
    assert r.entry.signal.kind == "macd_hist_delta"
    assert r.exit.signal.direction == "decreasing"
    assert r.entry.confirm[0]["kind"] == "zqzmom_delta_positive"
    assert r.entry.confirm[0]["timeframe"] == "1M"
    assert "SPX_GATE_ON" in r.exit.gate


def test_state_machine_precedence():
    assert transition("IN", entry_pass=True, exit_pass=True) == ("OUT", "SELL")
    assert transition("OUT", entry_pass=False, exit_pass=False) == ("OUT", "WAIT")
    assert transition("OUT", entry_pass=True, exit_pass=False) == ("IN", "BUY")
    assert transition("IN", entry_pass=False, exit_pass=False) == ("IN", "HOLD")
