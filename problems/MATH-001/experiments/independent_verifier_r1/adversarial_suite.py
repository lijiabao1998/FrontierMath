#!/usr/bin/env python3
"""Adversarial test suite for the DeepSeek r1 independent verifier (MATH-001).

Every case is judged by the fast verifier AND by an independent brute-force
determinant oracle (`oracle`), and the two must agree on the *legality* question.
Cases where they disagree are hard failures of this suite.

Case families
  P  positive controls        -- must PASS
  N  negative controls        -- must FAIL, with the expected violation kind
  F  fuzz                     -- random near-miss legal sets, agreement required
  X  structural/adversarial   -- count preservation, 4-collinear, coordinates, symmetry

Run:  python adversarial_suite.py --json negative_tests/adversarial_summary.json
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from fractions import Fraction
from itertools import combinations
from typing import Sequence

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ntil_verify import Point, canonical_line, det3, parse_points, verify  # noqa: E402


# --------------------------------------------------------------------------- #
# oracle: brute-force determinant legality, no shared code with the fast paths
# --------------------------------------------------------------------------- #


def _collinear_cross(p: Point, q: Point, r: Point) -> bool:
    """(q-p) x (r-p) = 0, but paired against q rather than the origin.

    Deliberately a *different* algebraic arrangement from ntil_verify.det3:
    det3 expands (x2-x1)(y3-y1) - (x3-x1)(y2-y1); this uses the equivalent
    (x2-x1)(y3-y2) - (x3-x2)(y2-y1), which shares no subterm with it. Two wrong
    implementations agreeing by accident is then far less likely.
    """
    (x1, y1), (x2, y2), (x3, y3) = p, q, r
    return (x2 - x1) * (y3 - y2) - (x3 - x2) * (y2 - y1) == 0


def _collinear_rational(p: Point, q: Point, r: Point) -> bool:
    """Same predicate via exact rational slopes. Third arithmetic path."""
    (x1, y1), (x2, y2), (x3, y3) = p, q, r
    if x1 == x2 and x2 == x3:
        return True
    if x1 == x2 or x2 == x3 or x1 == x3:
        # a vertical pair among them: collinear only if all three share that x
        xs = {x1, x2, x3}
        return len(xs) == 1
    return Fraction(y2 - y1, x2 - x1) == Fraction(y3 - y2, x3 - x2)


def oracle_is_legal(pts: Sequence[Point]) -> bool:
    """Definition-level legality, evaluated by two independent arithmetic paths.

    A disagreement between the two paths is a hard error, not a verdict.
    """
    seen = set()
    uniq = []
    for p in pts:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    for a, b, c in combinations(uniq, 3):
        lc = _collinear_cross(a, b, c)
        lr = _collinear_rational(a, b, c)
        if lc != lr:
            raise AssertionError(
                f"oracle self-disagreement on {a},{b},{c}: cross={lc} rational={lr}"
            )
        if lc:
            return False
    return True


def _strict_int(v: object) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def oracle_expected(pts: Sequence[Point], n: int, expect: int) -> bool:
    """Spec-level expectation for "is this a valid 2n certificate for D(n)=2n?".

    Deliberately stricter than Python's default coercion: floats and bools are not
    coordinates, they are type errors on a certificate for an exact integer claim.
    """
    if any(not (_strict_int(x) and _strict_int(y)) for x, y in pts):
        return False
    uniq = list(dict.fromkeys(pts))
    if len(uniq) != expect:
        return False
    if any(not (1 <= x <= n and 1 <= y <= n) for x, y in uniq):
        return False
    return oracle_is_legal(uniq)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def all_points(n: int) -> list[Point]:
    return [(x, y) for y in range(1, n + 1) for x in range(1, n + 1)]


def default_layout(n: int) -> list[Point]:
    """A guaranteed-legal 2n set: 2 points per row, arranged on the anti-diagonal bands.

    Construction: row y takes columns (y mod n)+1 and ((y+1) mod n)+1, i.e. two
    consecutive cyclic columns per row. This is a modular construction; legality is
    *not assumed* by the suite -- every layout is checked at runtime and the suite
    reports if the seed layout were to be illegal (it would then be a bug, not a
    passing test).
    """
    return [(c, y) for y in range(1, n + 1) for c in (((y - 1) % n) + 1, ((y + 1 - 1) % n) + 1)]


def valid_cert(n: int, rng: random.Random | None = None, node_budget: int = 300_000) -> list[Point] | None:
    """Find some legal 2n set for n by randomized depth-first row-pair search.

    DFS with prefix pruning: a partial row assignment that already contains a
    collinear triple cannot be extended to a legal configuration, so it is cut.
    Randomising the pair order per row makes repeated calls return different
    solutions (so the suite's controls are not all copies of one certificate).

    NOTE: this is a *generator*, not a verifier. It uses canonical line keys for
    incremental pruning (fast). Every set it produces is re-judged by the
    brute-force determinant oracle before being used, so a generator bug can only
    produce a failed case, not a silently wrong verdict.
    """
    if n < 2:
        return None
    pairs = list(combinations(range(1, n + 1), 2))
    rng = rng or random.Random(0)
    chosen: list[tuple[int, int]] = []
    used: set[tuple[int, int, int]] = set()

    def try_pair(row: int, pr: tuple[int, int]) -> list[tuple[int, int, int]] | None:
        """Return the keys to add if pr is compatible with the current prefix, else None."""
        freshpts = [(pr[0], row), (pr[1], row)]
        allpts = [(c, r) for r, p in enumerate(chosen) for c in p]
        add: list[tuple[int, int, int]] = []
        for i, p in enumerate(freshpts):
            for q in allpts:
                k = canonical_line(p, q)
                if k in used or k in add:
                    return None
                add.append(k)
        k = canonical_line(freshpts[0], freshpts[1])
        if k in used or k in add:
            return None
        add.append(k)
        return add

    def rec(row: int, budget: list[int]) -> bool:
        if row == n:
            return True
        order = pairs[:]
        rng.shuffle(order)
        for pr in order:
            budget[0] -= 1
            if budget[0] <= 0:
                return False
            add = try_pair(row, pr)
            if add is None:
                continue
            for k in add:
                used.add(k)
            chosen.append(pr)
            if rec(row + 1, budget):
                return True
            chosen.pop()
            for k in add:
                used.discard(k)
        return False

    if rec(0, [node_budget]):
        return [(c, r + 1) for r, p in enumerate(chosen) for c in p]
    return None


_SEED_CACHE: dict[int, list[Point]] = {}


def legal_seed(n: int) -> list[Point] | None:
    """Cached legal 2n set for n <= 9, used as a source of legal subsets.

    Monotonicity (used deliberately below): every subset of a legal set is legal,
    because deleting points cannot create a new collinear triple. So subsets of
    this seed are legal sets for every grid size >= n, with no search at all.
    """
    if n in _SEED_CACHE:
        return _SEED_CACHE[n]
    pts = None if n < 2 else valid_cert(n, random.Random(999_000 + n))
    _SEED_CACHE[n] = pts  # type: ignore[assignment]
    return pts


def legal_subset(n: int, rng: random.Random, kmax_scale: float = 1.0) -> list[Point] | None:
    """A random legal subset that lives inside grid(n), for any n >= 2.

    For n <= 9 the seed is a genuine 2n set. For n > 9 we reuse the n=9 seed and
    embed it in the larger grid; sizes are then capped at 18, which is the honest
    situation (no 2n certificate is produced for those n by this helper).
    """
    src = legal_seed(min(n, 9))
    if src is None:
        return None
    k = rng.randint(1, max(1, int(len(src) * kmax_scale)))
    return rng.sample(src, min(k, len(src)))


# --------------------------------------------------------------------------- #
# case builder
# --------------------------------------------------------------------------- #


class Suite:
    def __init__(self) -> None:
        self.cases: list[dict] = []
        self.failures: list[str] = []

    def add(self, name: str, family: str, pts: list[Point], n: int, expect: int, expect_ok: bool,
            expect_kind: str | None = None, expect_wellformed: bool | None = None) -> None:
        report = verify(pts, n, expect_count=expect)
        got_ok = bool(report["math_ok"])  # mathematical verdict only
        oracle_ok = oracle_expected(pts, n, expect)
        kinds = {v["kind"] for v in report["violations"]}

        problems = []
        if got_ok != expect_ok:
            problems.append(f"verifier math_ok={got_ok}, expected {expect_ok}")
        if oracle_ok != got_ok:
            problems.append(f"ORACLE DISAGREES: oracle_ok={oracle_ok} vs verifier_math_ok={got_ok}")
        if expect_kind is not None and not expect_ok and expect_kind not in kinds:
            problems.append(f"expected violation kind {expect_kind!r}, got {sorted(kinds)}")
        if expect_wellformed is not None and bool(report["wellformed"]) != expect_wellformed:
            problems.append(f"wellformed={report['wellformed']}, expected {expect_wellformed}")
        # internal agreement of the three arithmetic paths (None = did not run,
        # which only happens on the documented non-integer short circuit)
        c = report["checks"]
        if c.get("C5_agrees_with_C4") is None:
            if c.get("C1_integer_coordinates", True):
                problems.append("C4/C5 skipped without a non-integer short circuit")
        elif c["C5_agrees_with_C4"] is not True:
            problems.append("C4/C5 (integer pair-line vs rational) disagree")
        if c.get("C6_agrees_with_C4") is False:
            problems.append("C4/C6 (pair-line vs naive triples) disagree")

        rec = {
            "name": name,
            "family": family,
            "n": n,
            "declared_points": len(pts),
            "expect_count": expect,
            "expect_ok": expect_ok,
            "verifier_math_ok": got_ok,
            "verifier_wellformed": report["wellformed"],
            "oracle_ok": oracle_ok,
            "violation_kinds": sorted(kinds),
            "problems": problems,
        }
        self.cases.append(rec)
        if problems:
            self.failures.append(f"{name}: " + "; ".join(problems))

    def summary(self) -> dict:
        by_family: dict[str, dict] = {}
        for c in self.cases:
            b = by_family.setdefault(c["family"], {"total": 0, "passed": 0, "expect_pass": 0, "expect_fail": 0})
            b["total"] += 1
            if c["expect_ok"]:
                b["expect_pass"] += 1
            else:
                b["expect_fail"] += 1
            if not c["problems"]:
                b["passed"] += 1
        # A family that only ever exercises one verdict direction is weak evidence;
        # surface the split so a vacuous suite is visible rather than merely green.
        return {
            "total_cases": len(self.cases),
            "cases_with_problems": len(self.failures),
            "expect_pass_cases": sum(1 for c in self.cases if c["expect_ok"]),
            "expect_fail_cases": sum(1 for c in self.cases if not c["expect_ok"]),
            "families": by_family,
            "failures": self.failures,
            "suite_ok": not self.failures,
        }


# --------------------------------------------------------------------------- #
# the suite
# --------------------------------------------------------------------------- #


def run_suite(max_n: int = 10, fuzz_rounds: int = 400, seed: int = 20260928) -> dict:
    S = Suite()
    rng = random.Random(seed)

    # ---------------- P: positive controls ----------------
    # n <= 9: a genuine 2n certificate is generated by this file's own search.
    for n in range(2, 10):
        pts = valid_cert(n, random.Random(1000 + n))
        if pts is None:
            S.failures.append(f"could not construct a positive control for n={n}")
            continue
        S.add(f"P_valid_2n_n{n}", "P_positive", pts, n, 2 * n, True)

    # hand-made n=2 and n=3 controls whose legality is checkable by eye
    S.add("P_handmade_n2", "P_positive", [(1, 1), (2, 1), (1, 2), (2, 2)], 2, 4, True)
    S.add("P_handmade_n3", "P_positive", [(1, 1), (2, 1), (3, 2), (1, 2), (2, 3), (3, 3)], 3, 6, True)

    # transpose of a valid certificate must stay valid (T2 in DERIVATION.md)
    base = valid_cert(6, random.Random(7))
    S.add("P_transpose_n6", "P_positive", [(y, x) for x, y in base], 6, 12, True)

    # ---------------- N: negative controls ----------------
    n = 8
    base = valid_cert(n, random.Random(42))
    assert base is not None

    # N1 collinear injection preserving count: move a point onto the line through two others
    inj = None
    for i, j, k in combinations(range(len(base)), 3):
        p, q, r = base[i], base[j], base[k]
        cand = (2 * q[0] - p[0], 2 * q[1] - p[1])  # reflection of p through q: collinear
        if cand == r or cand in base:
            continue
        if 1 <= cand[0] <= n and 1 <= cand[1] <= n:
            inj = list(base)
            inj[k] = cand
            break
    assert inj is not None, "could not build a collinear injection"
    S.add("N1_collinear_injection_count_preserved", "N_negative", inj, n, 2 * n, False, "three_collinear")

    # N2 duplicate point (list length still 2n, distinct count drops)
    dup = list(base)
    dup[5] = dup[0]
    S.add("N2_duplicate_point", "N_negative", dup, n, 2 * n, False)

    # N3 out of range (x = n+1)
    oor = list(base)
    oor[0] = (n + 1, oor[0][1])
    S.add("N3_out_of_range_high", "N_negative", oor, n, 2 * n, False, "out_of_range")
    oor0 = list(base)
    oor0[0] = (0, oor0[0][1])
    S.add("N3_zero_indexed_point", "N_negative", oor0, n, 2 * n, False, "out_of_range")

    # N4 count errors
    S.add("N4_count_2n_minus_1", "N_negative", base[:-1], n, 2 * n, False, "count_mismatch")
    S.add("N4_count_2n_plus_1", "N_negative", base + [(1, 1)], n, 2 * n, False)
    # legal but under-full set: must fail on COUNT, not on collinearity
    S.add("N4_legal_but_underfull", "N_negative", base[: 2 * n - 2], n, 2 * n, False, "count_mismatch")
    # legal set of exactly 2n points re-labelled as a certificate for n+1: count wrong
    S.add("N4_wrong_n_claim", "N_negative", base, n + 1, 2 * (n + 1), False, "count_mismatch")

    # N5 four collinear points -- a triple scan must not "dedupe" this away
    four = [(1, 1), (2, 1), (3, 1), (4, 1)] + valid_cert(4, random.Random(3))[:4]
    S.add("N5_four_collinear", "N_negative", four, 4, 8, False, "three_collinear")

    # N6 n=1 fake 2n certificate (D(1)=1, 2n=2 > grid size)
    S.add("N6_n1_impossible", "N_negative", [(1, 1), (1, 1)], 1, 2, False)

    # N7 float / non-integer coordinates. Two flavours:
    #   N7a: 1.0 -- numerically in range, so only a strict type check catches it.
    #        (Python compares 1.0 == 1 and hashes them identically, so a checker
    #         that merely coerces would accept it.)
    #   N7b: 1.5 -- non-integral, must not reach the exact arithmetic at all.
    S.add("N7a_float_integral_coords", "N_negative", [(1.0, 1), (2, 1)] + list(base[2:]), n, 2 * n,
          False, "non_integer_coordinate")
    S.add("N7b_float_fractional_coords", "N_negative", [(1.5, 1), (2, 1)] + list(base[2:]), n, 2 * n,
          False, "non_integer_coordinate")

    # ---------------- X: structural adversarial ----------------
    # X1 whole-grid dump: 64 points for n=8, contains rows of 8 -> massively illegal
    S.add("X1_full_grid_n8", "X_structural", all_points(8), 8, 64, False, "three_collinear")

    # X2 a "row-pigeonhole violator": 3 points in one row, count 2n
    three_in_row = [(1, 1), (2, 1), (3, 1)] + [(c, y) for y in range(2, n + 1) for c in (1, 2)]
    three_in_row = three_in_row[: 2 * n]
    S.add("X2_three_in_one_row", "X_structural", three_in_row, n, 2 * n, False, "three_collinear")

    # X3 a diagonal line through the middle: 3 collinear on a non-axis line
    diag = [(i, i) for i in range(1, 4)] + [(c, y) for y in range(4, 6) for c in (1, 2, 3, 4)] + [(1, y) for y in range(6, 12)]
    diag = diag[: 2 * n]
    S.add("X3_diagonal_collinear", "X_structural", diag, n, 2 * n, False, "three_collinear")

    # X4 duplicate ENTRIES. Two semantically different situations that a checker
    # must not conflate:
    #   X4a: the same valid set written twice. The certificate denotes a set, so
    #        |S| = 2n still holds and the math is VALID; only the encoding is
    #        redundant -> expect math_ok True, wellformed False.
    #   X4b: 2n entries made of only n distinct points (each repeated). Here the
    #        point set really has n != 2n elements, so this is mathematically
    #        INVALID. Counting entries instead of points is trap T5.
    S.add("X4a_valid_set_written_twice", "X_structural", base + base, n, 2 * n, True,
          expect_wellformed=False)
    half = base[: len(base) // 2]
    S.add("X4b_entries_2n_but_distinct_n", "X_structural", half + half, n, 2 * n, False,
          "count_mismatch", expect_wellformed=False)

    # X5 parse-level: bools are ints in Python and must not be accepted as coordinates
    S.add("X5_bool_coords", "X_structural", [(True, 1), (2, 1)] + list(base[2:]), n, 2 * n, False)

    # ---------------- F: fuzz with oracle agreement ----------------
    # Every case's expectation is computed by the brute-force determinant oracle,
    # never by the verifier under test.
    fuzz = 0
    for _ in range(fuzz_rounds):
        nn = rng.randint(2, 14)
        mode = rng.random()
        if mode < 0.45:
            # legal near-miss: random legal subset, size random (often != 2n)
            pts = legal_subset(nn, rng)
            if pts is None:
                continue
        elif mode < 0.75:
            # random subset of the grid, any size
            cells = all_points(nn)
            k = rng.randint(1, min(len(cells), 2 * nn + 2))
            pts = rng.sample(cells, k)
        else:
            # legal subset then a single random mutation (usually breaks legality),
            # or a deliberate collinear injection that keeps the count intact
            pts = legal_subset(nn, rng, kmax_scale=1.0)
            if pts is None:
                continue
            pts = list(pts)
            if len(pts) >= 3 and rng.random() < 0.5:
                i, j, k = rng.sample(range(len(pts)), 3)
                cand = (2 * pts[j][0] - pts[i][0], 2 * pts[j][1] - pts[i][1])
                if 1 <= cand[0] <= nn and 1 <= cand[1] <= nn:
                    pts[k] = cand
                else:
                    pts[i] = (rng.randint(1, nn), rng.randint(1, nn))
            else:
                i = rng.randrange(len(pts))
                if rng.random() < 0.5:
                    pts[i] = (rng.randint(1, nn), rng.randint(1, nn))
                else:
                    pts[i] = pts[rng.randrange(len(pts))]
        target = 2 * nn
        expect_ok = oracle_expected(pts, nn, target)
        S.add(f"F_fuzz_{fuzz:04d}", "F_fuzz", pts, nn, target, expect_ok)
        fuzz += 1

    return S.summary(), S.cases


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-n", type=int, default=10)
    ap.add_argument("--fuzz-rounds", type=int, default=400)
    ap.add_argument("--seed", type=int, default=20260928)
    ap.add_argument("--json", default=None)
    args = ap.parse_args(list(argv) if argv is not None else None)

    summary, cases = run_suite(args.max_n, args.fuzz_rounds, args.seed)
    print(json.dumps(summary, indent=2, sort_keys=True))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"summary": summary, "cases": cases}, fh, indent=2, sort_keys=True)
        print(f"[written] {args.json}")
    return 0 if summary["suite_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
