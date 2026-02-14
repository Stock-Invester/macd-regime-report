from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .engine import evaluate_rules
from .parser import build_rules, load_rules_yaml, save_rules_yaml


def _read_ticker_result_csv(path: str | Path) -> list[tuple[str, str]]:
    df = pd.read_csv(path)
    cols = {c.lower(): c for c in df.columns}
    tcol = cols.get("ticker", "Ticker")
    rcol = cols.get("result", "Result")
    if tcol not in df.columns or rcol not in df.columns:
        raise ValueError("Input CSV must include Ticker and Result columns")
    return list(df[[tcol, rcol]].itertuples(index=False, name=None))


def main() -> None:
    p = argparse.ArgumentParser(description="MACD regime report engine")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build-rules")
    p_build.add_argument("--input", required=True, help="Ticker/Result CSV")
    p_build.add_argument("--out", default="rules.yaml")

    p_run = sub.add_parser("run-report")
    p_run.add_argument("--rules", default="rules.yaml")
    p_run.add_argument("--state", default="state_store.csv")
    p_run.add_argument("--out", default="report.csv")

    args = p.parse_args()

    if args.cmd == "build-rules":
        rows = _read_ticker_result_csv(args.input)
        rules = build_rules(rows)
        save_rules_yaml(rules, args.out)
        print(f"rules saved: {args.out} ({len(rules)} tickers)")
        return

    rules = load_rules_yaml(args.rules)
    report = evaluate_rules(rules, state_path=args.state)
    report.to_csv(args.out, index=False)
    print(report.to_markdown(index=False))
    print(f"report saved: {args.out}")


if __name__ == "__main__":
    main()
