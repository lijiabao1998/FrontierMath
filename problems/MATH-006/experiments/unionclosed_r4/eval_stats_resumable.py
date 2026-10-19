#!/usr/bin/env python3
"""MATH-006 r4 (resumable): complete m=5 enumeration with corrected Frankl
statistics, using disk checkpoints so an interrupted run CONTINUES from its
checkpoint instead of restarting.

Checkpoint (bfs_m5_checkpoint.json): {"seen": [...], "frontier": [...],
"n_done": int} — seen = all visited family masks; frontier = pending pops.
On resume: seen/frontier restored; enumeration continues until the frontier
empties (complete) or the per-invocation time cap hits (partial, checkpointed
again for the next session).

Deterministic; stdlib only. All families except the {∅}-only trivial family
are Frankl-checked (convention excludes {∅}-only).
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE.parent.parent / "results" / "r4"
CKPT = HERE / "bfs_m5_checkpoint.json"

M = 5
N_SUB = 1 << M
TIME_CAP_S = 20 * 60          # per-invocation cap (checkpoint enables resume)
CKPT_EVERY = 100_000          # new families between checkpoints


def closure(bits: int) -> int:
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


def load_checkpoint():
    if CKPT.exists():
        d = json.loads(CKPT.read_text(encoding="utf-8"))
        return (set(d["seen"]), list(d["frontier"]), d.get("n_done", 0),
                d.get("ratios", []), True)
    return {1}, [1], 0, [], False   # start: the {∅}-only family


def save_checkpoint(seen, frontier, n_done, ratios):
    CKPT.write_text(json.dumps(
        {"seen": sorted(seen), "frontier": frontier, "n_done": n_done,
         "ratios": ratios}, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    t0 = time.time()
    seen, frontier, n_done, ratios_persist, resumed = load_checkpoint()
    total_at_start = len(seen)
    frankl_viol = []
    ratios_nontrivial = ratios_persist  # accumulated across invocations
    n_nontrivial = len(ratios_persist)

    while frontier:
        if time.time() - t0 > TIME_CAP_S:
            save_checkpoint(seen, frontier, n_done, ratios_nontrivial)
            print(json.dumps({"status": "TIME_CAP_PARTIAL",
                              "seen": len(seen), "n_done": n_done}))
            return 2
        cur = frontier.pop()
        n_done += 1
        members = [i for i in range(N_SUB) if cur >> i & 1]
        total = len(members)
        if members == [0]:
            continue  # {∅}-only: trivial, excluded from Frankl stats
        best = 0
        for e in range(M):
            col = sum(1 for i in members if i >> e & 1)
            best = max(best, col)
        ratios_nontrivial.append((cur, best / total))
        if best * 2 < total:
            frankl_viol.append({"mask": cur, "ratio": best / total})
        for s in range(1, N_SUB):
            if (cur >> s) & 1:
                continue
            new = closure(cur | (1 << s))
            if new not in seen:
                seen.add(new)
                frontier.append(new)
        if n_done % CKPT_EVERY == 0:
            save_checkpoint(seen, frontier, n_done, ratios_nontrivial)

    # enumeration complete: final stats over ALL non-trivial families
    ratios = [r for (_, r) in ratios_nontrivial]
    checks = {
        "A_complete": not frontier,
        "B_frankl_all_nontrivial": not frankl_viol,
        "C_total_matches_A102896_5": len(seen) == 1385552,
    }
    out = {"complete": True, "n_families": len(seen),
           "n_nontrivial": n_nontrivial,
           "frankl_violations": frankl_viol,
           "min_ratio": round(min(ratios), 6) if ratios else None,
           "max_ratio": round(max(ratios), 6) if ratios else None,
           "mean_ratio": round(sum(ratios) / len(ratios), 6) if ratios else None,
           "checks": checks,
           "verdict": ("ENUMERATION_COMPLETE_FRANKL_VERIFIED" if all(checks.values())
                       else "ANOMALY_INVESTIGATE"),
           "elapsed_s": round(time.time() - t0, 1)}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "r5_complete_m5_frankl_results.json").write_bytes(
        (json.dumps(out, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({k: out[k] for k in ("n_families", "n_nontrivial",
                                          "frankl_violations", "min_ratio",
                                          "max_ratio", "checks", "verdict")},
                     ensure_ascii=False, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
