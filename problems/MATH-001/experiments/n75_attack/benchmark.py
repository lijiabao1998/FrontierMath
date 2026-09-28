#!/usr/bin/env python3
"""n=75 attack bench -- instance sizing, parity results, negative controls.

Produces benchmark.json. Nothing here claims a resolution of n=75; the point is to
measure the actual object an attack must face, to record which approaches are
excluded by counting, and to show that the encoder audit has teeth.
"""

from __future__ import annotations

import argparse
import hashlib
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
    audit_any,
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
    # The audit's output schema changed when completeness was required (P1-C): the field is
    # now `layer1_lines_with_missing_triple`, and `complete` replaced `covers_all_lines` as
    # the verdict. This caller was not updated at the time, which the in-round re-run caught
    # as a KeyError on the first A8 attempt; it is fixed here and the teeth condition is
    # strengthened to the completeness criterion rather than "a line was seen".
    c0, c1 = out["controls"][0], out["controls"][1]
    out["audit_has_teeth"] = bool(
        c0.get("complete") is True
        and c0.get("layer1_lines_with_missing_triple") == 0
        and c1.get("complete") is False
        and c1.get("layer1_lines_with_missing_triple", 0) >= 1
    )
    out["schema_note"] = (
        "controls[0] must be complete; controls[1] must be incomplete with at least one line "
        "missing at least one of its C(k,3) triples.")
    return out


def audit_instance(path: str, n: int, group: str | None, out: dict,
                   manifest: str | None = None) -> dict:
    """Run the COMPLETE audit on an actual target DIMACS (protocol gate G2).

    Added because the protocol previously told the reader to run benchmark.py, whose
    negative_controls only tests the audit on a deliberately broken n=5 instance -- so G2
    could have been marked complete without ever auditing the target formula. This runs
    the real thing on the real file.
    """
    if not os.path.exists(path):
        return {"path": path, "ran": False,
                "reason": "instance not found; regenerate it first (see G1)"}
    # Dispatch on the formulation. The cell audit assumes row-major cell variable ids,
    # which is wrong for the orbit encoding where many cells share one variable; a
    # reviewer showed the cell audit reports an intact n=3 rot2 instance as incomplete.
    gadgets = None
    manifest_clauses = None
    if manifest:
        with open(manifest, "r", encoding="utf-8") as fh:
            man = json.load(fh)
        gadgets = man["gadgets"]
        manifest_clauses = man.get("clauses")
    rep = audit_any(n, path, group, gadgets=gadgets, manifest_clauses=manifest_clauses)
    res = {
        "path": os.path.basename(path), "ran": True,
        "dimacs_sha256": None, "n": n, "group": group,
        "complete": rep["complete"], "covers_all_lines": rep.get("covers_all_lines", rep["complete"]),
        "layer1_explicit_lines": rep.get("layer1_explicit_lines"),
        "layer1_triples_expected": rep.get("layer1_triples_expected"),
        "layer1_triples_present": rep.get("layer1_triples_present"),
        "layer1_lines_with_missing_triple": rep.get("layer1_lines_with_missing_triple"),
        "layer2_network_lines": rep.get("layer2_network_lines"),
        "layer2_lines_checked": rep.get("layer2", {}).get("lines_checked", rep.get("lines_checked")),
        "layer2_lines_unchecked": rep.get("layer2", {}).get("lines_unchecked"),
        "lines_with_unrefuted_violation": rep.get("lines_with_unrefuted_violation"),
        "not_refuted": rep.get("not_refuted"),
        "formulation": rep.get("formulation", "cells"),
        "layer2_formula_satisfiable": rep.get("layer2", {}).get("formula_satisfiable"),
        "layer2_vacuous": rep.get("layer2", {}).get("vacuous"),
        "layer2_triples_checked": rep.get("layer2", {}).get("triples_checked"),
        "layer2_not_refuted": rep.get("layer2", {}).get("not_refuted"),
        "containment_mode": rep.get("containment_mode"),
        "clause_multiset_matches_manifest": rep.get("clause_multiset_matches_manifest"),
        "extra_clauses": rep.get("extra_clauses"), "missing_clauses": rep.get("missing_clauses"),
        "completeness_scope": rep["completeness_scope"],
    }
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    res["dimacs_sha256"] = h.hexdigest()
    res["gate_G2_satisfied"] = bool(rep["complete"])
    out["instance_audit"] = res
    return res


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=75)
    ap.add_argument("--audit-instance", default=None, metavar="DIMACS",
                    help="run protocol gate G2 against this actual instance and exit")
    ap.add_argument("--group", default=None, help="symmetry group label for the audit record")
    ap.add_argument("--gadget-manifest", default=None,
                    help="encoder-produced per-line clause manifest; REQUIRED for G2 on an "
                         "orbit instance (the audit fails closed without it)")
    ap.add_argument("--skip-instances", action="store_true")
    ap.add_argument("--json", default=os.path.join(HERE, "benchmark.json"))
    args = ap.parse_args(list(argv) if argv is not None else None)

    n = args.n
    bench: dict = {"n": n, "target": 2 * n, "python": sys.version.split()[0]}

    if args.audit_instance:
        print(f"== G2) complete audit of the actual target instance: {args.audit_instance} ==")
        res = audit_instance(args.audit_instance, n, args.group, bench, args.gadget_manifest)
        for k in ("ran", "dimacs_sha256", "complete", "layer1_lines_with_missing_triple",
                  "layer2_network_lines", "layer2_lines_unchecked", "layer2_formula_satisfiable",
                  "layer2_vacuous", "gate_G2_satisfied"):
            print(f"   {k}: {res.get(k)}")
        if not res.get("ran"):
            print(f"   reason: {res.get('reason')}")
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(bench, fh, indent=2, sort_keys=True, default=str)
        print(f"[written] {args.json}")
        return 0 if res.get("gate_G2_satisfied") else 1

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
        print(f"  {c['name']}: complete={c.get('complete')} "
              f"lines_with_missing_triple={c.get('layer1_lines_with_missing_triple')}")
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
