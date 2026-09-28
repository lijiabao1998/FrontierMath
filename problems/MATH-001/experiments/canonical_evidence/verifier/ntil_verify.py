#!/usr/bin/env python3
"""MATH-001 independent certificate verifier (DeepSeek, dsk/MATH-001-independent-verifier-r1).

Third implementation of the no-three-in-line `2n` certificate checker for
problems/MATH-001. Written from the frozen problem statement; deliberately does
NOT import, call, or copy either of GLM's r1 verifiers.

Mathematical basis: see DERIVATION.md.
  * primary check   -- injectivity of the canonical integer line of every pair
  * secondary check -- exact rational (slope, intercept) grouping, Fraction arithmetic
  * tertiary check  -- naive all-triples integer determinant scan (cross-check only)

Exit codes: 0 = PASS, 1 = FAIL (invalid certificate), 2 = usage/parse error.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from fractions import Fraction
from math import gcd
from typing import Iterable, Sequence

Point = tuple[int, int]

# --------------------------------------------------------------------------- #
# parsing
# --------------------------------------------------------------------------- #


class ParseError(Exception):
    pass


def _is_int(v: object) -> bool:
    # bool is a subclass of int; a certificate must not accept True/False as 1/0.
    return isinstance(v, int) and not isinstance(v, bool)


def parse_points(raw: object) -> list[Point]:
    """Accept the certificate shapes seen in this repo, and nothing sloppy.

    Accepted:
      [[x, y], ...]
      [{"x": .., "y": ..}, ...]      -- either order of the two keys
      {"points": [...]}              -- unwrapped recursively
      {"certificate": [...]} / {"solution": [...]} / {"S": [...]}
    Rejected: floats, strings, bools, nested wrong arity.
    """
    if isinstance(raw, dict):
        for key in ("points", "certificate", "solution", "S", "grid", "cells"):
            if key in raw:
                return parse_points(raw[key])
        raise ParseError(f"dict certificate without a points-like key; got {sorted(raw)[:8]}")

    if not isinstance(raw, list):
        raise ParseError(f"certificate must be a list or a wrapper dict, got {type(raw).__name__}")

    out: list[Point] = []
    for i, item in enumerate(raw):
        if isinstance(item, (list, tuple)):
            if len(item) != 2:
                raise ParseError(f"entry {i}: expected 2 coordinates, got {len(item)}")
            a, b = item
        elif isinstance(item, dict):
            if "x" not in item or "y" not in item:
                raise ParseError(f"entry {i}: object needs keys 'x' and 'y', got {sorted(item)[:8]}")
            a, b = item["x"], item["y"]
        else:
            raise ParseError(f"entry {i}: expected a pair or object, got {type(item).__name__}")
        if not _is_int(a) or not _is_int(b):
            raise ParseError(
                f"entry {i}: coordinates must be int (got {type(a).__name__}/{type(b).__name__}); "
                "floats are rejected because exactness is not recoverable"
            )
        out.append((a, b))
    return out


# --------------------------------------------------------------------------- #
# primary: canonical integer line + injectivity
# --------------------------------------------------------------------------- #


def canonical_line(p: Point, q: Point) -> tuple[int, int, int]:
    """Canonical (A,B,C), gcd-primitive and sign-normalised, for the line pq.

    A*x + B*y + C = 0.  Requires p != q.
    """
    (x1, y1), (x2, y2) = p, q
    a = y2 - y1
    b = x1 - x2
    c = x2 * y1 - x1 * y2
    if a == 0 and b == 0:
        raise ValueError("canonical_line needs two distinct points")
    g = gcd(gcd(abs(a), abs(b)), abs(c))
    if g > 1:
        a //= g
        b //= g
        c //= g
    for v in (a, b, c):
        if v != 0:
            if v < 0:
                a, b, c = -a, -b, -c
            break
    return (a, b, c)


def check_pair_line_injective(pts: Sequence[Point]) -> tuple[bool, tuple[Point, Point, Point] | None]:
    """True iff every unordered pair spans a distinct line.

    Returns (ok, witness) where witness is 3 distinct collinear points if not ok.
    """
    seen: dict[tuple[int, int, int], tuple[Point, Point]] = {}
    m = len(pts)
    for i in range(m):
        pi = pts[i]
        for j in range(i + 1, m):
            pj = pts[j]
            key = canonical_line(pi, pj)
            prev = seen.get(key)
            if prev is not None:
                # prev and (pi,pj) are distinct pairs on the same line.
                # Any 3 distinct points of prev ∪ {pi,pj} are collinear.
                cand = [prev[0], prev[1], pi, pj]
                uniq: list[Point] = []
                for c in cand:
                    if c not in uniq:
                        uniq.append(c)
                assert len(uniq) >= 3
                return False, (uniq[0], uniq[1], uniq[2])
            seen[key] = (pi, pj)
    return True, None


# --------------------------------------------------------------------------- #
# secondary: exact rationals
# --------------------------------------------------------------------------- #


def check_rational_grouping(pts: Sequence[Point]) -> tuple[bool, tuple[Point, Point, Point] | None]:
    """Same criterion via Fraction slope/intercept. Independent arithmetic path."""
    seen: dict[tuple, tuple[Point, Point]] = {}
    m = len(pts)
    for i in range(m):
        (x1, y1) = pts[i]
        for j in range(i + 1, m):
            (x2, y2) = pts[j]
            if x1 == x2:
                key: tuple = ("V", x1)
            else:
                key = (
                    Fraction(y2 - y1, x2 - x1),
                    Fraction(y1 * x2 - y2 * x1, x2 - x1),
                )
            prev = seen.get(key)
            if prev is not None:
                cand = [prev[0], prev[1], pts[i], pts[j]]
                uniq: list[Point] = []
                for c in cand:
                    if c not in uniq:
                        uniq.append(c)
                return False, (uniq[0], uniq[1], uniq[2])
            seen[key] = (pts[i], pts[j])
    return True, None


# --------------------------------------------------------------------------- #
# tertiary: naive all-triples determinant
# --------------------------------------------------------------------------- #


def det3(p: Point, q: Point, r: Point) -> int:
    (x1, y1), (x2, y2), (x3, y3) = p, q, r
    return (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)


def check_triples(pts: Sequence[Point], limit: int | None = None):
    """Naive O(m^3) scan. Only used for small m (self-validation of the fast paths)."""
    m = len(pts)
    if limit is not None and m > limit:
        raise ValueError(f"check_triples refuses m={m} > limit={limit}")
    for i in range(m):
        for j in range(i + 1, m):
            for k in range(j + 1, m):
                if det3(pts[i], pts[j], pts[k]) == 0:
                    return False, (pts[i], pts[j], pts[k])
    return True, None


# --------------------------------------------------------------------------- #
# full verdict
# --------------------------------------------------------------------------- #


def verify(
    pts: Sequence[Point],
    n: int,
    expect_count: int | None = None,
    run_triples_upto: int = 60,
) -> dict:
    """Verify that `pts` certifies D(n) = 2n for the given n.

    Returns a report dict with `ok` and per-check results.
    """
    if expect_count is None:
        expect_count = 2 * n

    report: dict = {
        "n": n,
        "declared_points": len(pts),
        "expect_count": expect_count,
        "checks": {},
        "violations": [],
        "ok": False,
    }
    checks = report["checks"]

    # C1 range, in the card's 1..n indexing. Type-check first: comparisons against
    # n are only meaningful for real numbers, and non-integers terminate the check.
    bad_axes = [p for p in pts if not (_is_int(p[0]) and _is_int(p[1]))]
    out_of_range = [
        p for p in pts
        if _is_int(p[0]) and _is_int(p[1]) and not (1 <= p[0] <= n and 1 <= p[1] <= n)
    ]
    checks["C1_in_range_1_to_n"] = not out_of_range and not bad_axes
    checks["C1_integer_coordinates"] = not bad_axes
    if bad_axes:
        report["violations"].append({"check": "C1", "kind": "non_integer_coordinate", "points": bad_axes[:5]})
    if out_of_range:
        # Diagnose the likely cause: a 0-indexed submission.
        zero_based = all(0 <= p[0] <= n - 1 and 0 <= p[1] <= n - 1 for p in pts)
        report["violations"].append(
            {
                "check": "C1",
                "kind": "out_of_range",
                "count": len(out_of_range),
                "example": out_of_range[:5],
                "looks_zero_indexed": zero_based,
            }
        )

    # The collinearity checks are exact-integer arithmetics and must not be fed
    # non-integers. If any coordinate is not an int, stop here and report; the
    # certificate is already invalid and there is nothing exact left to decide.
    if bad_axes:
        checks["C2_no_duplicate_entries"] = len(list(dict.fromkeys(pts))) == len(pts)
        checks["C3_count_eq_expect"] = len(list(dict.fromkeys(pts))) == expect_count
        checks["C4_no_three_in_line_pairlines"] = None
        checks["C5_no_three_in_line_rationals"] = None
        checks["C5_agrees_with_C4"] = None
        checks["C6_no_three_in_line_naive_triples"] = None
        checks["C6_agrees_with_C4"] = None
        report["distinct_points"] = len(list(dict.fromkeys(pts)))
        report["legal_set"] = None
        report["math_ok"] = False
        report["wellformed"] = False
        report["ok"] = False
        report["short_circuit"] = "non_integer_coordinate"
        return report

    # C2 duplicate *entries* -- a format-hygiene question, NOT a mathematical one.
    # The certificate denotes a set S; |S| is the number of DISTINCT points. A list
    # that repeats an entry denotes the same set and is mathematically the same
    # certificate, so this flag is kept separate from `math_ok` below. What must
    # never happen is counting entries instead of distinct points (trap T5), and
    # that is guarded by C3.
    uniq = list(dict.fromkeys(pts))
    dupes = len(pts) - len(uniq)
    checks["C2_no_duplicate_entries"] = dupes == 0
    if dupes:
        counts: dict[Point, int] = {}
        for p in pts:
            counts[p] = counts.get(p, 0) + 1
        report["violations"].append(
            {
                "check": "C2",
                "kind": "duplicate_entries",
                "entries": len(pts),
                "distinct": len(uniq),
                "duplicated": [list(p) for p, c in counts.items() if c > 1][:5],
            }
        )

    # C3 count of the DISTINCT point set (this is the mathematical count)
    checks["C3_count_eq_expect"] = len(uniq) == expect_count
    if len(uniq) != expect_count:
        report["violations"].append(
            {"check": "C3", "kind": "count_mismatch", "distinct": len(uniq), "expected": expect_count}
        )

    # C4 legality via pair-line injectivity (primary)
    ok_pairs, wit_pairs = check_pair_line_injective(uniq)
    checks["C4_no_three_in_line_pairlines"] = ok_pairs
    if not ok_pairs:
        report["violations"].append(
            {"check": "C4", "kind": "three_collinear", "witness": [list(w) for w in wit_pairs]}
        )

    # C5 legality via rational grouping (secondary). Only meaningful if C4 ran clean
    # or not -- run always, they must agree.
    ok_rat, wit_rat = check_rational_grouping(uniq)
    checks["C5_no_three_in_line_rationals"] = ok_rat
    checks["C5_agrees_with_C4"] = ok_rat == ok_pairs
    if not ok_rat:
        report["violations"].append(
            {"check": "C5", "kind": "three_collinear", "witness": [list(w) for w in wit_rat]}
        )

    # C6 naive triples, small instances only
    if len(uniq) <= run_triples_upto:
        ok_tri, wit_tri = check_triples(uniq)
        checks["C6_no_three_in_line_naive_triples"] = ok_tri
        checks["C6_agrees_with_C4"] = ok_tri == ok_pairs
        if not ok_tri:
            report["violations"].append(
                {"check": "C6", "kind": "three_collinear", "witness": [list(w) for w in wit_tri]}
            )
    else:
        checks["C6_no_three_in_line_naive_triples"] = None
        checks["C6_agrees_with_C4"] = None

    report["distinct_points"] = len(uniq)
    # Legality, ignoring the count question: did we find any collinear triple?
    collinear_found = (not ok_pairs) or (not ok_rat)
    report["legal_set"] = not collinear_found

    # The mathematical verdict: does the point SET witness "D(n) = 2n"?
    #   * set has exactly 2n distinct points  => D(n) >= 2n
    #   * each coordinate an in-range integer => the set lives in the stated grid
    #   * no three collinear                  => the set is legal
    # Together with the row-pigeonhole bound D(n) <= 2n this gives D(n) = 2n for
    # this single n. It says nothing about any other n.
    report["math_ok"] = bool(
        checks["C1_integer_coordinates"]
        and checks["C1_in_range_1_to_n"]
        and checks["C3_count_eq_expect"]
        and not collinear_found
        and checks["C5_agrees_with_C4"]
    )
    # Format hygiene is reported separately so that a well-formedness decision is
    # never confused with the mathematical one.
    report["wellformed"] = bool(checks["C1_integer_coordinates"] and checks["C2_no_duplicate_entries"])
    report["ok"] = report["math_ok"] and report["wellformed"]
    return report


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="MATH-001 independent certificate verifier (DeepSeek r1)")
    ap.add_argument("path", help="certificate JSON file")
    ap.add_argument("--n", type=int, default=None, help="grid size; inferred from --count/2 or file if omitted")
    ap.add_argument("--count", type=int, default=None, help="expected number of points (default 2n)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(list(argv) if argv is not None else None)

    try:
        with open(args.path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"PARSE_ERROR: {exc}", file=sys.stderr)
        return 2

    meta_n = raw.get("n") if isinstance(raw, dict) else None
    n = args.n if args.n is not None else meta_n
    try:
        pts = parse_points(raw)
    except ParseError as exc:
        print(f"PARSE_ERROR: {exc}", file=sys.stderr)
        return 2

    if n is None:
        n = len(pts) // 2
        if not args.quiet:
            print(f"[info] n not given; inferred n={n} from {len(pts)} points", file=sys.stderr)

    report = verify(pts, int(n), expect_count=args.count)
    if not args.quiet:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
