#!/usr/bin/env python3
"""Verify the artifact hash manifest. Exit != 0 on any mismatch.
Manifest must be regenerated AFTER the last edit of any hashed file."""
import hashlib, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent  # problems/MATH-001
def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()
fail = False
for line in (ROOT / "results" / "r2" / "hashes.txt").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    digest, name = line.split(maxsplit=1)
    name = name.lstrip("*")  # sha256sum binary-mode marker on Windows
    path = ROOT / name
    if not path.is_file():
        print(f"MISSING {name}"); fail = True; continue
    if sha(path) != digest:
        print(f"MISMATCH {name}"); fail = True
    else:
        print(f"OK {name}")
sys.exit(1 if fail else 0)
