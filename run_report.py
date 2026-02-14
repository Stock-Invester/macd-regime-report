from __future__ import annotations

import sys
from pathlib import Path


# Allow running from repository root without `pip install -e .`.
REPO_ROOT = Path(__file__).resolve().parent
SRC_DIR = REPO_ROOT / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from macd_regime.cli import main

if __name__ == "__main__":
    main()
