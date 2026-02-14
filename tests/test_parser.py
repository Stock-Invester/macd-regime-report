import unittest

from macd_regime.parser import build_rule_from_result


class ParserTests(unittest.TestCase):
    def test_parse_all_tokens(self):
        rule = build_rule_from_result("AAA", "매수 (3달봉), 매도 (1달봉), 오실, 침체, 1달봉 ZQ, 중국")
        self.assertEqual(rule.entry.timeframe, "3M")
        self.assertEqual(rule.exit.timeframe, "1M")
        self.assertEqual(rule.entry.signal, "hist_delta")
        self.assertEqual(rule.exit.signal, "hist_delta")
        self.assertIn("SPX_GATE_ON", rule.exit.gate)
        self.assertIn("zqzmom_delta_positive:1M", rule.entry.confirm)


if __name__ == "__main__":
    unittest.main()
