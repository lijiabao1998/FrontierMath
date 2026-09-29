#!/usr/bin/env python3
import hashlib, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent  # problems/MATH-006
fail = False
for line in (ROOT / "results" / "r3" / "hashes.txt").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    digest, name = line.split(maxsplit=1)
    name = name.lstrip("*")
    path = ROOT / name
    if not path.is_file():
        print(f"MISSING {name}"); fail = True; continue
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        print(f"MISMATCH {name}"); fail = True
    else:
        print(f"OK {name}")
sys.exit(1 if fail else 0)
