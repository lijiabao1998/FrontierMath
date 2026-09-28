#!/usr/bin/env python3
"""Compute the actual symmetry group of verified record configurations.

Rather than trusting prose descriptions of Flammenkamp's symmetry classes
(iden/rot2/dia1/ort1/rot4/rct4/dia2/ort2/full), determine each class as a
PROPERTY OF THE OBJECT: for a given verified point set, test every element of the
dihedral group D4 acting on the n x n grid and report which ones preserve the set.
Also report the orbit structure of the full D4 action, and the orbit structure of
the 90-degree rotation alone (which is what the "4-orbit / 1-cell / 2-orbit"
cardinality arguments need).

Usage:  python symmetry_probe.py [--json out.json]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from typing import Sequence

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_all_known import decode as decode_code, check_legal  # noqa: E402


def g_iden(n: int):
    return lambda r, c: (r, c)


def g_rot2(n: int):
    return lambda r, c: (n - 1 - r, n - 1 - c)


def g_rot4(n: int):
    return lambda r, c: (n - 1 - c, r)


def g_rot4i(n: int):
    return lambda r, c: (c, n - 1 - r)


def g_dia1(n: int):
    """reflection in the main diagonal (r == c)"""
    return lambda r, c: (c, r)


def g_dia2(n: int):
    """reflection in the anti-diagonal (r + c == n-1)"""
    return lambda r, c: (n - 1 - c, n - 1 - r)


def g_ort1(n: int):
    """horizontal reflection through the middle row"""
    return lambda r, c: (n - 1 - r, c)


def g_ort2(n: int):
    """vertical reflection through the middle column"""
    return lambda r, c: (r, n - 1 - c)


GENS = {
    "iden": g_iden,
    "rot2": g_rot2,
    "rot4": g_rot4,
    "rot4i": g_rot4i,
    "dia1": g_dia1,
    "dia2": g_dia2,
    "ort1": g_ort1,
    "ort2": g_ort2,
}


def zero_index(pts: Sequence[tuple[int, int]]) -> set[tuple[int, int]]:
    return {(r - 1, c - 1) for c, r in pts}


def preserves(S: set[tuple[int, int]], f, n: int) -> bool:
    return all(f(r, c) in S for (r, c) in S)


def rot4_orbits(n: int) -> dict:
    """Orbit decomposition of the 90-degree rotation T(r,c) = (n-1-c, r)."""
    seen: set[tuple[int, int]] = set()
    sizes: Counter = Counter()
    fixed_center = None
    for r in range(n):
        for c in range(n):
            if (r, c) in seen:
                continue
            orb = []
            cur = (r, c)
            while cur not in seen:
                seen.add(cur)
                orb.append(cur)
                cur = g_rot4(n)(*cur)
            sizes[len(orb)] += 1
            if len(orb) == 1:
                fixed_center = orb[0]
    return {
        "orbit_size_histogram": {str(k): v for k, v in sorted(sizes.items())},
        "n_orbits": sum(sizes.values()),
        "fixed_cell": fixed_center,
    }


def analyse(code: str) -> dict:
    sym, n, pts = decode_code(code)
    S = zero_index(pts)
    legal = check_legal(pts)
    grp = {}
    for name, gen in GENS.items():
        f = gen(n)
        # rot4i is the inverse quarter turn; for the group membership test both matter
        grp[name] = preserves(S, f, n)
    D4_size = 1 + sum(1 for k in ("rot2", "rot4", "rot4i", "dia1", "dia2", "ort1", "ort2") if grp[k])
    return {
        "n": n,
        "symmetry_char": sym,
        "points": len(pts),
        "legal": legal,
        "preserves": grp,
        "D4_elements_preserved": D4_size,
        "rotation_orbits": rot4_orbits(n),
        "all_rows_used": len({p[1] for p in pts}) == n,
        "all_cols_used": len({p[0] for p in pts}) == n,
    }


def main(argv: Sequence[str] | None = None) -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    # the fetched layout puts the corpus under provenance/ (fetch_third_party.py writes there);
    # lit_data/ is the older exploratory layout and is still tried second
    _cands = [os.path.abspath(os.path.join(here, "..", "provenance", "dl", "all_known_solutions")),
              os.path.abspath(os.path.join(here, "..", "lit_data", "dl", "all_known_solutions"))]
    src = next((c for c in _cands if os.path.exists(c)), _cands[0])
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-min", type=int, default=60)
    ap.add_argument("--file", default=src)
    ap.add_argument("--json", default=None)
    args = ap.parse_args(list(argv) if argv is not None else None)

    rows = []
    with open(args.file, "r", encoding="latin-1") as fh:
        for ln in fh:
            ln = ln.rstrip("\n").rstrip("\r")
            if not ln:
                continue
            n = (len(ln) - 1) // 2
            if n >= args.n_min:
                rows.append(ln)
    rows.sort(key=lambda s: ((len(s) - 1) // 2, s[0]))

    out = []
    print(f"{'n':>3} {'sym':>4} {'pts':>4} {'iden':>5} {'rot2':>5} {'rot4':>5} {'dia1':>5} {'dia2':>5} {'ort1':>5} {'ort2':>5}  D4  orbit-histogram")
    for code in rows:
        a = analyse(code)
        out.append(a)
        p = a["preserves"]
        oh = a["rotation_orbits"]["orbit_size_histogram"]
        print(
            f"{a['n']:>3} {a['symmetry_char']:>4} {a['points']:>4} "
            f"{str(p['iden']):>5} {str(p['rot2']):>5} {str(p['rot4']):>5} "
            f"{str(p['dia1']):>5} {str(p['dia2']):>5} {str(p['ort1']):>5} {str(p['ort2']):>5} "
            f"{a['D4_elements_preserved']:>3}  {oh}"
        )
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2, sort_keys=True)
        print(f"[written] {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
