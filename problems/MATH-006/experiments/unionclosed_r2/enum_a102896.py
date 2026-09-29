#!/usr/bin/env python3
"""MATH-006 r2: BFS enumeration of all empty-set-containing union-closed
families on [m], cross-checked against OEIS A102896 (Moore families on an
n-set — the complement image of ∅-containing union-closed families).

A1: BFS counts must exactly reproduce A102896(m) = 2/7/61/2480 for m = 1..4.
A2: all 2,480 m=4 families checked for Frankl (some element present in at
    least half the sets; {∅}-only families excluded by convention, recorded).
A4: exact min/max of the max-frequency ratio over all m=4 families.

m=5 (A102896(5) = 1,385,552) is NOT enumerated this round (Python budget;
documented in round.json as a next-round candidate). Deterministic; stdlib.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE.parent.parent / "results" / "r2"


def closure(bits: int) -> int:
    """Union-closure of a set-family encoded as a bitmask over subsets.

    Codex convergence-3 fix: the missing-union test previously used
    `u & ~bits`, conflating the number u with BIT number u — that made the
    closure an (almost) identity function on most inputs, which the
    A102896 cross-check exposed (BFS returned 8 families at m=2 instead of
    7, and a bogus Frankl-violating family at m=4). The correct test is
    whether BIT u is set in bits: (bits >> u) & 1.
    """
    while True:
        members = [i for i in range(64) if bits >> i & 1]
        add = 0
        for a in members:
            for c in members:
                u = a | c
                if not (bits >> u) & 1:
                    add |= 1 << u
        if not add:
            return bits
        bits |= add


def bfs_all(m: int) -> list[int]:
    U = [[a | b for b in range(1 << m)] for a in range(1 << m)]
    start = 1  # {∅} = subset index 0 (bit 0)
    seen = {start}
    frontier = [start]
    all_fams = []
    while frontier:
        cur = frontier.pop()
        all_fams.append(cur)
        for s in range(1, 1 << m):
            # NOTE: "already a member" is cur >> s & 1 — a bitmask AND here
            # (s & cur) wrongly skips every odd-index subset because bit 0
            # (the empty set) is always present (Codex convergence-3 bug fix)
            new = closure(cur | (1 << s))
            if new not in seen:
                seen.add(new)
                frontier.append(new)
    return all_fams


def main() -> int:
    expected = {1: 2, 2: 7, 3: 61, 4: 2480}
    out = {"results": []}
    ok = True
    fams_m4 = None
    for m in (1, 2, 3, 4):
        fams = bfs_all(m)
        entry = {"m": m, "bfs_count": len(fams), "A102896": expected[m],
                 "match": len(fams) == expected[m]}
        out["results"].append(entry)
        ok = ok and entry["match"]
        if m == 4:
            fams_m4 = fams

    # A2/A4 on all m=4 ∅-containing families
    frankl_ok = nontrivial = 0
    min_ratio, max_ratio = 1.0, 0.0
    for fam in fams_m4:
        members = [i for i in range(16) if fam >> i & 1]
        if members == [0]:
            continue  # only the empty subset: excluded by convention
        nontrivial += 1
        total = len(members)
        best = 0
        for e in range(4):
            col = sum(1 for i in members if i >> e & 1)
            best = max(best, col)
        ratio = best / total
        min_ratio = min(min_ratio, ratio)
        max_ratio = max(max_ratio, ratio)
        if best * 2 >= total:
            frankl_ok += 1
    a2 = frankl_ok == nontrivial
    out["m4_frankl"] = {"nontrivial_families": nontrivial,
                        "frankl_ok": frankl_ok, "all_satisfy": a2,
                        "min_max_freq_ratio": round(min_ratio, 4),
                        "max_max_freq_ratio": round(max_ratio, 4)}
    ok = ok and a2

    out["verdict"] = ("ENUMERATOR_VALIDATED_FRANKL_M4_PASS" if ok
                      else "DISCREPANCY_INVESTIGATE")
    dest = HERE.parent.parent / "results" / "r2"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "enum_a102896_results.json").write_bytes(
        (json.dumps(out, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"results": out["results"], "m4_frankl": out["m4_frankl"],
                      "verdict": out["verdict"]}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
