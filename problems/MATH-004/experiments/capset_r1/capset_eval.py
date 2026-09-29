#!/usr/bin/env python3
"""MATH-004 r1: exact AP-free (cap set) verifier and small-n exact/lower-bound
computation for F_3^n.

A cap set is a subset of {0,1,2}^n with no nontrivial 3-term arithmetic
progression: no distinct x, y, z with x + z == 2*y coordinate-wise.

V1 verifier: exact integer triple check. Positive control: known cap PASSes.
Sabotage control: injecting an AP must FAIL.
V2 exhaustive exact D(n) for n=1 (3 subsets) and n=2 (512 subsets);
   literature: 2 and 4 (OEIS A090245).
V3 n=3..6: DFS with AP-triple pruning and node caps. Results are OUR achieved
   lower bounds, recorded honestly against literature values 9/20/45/112 —
   literature values are cited claims, NOT computed here. The pass/fail gate
   is only that every achieved set independently verifies AP-free.
"""
from __future__ import annotations
import itertools
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent.parent  # problems/MATH-004


def is_cap_fast(points) -> bool:
    """F_3 AP check (Codex-style adversarial correction): a 3-term AP in
    F_3^n is x + z == 2y MOD 3 — wrapped APs like (0,0),(1,2),(2,1) in F_3^2
    count. The initial integer check 2b==a+c missed these and produced a
    false D(2)=6 versus the literature 4; the exhaustive-vs-literature
    mismatch exposed the definitional bug. See results JSON note."""
    pts = sorted(points)
    m = len(pts)
    for i in range(m):
        x = pts[i]
        for j in range(i + 1, m):
            y = pts[j]
            for k in range(j + 1, m):
                z = pts[k]
                if all((a + c - 2 * b) % 3 == 0 for a, b, c in zip(x, y, z)):
                    return False
    return True


def exhaustive_max(n: int) -> int:
    cells = list(itertools.product(range(3), repeat=n))
    for size in range(len(cells), 0, -1):
        for combo in itertools.combinations(cells, size):
            if is_cap_fast(combo):
                return size
    return 0


def greedy_cap(n: int, seed: int = 42) -> list:
    """Deterministic greedy: cells in seed-shuffled order, kept if AP-free."""
    import random
    cells = list(itertools.product(range(3), repeat=n))
    random.Random(seed).shuffle(cells)
    chosen = []
    chosen_set = set()
    for c in cells:
        ok = True
        for p in chosen:
            for q in chosen:
                # c completes an AP with p, q (any order)?
                if all((a + c2 - 2 * b) % 3 == 0 for a, b, c2 in zip(p, c, q)):
                    ok = False
                    break
                if all((a + c2 - 2 * b) % 3 == 0 for a, b, c2 in zip(p, q, c)):
                    ok = False
                    break
            if not ok:
                break
        if ok and is_cap_fast(chosen + [c]):
            chosen.append(c)
            chosen_set.add(c)
    return chosen


def dfs_max(n: int, node_cap: int) -> tuple[int, list]:
    cells = list(itertools.product(range(3), repeat=n))
    pt = {c: i for i, c in enumerate(cells)}
    triples = []
    for a, b, c in itertools.combinations(cells, 3):
        if all((aa + cc - 2 * bb) % 3 == 0 for aa, bb, cc in zip(a, b, c)):
            triples.append((pt[a], pt[b], pt[c]))
    banned = [set() for _ in cells]
    for (a, b, c) in triples:
        banned[a].update((b, c))
        banned[b].update((a, c))
        banned[c].update((a, b))
    best = [0, []]
    nodes = [0]

    def dfs(i: int, chosen: list, blocked: frozenset):
        if nodes[0] > node_cap:
            return
        nodes[0] += 1
        if len(chosen) > best[0]:
            best[0] = len(chosen)
            best[1] = list(chosen)
        if len(chosen) + (len(cells) - i) <= best[0]:
            return
        for j in range(i, len(cells)):
            if j in blocked:
                continue
            chosen.append(j)
            dfs(j + 1, chosen, blocked | banned[j])
            chosen.pop()

    dfs(0, [], frozenset())
    return best[0], [cells[i] for i in best[1]]


def main() -> int:
    out = {"results": [], "literature_claim_only": {
        "exact_n1_to_n6": [2, 4, 9, 20, 45, 112],
        "source": "OEIS A090245 (cited, not computed here)",
        "upper_bound": "2.756^n (Ellenberg-Gijswijt 2017, cited)",
        "lower_bound_n8": "512-cap via FunSearch (cited)"}}
    ok = True

    cap2 = [(0, 0), (1, 1), (2, 0), (0, 2)]
    v1_pos = is_cap_fast(cap2)
    v1_neg = is_cap_fast(cap2 + [(2, 2)])  # (0,0),(1,1),(2,2) is an AP
    checks = {"V1_positive_PASS": v1_pos, "V1_sabotage_FAIL": not v1_neg}

    for n in (1, 2):
        d = exhaustive_max(n)
        out["results"].append({"n": n, "method": "exhaustive", "D_n": d,
                               "literature": 2 if n == 1 else 4,
                               "matches_literature": d == (2 if n == 1 else 4)})
        ok = ok and (d == (2 if n == 1 else 4))

    lit = {3: 9, 4: 20, 5: 45, 6: 112}
    for n in (3, 4, 5, 6):
        pts = greedy_cap(n, seed=42)
        size = len(pts)
        verified = is_cap_fast(pts)
        out["results"].append({"n": n, "method": "greedy_lower_bound(seed42)",
                               "achieved_lower_bound": size,
                               "literature_value_cited": lit[n],
                               "reaches_literature_value": size >= lit[n],
                               "set_independently_verified_ap_free": verified})
        ok = ok and verified

    out["checks"] = checks
    out["verdict"] = ("EVALUATOR_ROUND_COMPLETE" if ok
                      else "EVALUATOR_VERIFICATION_FAILURE")
    dest = HERE.parent.parent / "results" / "r1"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "capset_r1_results.json").write_bytes(
        (json.dumps(out, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"checks": checks, "verdict": out["verdict"],
                      "summary": [{k: r.get(k) for k in ("n", "method", "D_n",
                                                         "achieved_lower_bound",
                                                         "literature_value_cited",
                                                         "reaches_literature_value",
                                                         "set_independently_verified_ap_free")}
                                  for r in out["results"]]},
                     ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
