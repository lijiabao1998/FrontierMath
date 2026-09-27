#!/usr/bin/env python3
"""Adversarial (Skeptic) test suite for the MATH-001 evaluators.

For every positive certificate this script builds corrupted variants that MUST
be rejected by BOTH implementations (verifier.verify and
verifier_indep.verify_indep, imported in-process so the same verify() code
paths run as in the CLI):

  collinear_injection : keep count == 2n, move one existing point onto the
                        exact integer line through two other existing points
                        (exhaustive over pairs x free line cells)
  duplicate_point     : copy the first point over the last slot
  out_of_range        : push one point outside {1..n}^2
  count_deficit       : drop one point (count != 2n)

Plus a fake n=1 certificate claiming 2 points (impossible: D(1)=1) and 600
seeded random configurations of 2n points (n=4,5,6), which must all be
rejected: a random no-three-in-line set of size 2n is astronomically unlikely.

The suite FAILS (exit 1) if any corrupted variant is accepted by either
implementation or if v1/v2 ever disagree. Deterministic (random.Random(42)).
Stdlib only.
"""
from __future__ import annotations
import datetime as dt
import json
import random
import sys
from itertools import combinations
from math import gcd
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import verifier  # noqa: E402
import verifier_indep  # noqa: E402


def inject_collinear(cert: dict) -> dict | None:
    """Move the last point onto the exact line through two other points."""
    n = cert["n"]
    anchor = [tuple(p) for p in cert["points"][:-1]]
    occupied = {tuple(p) for p in cert["points"]}
    for a, b in combinations(anchor, 2):
        dx, dy = b[0] - a[0], b[1] - a[1]
        g = gcd(abs(dx), abs(dy))
        if g == 0:
            continue
        sx, sy = dx // g, dy // g
        k = 1
        while True:  # walk the integer line in both directions from a
            cands = [(a[0] + k * sx, a[1] + k * sy),
                     (a[0] - k * sx, a[1] - k * sy)]
            inside = [(x, y) for x, y in cands
                      if 1 <= x <= n and 1 <= y <= n]
            if not inside:
                break  # line has left the grid: terminate for ANY slope
            for cand in inside:
                if cand not in occupied:
                    pts = [list(p) for p in anchor] + [list(cand)]
                    return {**cert, "points": pts,
                            "source": f"tamper:collinear_injection_of_{cert['source']}",
                            "tamper_note": f"moved last point to {cand} on line {a}-{b}"}
            k += 1
    return None


def corrupt(cert: dict, mode: str) -> dict | None:
    n, pts = cert["n"], [list(p) for p in cert["points"]]
    if mode == "duplicate_point":
        pts[-1] = list(pts[0])
        return {**cert, "points": pts,
                "source": f"tamper:duplicate_point_of_{cert['source']}"}
    if mode == "out_of_range":
        pts[0] = [0, 1]
        return {**cert, "points": pts,
                "source": f"tamper:out_of_range_of_{cert['source']}"}
    if mode == "count_deficit":
        return {**cert, "points": pts[:-1], "target": 2 * n,
                "source": f"tamper:count_deficit_of_{cert['source']}"}
    if mode == "collinear_injection":
        return inject_collinear(cert)
    raise ValueError(mode)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: tamper_test.py <cert_dir> <outdir>", file=sys.stderr)
        return 2
    cert_dir, outdir = Path(argv[1]), Path(argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    certs = sorted(cert_dir.glob("self_n*.json"))
    if not certs:
        print("no certificates found", file=sys.stderr)
        return 2
    failures, records = [], []
    total = agreed = 0

    def must_fail(name: str, cert: dict) -> None:
        nonlocal total, agreed
        total += 1
        path = outdir / f"{name}.json"
        path.write_text(json.dumps(cert, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        errs1 = verifier.verify(cert)
        errs2 = verifier_indep.verify_indep(cert)
        ok1, ok2 = not errs1, not errs2
        rec = {"case": name, "v1_pass": ok1, "v2_pass": ok2,
               "v1_first_error": errs1[:1], "v2_first_error": errs2[:1]}
        if ok1 or ok2:
            failures.append(rec)
        if ok1 == ok2:
            agreed += 1
        records.append(rec)

    for cert_path in certs:
        cert = json.loads(cert_path.read_text(encoding="utf-8"))
        tag = f"n{cert['n']:02d}"
        for mode in ("collinear_injection", "duplicate_point",
                     "out_of_range", "count_deficit"):
            bad = corrupt(cert, mode)
            if bad is None:
                records.append({"case": f"{tag}_{mode}",
                                "skipped": "no free collinear cell on any pair-line"})
                continue
            must_fail(f"{tag}_{mode}", bad)

    must_fail("n01_fake_target2", {
        "problem": "MATH-001", "n": 1, "target": 2,
        "points": [[1, 1], [1, 2]], "source": "tamper:fake_n1_boundary",
        "tamper_note": "D(1)=1<2: no 2-point config exists in a 1x1 grid"})

    rng = random.Random(42)
    for n in (4, 5, 6):
        for i in range(200):
            cells = [[x, y] for x in range(1, n + 1) for y in range(1, n + 1)]
            pts = rng.sample(cells, 2 * n)
            must_fail(f"n{n:02d}_random_{i:03d}",
                      {"problem": "MATH-001", "n": n, "target": 2 * n,
                       "points": pts, "source": "tamper:random_fuzz_seed42"})

    summary = {
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "total_cases": total,
        "both_verifiers_agree": agreed,
        "improperly_accepted": failures,
        "verdict": "EVALUATORS_SOUND" if not failures else "EVALUATOR_BUG",
        "note": "collinearity-injection cases keep count==2n, so any PASS "
                "would expose a real evaluator bug, not a count mismatch. "
                "Random fuzz expects rejection (2n-point random sets are "
                "essentially never no-three-in-line for n>=4).",
        "cases": records,
    }
    (outdir / "tamper_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in
                      ("total_cases", "both_verifiers_agree", "verdict")},
                     ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
