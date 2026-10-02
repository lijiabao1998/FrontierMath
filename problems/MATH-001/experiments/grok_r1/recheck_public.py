"""Entry point kept so the old command still runs.

It no longer skips n<55. The scan is full_scan.py: both checkers, checkpointed,
fail-closed. A partial checkpoint is not a full reproduction.
"""
from __future__ import annotations
import sys
from pathlib import Path

from full_scan import main as scan_main

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CACHE = HERE / "data_cache" / "all_known_solutions"
CHECKPOINT = ROOT / "problems" / "MATH-001" / "results" / "grok_r1" / "public" / "all_known_full_checkpoint.json"
MANIFEST = ROOT / "problems" / "MATH-001" / "results" / "grok_r1" / "public" / "all_known_full_manifest.json"


def main() -> int:
    if not CACHE.exists():
        print("RED dataset missing", flush=True)
        return 2
    return scan_main([
        "--dataset", str(CACHE),
        "--checkpoint", str(CHECKPOINT),
        "--manifest-out", str(MANIFEST),
        "--git-start", str(ROOT),
    ])


if __name__ == "__main__":
    sys.exit(main())
