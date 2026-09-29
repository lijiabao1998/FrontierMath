#!/usr/bin/env python3
"""MATH-006 r1: union-closed exact verifier, small-m exhaustive Frankl check,
family counts, and a Gilmer-inspired numeric exploration.

V1 verifier: F is union-closed iff for all A,B in F, A∪B in F.
   Positive control: closure family PASSes. Sabotage control: a family with a
   missing union FAILs.
V2 exhaustive Frankl check for m = 1..4 (universe {1..m}): enumerate ALL
   2^(2^m) families, keep nonempty union-closed families other than {∅}-only,
   check that some element appears in at least half the sets. Literature says
   all pass — honest reproduction.
V3 family counts per m (computed data point; literature counts to be cited
   in a later round).
V4 Gilmer-inspired numeric exploration (HYPOTHESIS-level, clearly labeled):
   200 random union-closed families (closure of random subfamilies, seeds
   42/12345), record the max-frequency ratio distribution. Observation only —
   NOT a reproduction of Gilmer's theorem.

Deterministic. Stdlib only.
"""
from __future__ import annotations
import itertools
import json
import random
import statistics
from collections import Counter
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent.parent  # problems/MATH-006


def is_union_closed(fam) -> bool:
    famset = set(fam)
    for a in famset:
        for b in famset:
            if (a | b) not in famset:
                return False
    return True


def closure(gen) -> frozenset:
    fam = set(gen)
    if not fam:
        fam.add(())
    changed = True
    while changed:
        changed = False
        for a in list(fam):
            for b in list(fam):
                u = a | b
                if u not in fam:
                    fam.add(u)
                    changed = True
    return frozenset(fam)


def frankl_ok(fam) -> bool:
    """Some element in >= half the sets (families with only the empty set are
    conventionally excluded from the conjecture)."""
    m = len(fam)
    freq = [0] * max((max(s) + 1 for s in fam if s), default=0)
    for s in fam:
        if not s:
            continue
        for e in s:
            if e - 1 < len(freq):
                freq[e - 1] += 1
    return m > 0 and max(freq, default=0) * 2 >= m


def main() -> int:
    out = {"results": []}
    ok = True

    # ---- V1 controls ----
    good = closure([frozenset({1}), frozenset({2})])
    v1_pos = is_union_closed(good)
    bad = set(good) - {frozenset({1, 2})}
    v1_neg = is_union_closed(bad)
    checks = {"V1_positive_PASS": v1_pos, "V1_sabotage_FAIL": not v1_neg}
    out["results"].append({"check": "V1", "v1_pos": v1_pos, "v1_neg": v1_neg})

    # ---- V2/V3 exhaustive m=1..4 ----
    for m in (1, 2, 3, 4):
        universe = set(range(1, m + 1))
        subsets = [frozenset(c)
                   for k in range(m + 1)
                   for c in itertools.combinations(universe, k)]
        n_fam = 1 << len(subsets)
        uc = 0
        frankl_ok_count = 0
        uc_nontrivial = 0
        for bits in range(n_fam):
            fam = []
            for j in range(len(subsets)):
                if bits >> j & 1:
                    fam.append(subsets[j])
            if not fam:
                continue
            famset = frozenset(fam)
            if not is_union_closed(fam):
                continue
            uc += 1
            nonempty = [s for s in fam if s]
            if len(nonempty) == 0:
                continue  # only empty-set family: excluded by convention
            if len(famset) == 1 and frozenset() in famset:
                continue  # { {} } only
            if frankl_ok(fam):
                frankl_ok_count += 1
            uc_nontrivial += 1
        all_pass = (frankl_ok_count == uc_nontrivial)
        ok = ok and all_pass
        out["results"].append({"m": m, "union_closed_families": uc,
                               "nontrivial_frankl_checked": uc_nontrivial,
                               "frankl_ok": frankl_ok_count,
                               "all_satisfy_frankl": all_pass})

    # ---- V4 Gilmer-inspired numeric exploration (HYPOTHESIS-level) ----
    rng = random.Random(42)
    ratios = []
    for trial in range(200):
        m = 6
        universe = set(range(1, m + 1))
        subsets = [frozenset(c) for k in range(m + 1)
                   for c in itertools.combinations(universe, k)]
        seed_fam = [s for s in subsets if rng.random() < 0.3] or [frozenset()]
        fam = closure(seed_fam)
        nonempty = [s for s in fam if s]
        total = len(fam)
        freq = Counter()
        for s in fam:
            for e in s:
                freq[e] += 1
        best = max(freq.values()) if freq else 0
        ratios.append(best / total)
    out["V4_gilmer_numeric_exploration"] = {
        "trials": len(ratios),
        "min_ratio": round(min(ratios), 4),
        "mean_ratio": round(statistics.mean(ratios), 4),
        "max_ratio": round(max(ratios), 4),
        "fracs_ge_038": round(sum(r >= 0.38 for r in ratios) / len(ratios), 4),
        "status": "HYPOTHESIS_LEVEL_NUMERIC_OBSERVATION — "
                  "not a reproduction of Gilmer's theorem",
    }

    out["verdict"] = ("EVALUATOR_ROUND_COMPLETE" if ok else "EVALUATOR_ISSUES")
    dest = HERE / "results" / "MATH-006" / "r1"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "unionclosed_r1_results.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"checks": checks, "verdict": out["verdict"],
                      "results": out["results"],
                      "V4": out["V4_gilmer_numeric_exploration"]},
                     ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
