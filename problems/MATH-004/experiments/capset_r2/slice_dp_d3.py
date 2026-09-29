#!/usr/bin/env python3
"""MATH-004 r2: exact D(3) for cap sets in F_3^3 via complete slice-DP.

Method (frozen in runs/20260929T155952970349Z-glm-MATH-004/round.json):
  F_3^3 = three z-layers, each a copy of F_3^2 (9 cells).
  1. enumerate all 512 subsets of F_3^2; keep 2D caps (wrapped mod-3 AP-free).
  2. the optimum has every layer AP-free (an in-layer AP point can be removed
     without creating violations), so enumerating triples of 2D caps is
     COMPLETE for the maximum.
  3. cross-layer constraint: no a in S0, b in S1, c in S2 with
     (a + c - 2b) == 0 (mod 3) coordinate-wise — all three midpoint-layer
     cases are enforced (midpoint in S0 / S1 / S2).
  4. D(3) = max |S0| + |S1| + |S2| over valid triples.

Cross-check: the optimal union is re-verified with the r1 mod-3 triple
checker (independent code path), and literature value is 9 (OEIS A090245;
Edel-FLS 2002 / Potechin 2008 for maximality context). Deterministic; stdlib.
"""
from __future__ import annotations
import itertools
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE.parent.parent / "results" / "r2"

CELLS = list(itertools.product(range(3), repeat=2))
N_CELLS = len(CELLS)
CIDX = {c: i for i, c in enumerate(CELLS)}


def is_cap_2d(points) -> bool:
    pts = list(points)
    m = len(pts)
    for i in range(m):
        for j in range(i + 1, m):
            for k in range(j + 1, m):
                if all((a + c - 2 * b) % 3 == 0
                       for a, b, c in zip(pts[i], pts[j], pts[k])):
                    return False
    return True


def midpoints_mask(A_mask: int, C_mask: int) -> int:
    """9-bit mask of points b such that some a in A, c in C form an AP with
    midpoint b (a + c = 2b mod 3; 2^{-1} = 2 mod 3)."""
    a_list = [i for i in range(N_CELLS) if A_mask >> i & 1]
    c_list = [i for i in range(N_CELLS) if C_mask >> i & 1]
    m = 0
    for ia in a_list:
        for ic in c_list:
            pa, pc = CELLS[ia], CELLS[ic]
            b = tuple((x + z) * 2 % 3 for x, z in zip(pa, pc))
            m |= 1 << CIDX[b]
    return m


def main() -> int:
    # 1. all 2D caps of F_3^2 (as 9-bit masks), incl. empty
    caps = []
    for mask in range(1 << N_CELLS):
        pts = [CELLS[i] for i in range(N_CELLS) if mask >> i & 1]
        if is_cap_2d(pts):
            caps.append(mask)
    K = len(caps)
    sizes = [bin(m).count("1") for m in caps]

    # 2. enumerate (S0, S2) pairs; for each, the best S1 avoiding midpoints
    best = 0
    best_triple = None
    n_valid_triples = 0
    for i0, S0 in enumerate(caps):
        for i2, S2 in enumerate(caps):
            f12 = midpoints_mask(S2, S0)  # forbidden for S0 (midpoints of S1,S2)
            f01 = midpoints_mask(S0, S2)  # hmm: see note below
            # S1 forbidden = midpoints(S0,S2); S0 forbidden = midpoints(S1,S2);
            # S2 forbidden = midpoints(S0,S1)
            f_for_s1 = midpoints_mask(S0, S2)
            for i1, S1 in enumerate(caps):
                if S1 & f_for_s1:
                    continue
                # S0 must avoid midpoints(S1, S2)
                f0 = midpoints_mask(S1, S2)
                if S0 & f0:
                    continue
                # S2 must avoid midpoints(S0, S1)
                f2 = midpoints_mask(S0, S1)
                if S2 & f2:
                    continue
                n_valid_triples += 1
                total = sizes[i0] + sizes[i1] + sizes[i2]
                if total > best:
                    best = total
                    best_triple = (S0, S1, S2)
    # note: f12/f01 variables above are subsumed by the explicit f0/f2 checks;
    # the S1-side constraint is f_for_s1 (midpoints of S0,S2).

    # 3. cross-check optimal union with the r1 mod-3 triple checker
    def union_points(triple):
        pts = set()
        for z, layer in enumerate(triple):
            for i in range(N_CELLS):
                if layer >> i & 1:
                    x, y = CELLS[i]
                    pts.add((x, y, z))
        return sorted(pts)

    def has_ap(points):
        pts = sorted(points)
        m = len(pts)
        for i in range(m):
            for j in range(i + 1, m):
                for k in range(j + 1, m):
                    if all((a + c - 2 * b) % 3 == 0
                           for a, b, c in zip(pts[i], pts[j], pts[k])):
                        return True
        return False

    union_pts = union_points(best_triple) if best_triple else []
    independent_check = (len(union_pts) == best) and not has_ap(union_pts)

    literature = 9
    out = {"n": 3, "n_2d_caps_including_empty": K,
           "valid_triples_checked": n_valid_triples,
           "D3_computed": best,
           "literature_value": literature,
           "replicated": best == literature,
           "independent_union_check": independent_check,
           "optimal_layer_masks": ([bin(t) for t in best_triple]
                                   if best_triple else None),
           "verdict": ("REPLICATED" if (best == literature and independent_check)
                       else "CONTESTED")}
    dest = HERE.parent.parent / "results" / "r2"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "slice_dp_d3_results.json").write_bytes(
        (json.dumps(out, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({k: out[k] for k in ("n_2d_caps_including_empty",
                                          "valid_triples_checked",
                                          "D3_computed", "literature_value",
                                          "replicated",
                                          "independent_union_check",
                                          "verdict")},
                     ensure_ascii=False, indent=2))
    return 0 if out["replicated"] and independent_check else 1


if __name__ == "__main__":
    sys.exit(main())
