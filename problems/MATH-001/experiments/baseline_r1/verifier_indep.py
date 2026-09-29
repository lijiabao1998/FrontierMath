#!/usr/bin/env python3
"""MATH-001 independent verifier (implementation v2).

Deliberately written from a different algorithmic plan than verifier.py so the
two implementations share no code and fail differently:

  - structural audit: sorted duplicates, row/column occupancy counts (<= 2 each
    is a necessary condition of no-three-in-line)
  - collinearity: for every pair of DISTINCT ROWS, take the 4 point pairs and
    sweep every other row; the exact integer line hits row y at most once, so a
    third point exists iff that cell is occupied (O(n^3) grid sweep, integer
    arithmetic, no floating point)
  - every claimed violation is re-checked with Fraction slopes before reporting

Exit code 0 = PASS, 1 = FAIL, 2 = usage/IO error. Stdlib only.
"""
from __future__ import annotations
import json
import sys
from fractions import Fraction
from itertools import combinations
from pathlib import Path


def verify_indep(cert: dict) -> list[str]:
    errors: list[str] = []
    n = cert.get("n")
    points = cert.get("points")
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        return [f"invalid n: {n!r}"]
    if not isinstance(points, list) or not points:
        return ["missing or empty points"]
    target = cert.get("target", 2 * n)
    pts: list[tuple[int, int]] = []
    for p in points:
        if (isinstance(p, list) and len(p) == 2
                and all(isinstance(v, int) and not isinstance(v, bool) for v in p)
                and 1 <= p[0] <= n and 1 <= p[1] <= n):
            pts.append((p[0], p[1]))
        else:
            errors.append(f"bad or out-of-range point: {p!r}")
    if errors:
        return errors
    if len(set(pts)) != len(pts):
        errors.append("duplicate points present")
    if len(pts) != target:
        errors.append(f"point count {len(pts)} != target {target}")
    occupied = set(pts)

    rows: dict[int, list[int]] = {}
    cols: dict[int, int] = {}
    for x, y in pts:
        rows.setdefault(y, []).append(x)
        cols[x] = cols.get(x, 0) + 1
    for y, xs in rows.items():
        if len(xs) > 2:
            errors.append(f"row {y} holds {len(xs)} points (>2)")
    for x, c in cols.items():
        if c > 2:
            errors.append(f"column {x} holds {c} points (>2)")
    if errors:
        return errors

    by_row = {y: sorted(xs) for y, xs in rows.items()}
    row_ids = sorted(by_row)
    for r1, r2 in combinations(row_ids, 2):
        dy = r2 - r1
        for x1 in by_row[r1]:
            for x2 in by_row[r2]:
                dx = x2 - x1
                for r3 in row_ids:
                    if r3 in (r1, r2):
                        continue
                    step = r3 - r1
                    if (step * dx) % dy:
                        continue
                    x3 = x1 + (step * dx) // dy
                    if 1 <= x3 <= n and (x3, r3) in occupied:
                        a, b, c = (x1, r1), (x2, r2), (x3, r3)
                        # Fraction-slope re-check before flagging (vertical-safe)
                        vert_ab = b[0] == a[0]
                        vert_ac = c[0] == a[0]
                        collinear = (
                            vert_ab and vert_ac
                            or (not vert_ab and not vert_ac
                                and Fraction(c[1] - a[1], c[0] - a[0])
                                == Fraction(b[1] - a[1], b[0] - a[0]))
                        )
                        if collinear:
                            errors.append(
                                f"collinear triple: {a},{b},{c}")
                            if len(errors) >= 5:
                                errors.append("... further violations suppressed")
                                return errors
    return errors


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: verifier_indep.py <cert.json> [cert2.json ...]", file=sys.stderr)
        return 2
    rc = 0
    for arg in argv[1:]:
        path = Path(arg)
        try:
            with path.open(encoding="utf-8") as f:
                cert = json.load(f)
            errors = verify_indep(cert)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"FAIL {path}: unreadable certificate: {exc}", file=sys.stderr)
            rc = 1
            continue
        if errors:
            print(f"FAIL {path.name} (n={cert.get('n')}): {errors[0]}", file=sys.stderr)
            rc = 1
        else:
            print(f"PASS {path.name} (n={cert.get('n')}, "
                  f"{len(cert['points'])} points, v2-indep)")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
