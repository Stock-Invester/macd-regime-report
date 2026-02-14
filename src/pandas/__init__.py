from __future__ import annotations

import csv
from datetime import datetime, timedelta
from typing import Any


class Series:
    def __init__(self, data, index=None, dtype=None):
        self.data = [float(x) if dtype in (float, "float") else x for x in data]
        self.index = index

    def __add__(self, other):
        return Series([x + other for x in self.data], index=self.index)


class _ILoc:
    def __init__(self, df):
        self.df = df

    def __getitem__(self, idx: int):
        return self.df._rows[idx]


class DataFrame:
    def __init__(self, data, index=None):
        self.index = index
        self._rows = []
        self.columns = []

        if isinstance(data, list):
            self._rows = [dict(r) for r in data]
            self.columns = list(self._rows[0].keys()) if self._rows else []
        elif isinstance(data, dict):
            self.columns = list(data.keys())
            row_count = 0
            for v in data.values():
                if isinstance(v, Series):
                    row_count = max(row_count, len(v.data))
                elif isinstance(v, list):
                    row_count = max(row_count, len(v))
                else:
                    row_count = max(row_count, 1)
            for i in range(row_count):
                row = {}
                for col, v in data.items():
                    if isinstance(v, Series):
                        row[col] = v.data[i]
                    elif isinstance(v, list):
                        row[col] = v[i]
                    else:
                        row[col] = v
                self._rows.append(row)

    @property
    def iloc(self):
        return _ILoc(self)

    def to_csv(self, path, index=False):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=self.columns)
            w.writeheader()
            for row in self._rows:
                w.writerow(row)


class MultiIndex:
    def get_level_values(self, _level):
        return []


def date_range(start: str, periods: int, freq: str = "D"):
    dt = datetime.fromisoformat(start)
    step = timedelta(days=1 if freq == "D" else 30)
    return [dt + i * step for i in range(periods)]


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return DataFrame(rows)
