from __future__ import annotations

import argparse
import csv

from .engine import run_engine
from .parser import load_rules_yaml, parse_bulk_rules, write_rules_yaml


def _load_pairs(csv_path: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            out.append((row["Ticker"].strip(), row["Result"].strip()))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="MACD regime report engine")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build-rules", help="Build rules.yaml from input CSV")
    p_build.add_argument("--input-csv", required=True, help="CSV with columns: Ticker,Result")
    p_build.add_argument("--output", default="rules.yaml")

    p_run = sub.add_parser("run", help="Run engine and emit report")
    p_run.add_argument("--rules", default="rules.yaml")
    p_run.add_argument("--state", default="state_store.json")
    p_run.add_argument("--report", default="report.csv")

    args = ap.parse_args()

    if args.cmd == "build-rules":
        pairs = _load_pairs(args.input_csv)
        rules = parse_bulk_rules(pairs)
        write_rules_yaml(rules, args.output)
        print(f"wrote {len(rules)} rules to {args.output}")
    elif args.cmd == "run":
        rules = load_rules_yaml(args.rules)
        run_engine(rules=rules, state_path=args.state, report_csv_path=args.report)


if __name__ == "__main__":
    main()
