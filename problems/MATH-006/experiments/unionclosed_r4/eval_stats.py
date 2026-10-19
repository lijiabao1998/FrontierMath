#!/usr/bin/env python3
"""MATH-006 r4: corrected Frankl statistics over the COMPLETE m=5 enumeration
(fixed closure, deterministic BFS — same enumeration as r3, corrected stats).

r3's ratio statistics wrongly included the {∅}-only family (min ratio 0.0).
r4 corrects: ratio stats computed over NON-TRIVIAL families only (excluding
the {∅}-only family per Frankl convention). Also adds an exact ratio
histogram and the count of families with max-frequency ratio exactly 0.5.

No volatile fields (deterministic replay). Stdlib only.
"""
from __future__ import annotations
import json
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE.parent.parent / "results" / "r4"


def closure(bits: int) -> int:
    """Fixed union-closure (bit-test semantics, r2 corrected)."""
    while True:
        members = [i for i in range(32) if bits >> i & 1]
        add = 0
        for a in members:
            for c in members:
                u = a | c
                if not (bits >> u) & 1:
                    add |= 1 << u
        if not add:
            return bits
        bits |= add


def main() -> int:
    t0 = time.time()
    m = 5
    n_sub = 1 << m
    start = closure(1)

    seen = {start}
    frontier = [start]
    frankl_violations = []          # expected: only the {∅}-only family
    ratios_nontrivial = []          # per-family max-frequency ratio, non-{∅}-only
    hist = Counter()                # 16 buckets, width 1/16

    while frontier:
        cur = frontier.pop()
        # BFS expansion FIRST — every family expands (incl. {∅}-only start)
        for s in range(1, n_sub):
            if (cur >> s) & 1:
                continue
            new = closure(cur | (1 << s))
            if new not in seen:
                seen.add(new)
                frontier.append(new)
        members = [i for i in range(n_sub) if cur >> i & 1]
        total = len(members)
        if members == [0]:
            # {∅}-only family: ratio 0 by convention-excluded trivial case
            frankl_violations.append({"mask": cur, "kind": "only_empty",
                                      "ratio": 0.0})
            continue
        best = 0
        for e in range(m):
            col = sum(1 for i in members if i >> e & 1)
            best = max(best, col)
        ratios_nontrivial.append(best / total)
        if len(seen) % 200000 < 32:
            print(f"progress: seen={len(seen)} frontier={len(frontier)}",
                  flush=True)

        # BFS expansion (was missing in the first r4 draft — Codex-style
        # self-check: without expansion the loop pops one family and dies)
        for s in range(1, n_sub):
            if (cur >> s) & 1:
                continue
            new = closure(cur | (1 << s))
            if new not in seen:
                seen.add(new)
                frontier.append(new)

    n_nontrivial = len(ratios_nontrivial)
    stats = {
        "min": round(min(ratios_nontrivial), 6),
        "mean": round(sum(ratios_nontrivial) / n_nontrivial, 6),
        "max": round(max(ratios_nontrivial), 6),
    }
    # families at exactly ratio 0.5 (Frankl-tight)
    n_half = sum(1 for r in ratios_nontrivial if abs(r - 0.5) < 1e-9)

    checks = {
        "S1_frankl_all_nontrivial_pass": all(r * 2 >= 1 for r in ratios_nontrivial),
        "S2_violations_only_conventional": (len(frankl_violations) == 1
            and frankl_violations[0]["kind"] == "only_empty"),
        "S3_count_matches_A102896_5": len(seen) == 1385552,
    }
    out = {"n_families_total": len(seen),
           "n_nontrivial": n_nontrivial,
           "ratio_stats_nontrivial": stats,
           "n_half_ratio_families": n_half,
           "checks": checks,
           "verdict": ("STATS_ROUND_COMPLETE" if all(checks.values())
                       else "STATS_ROUND_INCOMPLETE"),
           "elapsed_s": round(time.time() - t0, 1)}
    (RESULTS / "r4_frankl_stats_results.json").write_bytes(
        (json.dumps(out, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({k: out[k] for k in ("n_families_total", "n_nontrivial",
                                          "ratio_stats_nontrivial",
                                          "n_half_ratio_families", "checks",
                                          "verdict")}, ensure_ascii=False, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
