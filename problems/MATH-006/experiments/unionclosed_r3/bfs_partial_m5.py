#!/usr/bin/env python3
"""MATH-006 r3: time-boxed partial BFS enumeration of empty-set-containing
union-closed families on [5] — an EXACT LOWER BOUND on the total count
(literature: A102896(5) = 1,385,552).

Method (frozen in round.json): BFS from {∅} (32-bit mask, subset index =
element mask), incremental worklist closure (the FIXED bit-test closure from
r2), distinct-family counting with Frankl check on every visited family.
A1 validates the closure against the known m=2 enumeration (7 families).

Deterministic; stdlib; time budget enforced via node counter and wall clock.
"""
from __future__ import annotations
import datetime as dt
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE.parent.parent / "results" / "r3"

U = [[a | b for b in range(32)] for a in range(32)]


def closure(bits: int) -> int:
    """Fixed closure (r2 corrected): bit-test u via (bits >> u) & 1."""
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
    m = 5
    time_budget_s = 20 * 60  # 20 min hard cap for the BFS leg
    t0 = time.time()

    # A1: closure cross-validation on m=2 (known 7 families)
    seen2 = {1}
    frontier2 = [1]
    while frontier2:
        cur = frontier2.pop()
        for s in range(1, 8):
            new = closure(cur | (1 << s))
            if new not in seen2:
                seen2.add(new)
                frontier2.append(new)
    a1 = len(seen2) == 7

    # BFS on m=5
    start = closure(1)
    seen = {start}
    frontier = [start]
    frankl_violations = []
    ratios = []
    n_sub = 1 << m
    n_visited = 0
    ckpt_every = 20000
    ckpt_path = HERE / "bfs_checkpoint.json"
    while frontier and time.time() - t0 < time_budget_s:
        cur = frontier.pop()
        n_visited += 1
        # Frankl: best element frequency vs |F|
        total = bin(cur).count("1")
        best = 0
        for e in range(m):
            col = sum(1 for i in range(n_sub) if cur >> i & 1 and i >> e & 1)
            best = max(best, col)
        ratio = best / total
        ratios.append(ratio)
        if best * 2 < total:
            frankl_violations.append({"mask": cur, "ratio": round(ratio, 4)})
        members = [i for i in range(n_sub) if cur >> i & 1]
        for s in range(1, n_sub):
            if (cur >> s) & 1:
                continue
            new = closure(cur | (1 << s))
            if new not in seen:
                seen.add(new)
                frontier.append(new)
        if n_visited % ckpt_every == 0:
            # crash-safe checkpoint: frontier is resumable state
            (HERE / "bfs_checkpoint.json").write_text(json.dumps(
                {"n_visited": n_visited, "frontier": frontier,
                 "seen_count": len(seen)}, ensure_ascii=False), encoding="utf-8")

    elapsed = time.time() - t0
    min_ratio = min(ratios) if ratios else None
    max_ratio = max(ratios) if ratios else None
    out = {
        "m": m, "time_budget_s": time_budget_s, "elapsed_s": round(elapsed, 1),
        "visited_families": n_visited,
        "status": "COMPLETE" if not frontier else "PARTIAL_TIME_BOXED",
        "A1_closure_m2_validation": a1,
        "A2_lower_bound": len(seen),
        "A3_frankl_violations": frankl_violations,
        "A4_freq_ratio": {"min": round(min_ratio, 4), "max": round(max_ratio, 4)},
        "note": "distinct visited families = exact lower bound on the total; "
                "A102896(5) = 1,385,552 is the literature total (cited)",
        "generated": datetime_utc_now(),
    }
    dest = HERE.parent.parent / "results" / "r3"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "bfs_partial_m5_results.json").write_bytes(
        (json.dumps(out, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({k: out[k] for k in ("visited_families", "status",
                                          "A1_closure_m2_validation",
                                          "A3_frankl_violations",
                                          "A4_freq_ratio", "elapsed_s")},
                     ensure_ascii=False, indent=2))
    return 0 if (a1 and not frankl_violations) else 1


def datetime_utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


if __name__ == "__main__":
    sys.exit(main())
