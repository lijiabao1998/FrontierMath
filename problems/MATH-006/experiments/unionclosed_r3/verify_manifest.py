#!/usr/bin/env python3
"""Verify problems/MATH-006/results/r3/hashes.txt.

paths in the manifest are relative to problems/MATH-006 (= three parents up
from this file). Exit != 0 on any mismatch or missing file."""
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent           # experiments/unionclosed_r3
ROOT = HERE.parent.parent                        # problems/MATH-006
MANIFEST = ROOT / "results" / "r3" / "hashes.txt"

fail = False
for line in MANIFEST.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    digest, name = line.split(maxsplit=1)
    name = name.lstrip("*")
    path = ROOT / name
    if not path.is_file():
        print(f"MISSING {name}")
        fail = True
        continue
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != digest:
        print(f"MISMATCH {name}")
        fail = True
    else:
        print(f"OK {name}")
sys.exit(1 if fail else 0)
