"""
Phorager summaries package.

Auto-imports every summary module in this directory so that each module's
registry.register() call fires at import time. This means adding a new
summary type requires only:

  1. Create lib/summaries/my_new_summary.py
  2. Implement BaseSummary and call registry.register(MyNewSummary)

No changes to this file, registry.py, or summarize.py are needed.
"""

import importlib
from pathlib import Path

_SKIP = {"__init__", "base", "registry"}

for _f in sorted(Path(__file__).parent.glob("*.py")):
    if _f.stem not in _SKIP:
        importlib.import_module(f"summaries.{_f.stem}")
