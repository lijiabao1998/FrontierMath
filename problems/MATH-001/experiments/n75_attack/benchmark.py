#!/usr/bin/env python3
"""n=75 attack bench -- instance sizing, parity results, negative controls.

Produces benchmark.json. Nothing here claims a resolution of n=75; the point is to
measure the actual object an attack must face, to record which approaches are
excluded by counting, and to show that the encoder audit has teeth.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from math import comb
from typing import Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "independent_verifier_r1")))

from encoder import (  # noqa: E402
    SYMMETRY_GROUPS,
    audit_cnf_covers_lines,
    encode_cells,
    encode_orbits,
    maximal_lines,
    orbit_feasibility,
    orbits,
)


def line_census(n: int) -> dict:
    t0 = time.time()
    lines = maximal_lines(n, 3)
    by_len = Counter(len(l) for l in lines)
    inc = sum(len(l) for l in lines)
    # clause cost with the hybrid encoding used by encoder.CNF.add_at_most:
    #   |l| == 3  -> 1 explicit clause
    #   |l| >= 4  -> sequential-counter at-most-2 over |l| literals, about 4*|l|
    enum_clauses = sum(comb(len(l), 3) for l in lines if comb(len(l), 3) <= 4096)
    net_lines = [l for l in lines if comb(len(l), 3) > 4096]
    net_clauses = sum(4 * len(l) + 8 for l in net_lines)
    return {
        "n": n,
        "maximal_lines_ge3": len(lines),
        "total_incidences": inc,
        "max_line_length": max(len(l) for l in lines),
        "line_length_histogram": {str(k): v for k, v in sorted(by_len.items())},
        "lines_encoded_explicitly": sum(1 for l in lines if comb(len(l), 3) <= 4096),
        "lines_needing_cardinality_network": len(net_lines),
        "estimated_clauses": enum_clauses + net_clauses,
        "seconds": round(time.time() - t0, 2),
    }


def negative_controls(n: int = 5) -> dict:
    """Show the CNF audit catches a deliberately broken encoder."""
    out: dict = {"n": n, "controls": []}
    tmp = os.path.join(HERE, "negative_tests")
    os.makedirs(tmp, exist_ok=True)

    good_path = os.path.join(tmp, f"n{n}_cells_good.cnf")
    cnf = encode_cells(n, 2)
    with open(good_path, "w", encoding="utf-8") as fh:
        fh.write(cnf.dimacs())
    good = audit_cnf_covers_lines(n, good_path)
    out["controls"].append({"name": "intact_encoder", "expect_covers": True, **good})

    # Broken encoder: drop every line constraint of one direction family, by
    # rebuilding with a filtered line list. We emulate by deleting the clauses of
    # triples that lie on lines with direction (1,1) -- simplest is to remove all
    # clauses containing a specific known-diagonal triple.
    lines = maximal_lines(n, 3)
    # find a line to sabotage: the main diagonal
    diag = [(i, i) for i in range(1, n + 1)]
    sabotage = None
    for l in lines:
        if set(diag).issubset(set(l)) or l == diag:
            sabotage = l
            break
    if sabotage is None:
        sabotage = lines[0]
    order = [(x, y) for y in range(1, n + 1) for x in range(1, n + 1)]
    var_of = {cell: i + 1 for i, cell in enumerate(order)}
    bad_vars = {var_of[c] for c in sabotage}
    bad_path = os.path.join(tmp, f"n{n}_cells_missing_line_family.cnf")
    kept = 0
    removed = 0
    with open(bad_path, "w", encoding="utf-8") as fh:
        fh.write(f"p cnf {cnf.nvars} {len(cnf.clauses)}\n")
        for cl in cnf.clauses:
            if len(cl) == 3 and all(v < 0 for v in cl) and all(-v in bad_vars for v in cl):
                removed += 1
                continue
            fh.write(" ".join(str(v) for v in cl) + " 0\n")
            kept += 1
    bad = audit_cnf_covers_lines(n, bad_path)
    out["controls"].append(
        {"name": "missing_line_family", "sabotaged_line": sabotage, "removed_clauses": removed,
         "kept_clauses": kept, "expect_covers": False, **bad}
    )
    out["audit_has_teeth"] = (
        out["controls"][0]["covers_all_lines"] is True
        and out["controls"][1]["covers_all_lines"] is False
        and out["controls"][1]["lines_not_covered"] >= 1
    )
    return out


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=75)
    ap.add_argument("--skip-instances", action="store_true")
    ap.add_argument("--json", default=os.path.join(HERE, "benchmark.json"))
    args = ap.parse_args(list(argv) if argv is not None else None)

    n = args.n
    bench: dict = {"n": n, "target": 2 * n, "python": sys.version.split()[0]}

    print(f"== line census for n={n} ==")
    cens = line_census(n)
    bench["line_census"] = cens
    print(f"  {cens['maximal_lines_ge3']} maximal lines with >=3 points, "
          f"{cens['total_incidences']} incidences, longest line {cens['max_line_length']}")
    print(f"  encoded explicitly: {cens['lines_encoded_explicitly']}, "
          f"needing a cardinality network: {cens['lines_needing_cardinality_network']}")
    print(f"  estimated clauses: {cens['estimated_clauses']:,}   ({cens['seconds']}s)")

    print("== orbit structure and parity exclusions ==")
    par: dict = {}
    for g in SYMMETRY_GROUPS:
        feas = orbit_feasibility(n, SYMMETRY_GROUPS[g], 2 * n)
        par[g] = feas
        print(f"  {g:>5}: sizes {feas['orbit_size_multiset']}  feasible={feas['feasible']}"
              + (f"  -- {feas['reason']}" if feas["reason"] else ""))
    bench["orbit_feasibility"] = par
    bench["parity_excluded_groups"] = [g for g, f in par.items() if not f["feasible"]]
    print(f"  -> excluded by counting alone: {bench['parity_excluded_groups']}")

    print("== rot2 (180-degree) instance for n=75 ==")
    feas = par["rot2"]
    bench["rot2_instance"] = feas
    if not args.skip_instances and feas["feasible"]:
        t0 = time.time()
        try:
            cnf = encode_orbits(n, "rot2", 2 * n)
            bench["rot2_instance"].update({
                "vars": cnf.nvars, "clauses": len(cnf.clauses),
                "dimacs_bytes": len(cnf.dimacs()),
                "sha256": cnf.sha256(), "build_seconds": round(time.time() - t0, 2),
            })
            print(f"  built: vars={cnf.nvars:,} clauses={len(cnf.clauses):,} "
                  f"bytes={len(cnf.dimacs()):,}  sha256={cnf.sha256()[:16]}  ({t0 and round(time.time()-t0,1)}s)")
        except MemoryError as exc:
            bench["rot2_instance"]["build_error"] = f"MemoryError: {exc}"
            print(f"  build failed: MemoryError")
        except Exception as exc:  # noqa: BLE001
            bench["rot2_instance"]["build_error"] = f"{type(exc).__name__}: {exc}"
            print(f"  build failed: {type(exc).__name__}: {exc}")

    print("== negative controls: does the CNF audit catch a broken encoder? ==")
    neg = negative_controls(5)
    bench["negative_controls"] = neg
    for c in neg["controls"]:
        print(f"  {c['name']}: covers_all_lines={c['covers_all_lines']} "
              f"lines_not_covered={c['lines_not_covered']}")
    print(f"  audit_has_teeth={neg['audit_has_teeth']}")

    bench["claims"] = {
        "solved_n75": False,
        "status": "COMPUTE_REQUIRED",
        "note": (
            "No claim of D(75)=150 or D(75)<150 is made. No DRAT/LRAT proof was "
            "produced, so any UNSAT from a solver is residue, not a theorem."
        ),
    }

    with open(args.json, "w", encoding="utf-8") as fh:
        json.dump(bench, fh, indent=2, sort_keys=True, default=str)
    print(f"[written] {args.json}")
    return 0 if neg["audit_has_teeth"] else 1


if __name__ == "__main__":
    sys.exit(main())
