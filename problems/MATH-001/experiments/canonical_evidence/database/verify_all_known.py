#!/usr/bin/env python3
"""Full independent verification of Flammenkamp's complete known-solution database.

Source (primary, fetched fresh by this round):
    https://wwwhomes.uni-bielefeld.de/achim/no3in/download/all_known_solutions
    "all (to me) known no-three-in-line problem solutions aka. valid configurations"
    431,008 lines, last modified 2026-08-31.

This is the file the r1 round reported as unobtainable. It covers n = 2..76
(and notably contains ZERO configurations for n = 75).

Encoding: derived from the page  https://wwwhomes.uni-bielefeld.de/achim/no3in/encoding
    alphabet = "0-9 A-Z a-z" + "#$%&@?!()[]<>{}=*+|-/~^_:;,."   (indices 0..89, so n <= 90)
The r1 round's 36,912-line file `data_1997/known_solutions` only needed indices
<= 61 ('z'); this file needs the full alphabet because it contains n up to 76.

Every mapping used here is validated by two independent invariants:
    structural: max column index of a line must equal n-1   (decode.c enforces this)
    geometric:  the decoded set must have no three collinear points
A wrong character mapping breaks one or both, so the mapping cannot silently pass.

Usage:
    python verify_all_known.py --file <path> [--sample N] [--json out.json] [--progress 50000]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter, defaultdict
from math import gcd
from typing import Sequence

ALPHABET = (
    "0123456789"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "#$%&@?!()[]<>{}=*+|-/~^_:;,."
)
CHAR_TO_COL = {ch: i for i, ch in enumerate(ALPHABET)}

# The historical mapping shipped in decode.c, valid only for n <= 62.
def legacy_col(ch: str) -> int:
    o = ord(ch)
    if 0x30 <= o <= 0x39:
        return o - 0x30
    if 0x41 <= o <= 0x5A:
        return o - 0x41 + 10
    if 0x61 <= o <= 0x7A:
        return o - 0x61 + 36
    return o + 1


def check_legal(pts: list[tuple[int, int]]) -> bool:
    """No three of `pts` collinear, via canonical-line injectivity.

    Inlined for throughput; mathematically the same criterion as
    ntil_verify.check_pair_line_injective.
    """
    seen = set()
    m = len(pts)
    add = seen.add
    for i in range(m):
        x1, y1 = pts[i]
        for j in range(i + 1, m):
            x2, y2 = pts[j]
            a = y2 - y1
            b = x1 - x2
            c = x2 * y1 - x1 * y2
            g = gcd(gcd(a if a >= 0 else -a, b if b >= 0 else -b), c if c >= 0 else -c)
            if g > 1:
                a //= g
                b //= g
                c //= g
            if a < 0 or (a == 0 and b < 0):
                a = -a
                b = -b
                c = -c
            k = (a, b, c)
            if k in seen:
                return False
            add(k)
    return True


def decode(line: str) -> tuple[str, int, list[tuple[int, int]]] | None:
    sym = line[0]
    data = line[1:]
    if not data or len(data) % 2:
        return None
    n = len(data) // 2
    if n < 2:
        return None
    try:
        cols = [CHAR_TO_COL[c] for c in data]
    except KeyError as exc:
        raise ValueError(f"char {exc.args[0]!r} not in alphabet") from None
    if max(cols) != n - 1:
        raise ValueError(f"max col {max(cols)} != n-1 = {n - 1}")
    pts = []
    for j in range(n):
        c1, c2 = cols[2 * j], cols[2 * j + 1]
        if c1 == c2:
            raise ValueError(f"degenerate row pair at row {j + 1}")
        pts.append((c1 + 1, j + 1))
        pts.append((c2 + 1, j + 1))
    return sym, n, pts


def main(argv: Sequence[str] | None = None) -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.abspath(os.path.join(here, "..", "lit_data", "dl", "all_known_solutions"))
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=default)
    ap.add_argument("--sample", type=int, default=0, help="verify only a random sample of this size (0 = all)")
    ap.add_argument("--seed", type=int, default=20260928)
    ap.add_argument("--json", default=None)
    ap.add_argument("--progress", type=int, default=50000)
    args = ap.parse_args(list(argv) if argv is not None else None)

    t0 = time.time()
    with open(args.file, "r", encoding="latin-1") as fh:
        lines = [ln.rstrip("\n").rstrip("\r") for ln in fh if ln.strip()]
    read_s = round(time.time() - t0, 2)
    print(f"[read] {len(lines)} lines from {args.file} in {read_s}s", flush=True)

    if args.sample:
        import random

        lines = random.Random(args.seed).sample(lines, min(args.sample, len(lines)))
        print(f"[sample] verifying a random subset of {len(lines)}", flush=True)

    per_n: Counter = Counter()
    pass_n: Counter = Counter()
    sym_per_n: dict[int, Counter] = defaultdict(Counter)
    decode_errors: list[dict] = []
    verify_failures: list[dict] = []
    max_col_seen: dict[int, int] = {}
    legacy_mismatch = 0

    t0 = time.time()
    for idx, line in enumerate(lines, 1):
        try:
            dec = decode(line)
        except ValueError as exc:
            decode_errors.append({"idx": idx, "line": line[:80], "error": str(exc)})
            continue
        if dec is None:
            continue
        sym, n, pts = dec
        per_n[n] += 1
        sym_per_n[n][sym] += 1
        max_col_seen[n] = max(max_col_seen.get(n, 0), len(line) - 1)
        if n <= 62:
            # for n <= 62 the extended and legacy alphabets must agree exactly
            dat = line[1:]
            if any(legacy_col(c) != CHAR_TO_COL[c] for c in dat):
                legacy_mismatch += 1
        if check_legal(pts):
            pass_n[n] += 1
        elif len(verify_failures) < 20:
            verify_failures.append({"idx": idx, "n": n, "sym": sym, "line": line[:80]})
        if args.progress and idx % args.progress == 0:
            el = time.time() - t0
            print(f"  [{idx}/{len(lines)}] {el:.1f}s  {idx / el:.0f} lines/s", flush=True)

    elapsed = round(time.time() - t0, 2)
    total = sum(per_n.values())
    passed = sum(pass_n.values())
    out = {
        "file": os.path.basename(args.file),
        "lines_read": len(lines),
        "decoded": total,
        "verify_pass": passed,
        "verify_fail": total - passed,
        "n_min": min(per_n) if per_n else None,
        "n_max": max(per_n) if per_n else None,
        "n_present": sorted(per_n),
        "per_n_counts": {str(k): per_n[k] for k in sorted(per_n)},
        "n75_present": 75 in per_n,
        "n75_count": per_n.get(75, 0),
        "n_ge_60": {str(k): per_n[k] for k in sorted(per_n) if k >= 60},
        "decode_errors": decode_errors[:20],
        "n_decode_errors": len(decode_errors),
        "verify_failures": verify_failures,
        "legacy_alphabet_mismatches_for_n_le_62": legacy_mismatch,
        "seconds": elapsed,
        "read_seconds": read_s,
    }
    print(json.dumps({k: v for k, v in out.items() if k not in ("per_n_counts",)}, indent=2, sort_keys=True))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2, sort_keys=True)
        print(f"[written] {args.json}")
    return 0 if (total == passed and not decode_errors) else 1


if __name__ == "__main__":
    sys.exit(main())
