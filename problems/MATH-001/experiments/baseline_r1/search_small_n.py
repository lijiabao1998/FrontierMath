#!/usr/bin/env python3
"""Deterministic DFS search for 2n-point no-three-in-line configurations.

WLOG reasoning recorded on the certificate: the upper bound D(n) <= 2n follows
from at most 2 points per row; a 2n-point configuration therefore has exactly
2 points in every row and at most 2 per column. The search fixes rows 1..n in
order, picks column pairs {c1 < c2} among columns with occupancy < 2, and
prunes any pair that completes a collinear triple with points already placed
(the only new-triple shape is one new point + two existing points; two new
points + one old lie on the row itself and cannot be collinear with an old
point in another row).

Deterministic: lexicographic column-pair order, no RNG. Stdlib only.

Usage: search_small_n.py N [N ...] --outdir DIR
Writes one certificate JSON per n on success; on UNSAT writes nothing and
prints "UNSAT n=<N>" (expected for n=1 with target 2).
"""
from __future__ import annotations
import datetime as dt
import json
import sys
import time
from pathlib import Path


def collinear(a: tuple[int, int], b: tuple[int, int], c: tuple[int, int]) -> bool:
    return (b[0] - a[0]) * (c[1] - a[1]) == (c[0] - a[0]) * (b[1] - a[1])


def search(n: int) -> tuple[list[tuple[int, int]] | None, float, int]:
    """Return (points | None, wall_seconds, nodes_explored)."""
    t0 = time.perf_counter()
    nodes = 0
    occupied: set[tuple[int, int]] = set()
    col_count = [0] * (n + 1)
    placed: list[tuple[int, int]] = []

    def ok_with_existing(p: tuple[int, int]) -> bool:
        # p + any two already-placed points must not be collinear
        m = len(placed)
        for i in range(m):
            for j in range(i + 1, m):
                if collinear(p, placed[i], placed[j]):
                    return False
        return True

    def dfs(row: int) -> list[tuple[int, int]] | None:
        nonlocal nodes
        if row > n:
            return list(placed)
        for c1 in range(1, n + 1):
            if col_count[c1] >= 2:
                continue
            p1 = (c1, row)
            if not ok_with_existing(p1):
                continue
            occupied.add(p1); col_count[c1] += 1; placed.append(p1)
            for c2 in range(c1 + 1, n + 1):
                if col_count[c2] >= 2:
                    continue
                p2 = (c2, row)
                if not ok_with_existing(p2):
                    continue
                occupied.add(p2); col_count[c2] += 1; placed.append(p2)
                nodes += 1
                got = dfs(row + 1)
                if got is not None:
                    return got
                placed.pop(); occupied.discard(p2); col_count[c2] -= 1
            placed.pop(); occupied.discard(p1); col_count[c1] -= 1
        return None

    got = dfs(1)
    return got, time.perf_counter() - t0, nodes


def main(argv: list[str]) -> int:
    if "--outdir" not in argv or len(argv) < 4:
        print("usage: search_small_n.py N [N ...] --outdir DIR", file=sys.stderr)
        return 2
    cut = argv.index("--outdir")
    sizes = [int(v) for v in argv[1:cut]]
    outdir = Path(argv[cut + 1])
    outdir.mkdir(parents=True, exist_ok=True)
    rc = 0
    for n in sizes:
        pts, secs, nodes = search(n)
        stamp = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        if pts is None:
            print(f"UNSAT n={n} for target 2n ({secs:.2f}s, {nodes} nodes) "
                  f"[expected: n=1 holds only 1 cell; n>=2 should be SAT "
                  f"per literature]")
            rc = max(rc, 1 if n >= 2 else 0)
            continue
        cert = {
            "problem": "MATH-001",
            "n": n,
            "target": 2 * n,
            "points": [list(p) for p in pts],
            "source": "glm-dfs-r1",
            "origin_ref": (
                "self-generated deterministic DFS, experiments/baseline_r1/"
                "search_small_n.py; upper bound 2n via <=2 per row, so a "
                "verified 2n certificate proves D(n)=2n for this n"),
            "generated": stamp,
            "search_stats": {"wall_seconds": round(secs, 3), "nodes": nodes},
            "wlog_note": "exactly 2 points per row; columns capped at 2",
        }
        out = outdir / f"self_n{n:02d}.json"
        out.write_text(json.dumps(cert, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
        print(f"SAT n={n}: 2n={2*n} points in {secs:.2f}s ({nodes} nodes) -> {out}")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
