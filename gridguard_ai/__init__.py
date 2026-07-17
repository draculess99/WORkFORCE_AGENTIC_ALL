"""GridGuard AI package embedded in the Workforce AI Suite."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

GRIDGUARD_ROOT = Path(__file__).resolve().parent
SUITE_ROOT = GRIDGUARD_ROOT.parent

# Use the suite-level .env so one Railway service can share provider keys.
load_dotenv(SUITE_ROOT / ".env", override=False)

_PATH_DEFAULTS = {
    "GRIDGUARD_KAGGLE_DATA_PATH": GRIDGUARD_ROOT / "data" / "kaggle" / "hourly_energy_consumption.csv",
    "GRIDGUARD_MEMORY_PATH": GRIDGUARD_ROOT / "data" / "runtime" / "decision_memory.json",
    "GRIDGUARD_TOKEN_LEDGER_PATH": GRIDGUARD_ROOT / "data" / "runtime" / "token_usage.json",
    "GRIDGUARD_JSON_PATH": GRIDGUARD_ROOT / "data" / "runtime" / "decisions.json",
    "GRIDGUARD_RAG_DOCS_DIR": GRIDGUARD_ROOT / "docs" / "rag",
}
for _name, _path in _PATH_DEFAULTS.items():
    os.environ.setdefault(_name, str(_path))

__all__ = ["GRIDGUARD_ROOT", "SUITE_ROOT"]
