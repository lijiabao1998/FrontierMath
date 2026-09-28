#!/usr/bin/env python3
"""Re-execute the MATH-001 verifications inside the ADMITTED round.

Staged so each invocation fits inside a single foreground call: the background runner in
this environment terminates long jobs, so the re-execution is split with `--only` and the
partial evidence files are merged with `--merge`.

Every tool is invoked as a subprocess so its real exit code and stdout are captured, and
every output is written under problems/MATH-001/results/<round-id>/. The acceptance for
this round was frozen before any of this ran (see runs/<round-id>/round.json).

    python reexecute_round.py --json runs/<id>/stage1.json --only A0,A1,A2
    python reexecute_round.py --json runs/<id>/RERUN_EVIDENCE.json --merge runs/<id>/stage1.json
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
IV = os.path.join(HERE, "independent_verifier_r1")
NA = os.path.join(HERE, "n75_attack")
LIT = os.path.join(HERE, "lit_data")
ROUND_ID = "20260928T034737813749Z-dsk-MATH-001"
OUT = os.path.join(ROOT, "results", ROUND_ID)

ALL = ["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8"]


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd, cwd, log_name, ev, timeout=5400):
    """Run a tool, capture exit code + stdout into a log, and record the invocation."""
    t0 = time.time()
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    elapsed = round(time.time() - t0, 2)
    os.makedirs(OUT, exist_ok=True)
    log = os.path.join(OUT, log_name)
    with open(log, "w", encoding="utf-8") as fh:
        fh.write("$ " + " ".join(cmd) + f"\n[cwd] {cwd}\n[exit] {p.returncode}\n")
        fh.write(f"[seconds] {elapsed}\n\n===== stdout =====\n{p.stdout}\n"
                 f"===== stderr =====\n{p.stderr}\n")
    ev["commands"].append({"cmd": " ".join(cmd), "cwd": os.path.relpath(cwd, HERE),
                           "exit": p.returncode, "seconds": elapsed,
                           "log": os.path.relpath(log, HERE),
                           "stdout_tail": p.stdout[-1000:]})
    print(f"   exit={p.returncode}  {elapsed}s  ({log_name})", flush=True)
    return p


def jload(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(ev, msg):
    ev["failures"].append(msg)


# --------------------------------------------------------------------------- #


def stage_A0(ev):
    p = run([sys.executable, "fetch_third_party.py", "--check"], LIT, "00_fetch_check.log", ev)
    hashes = {}
    for rel in ("known_solutions_1997.txt", "dl/all_known_solutions"):
        fp = os.path.join(LIT, rel)
        if os.path.exists(fp):
            hashes[rel] = {"bytes": os.path.getsize(fp), "sha256": sha256_file(fp)}
    ev["machine"]["provenance_fetch_check_exit"] = p.returncode
    ev["machine"]["corpus_hashes"] = hashes
    ev["criteria"]["A0_provenance"] = {"exit": p.returncode, "corpus_hashes": hashes,
                                       "passed": p.returncode == 0}
    if p.returncode != 0:
        fail(ev, "A0 provenance: fetch_third_party.py --check did not pass")


def stage_A1(ev):
    out = os.path.join(OUT, "A1_adversarial_summary.json")
    run([sys.executable, "adversarial_suite.py", "--fuzz-rounds", "600", "--json", out],
        IV, "A1_adversarial.log", ev)
    s = jload(out)["summary"]
    passed = bool(s["cases_with_problems"] == 0 and s["expect_pass_cases"] > 0
                  and s["expect_fail_cases"] > 0)
    ev["criteria"]["A1_adversarial_suite"] = {
        "total_cases": s["total_cases"], "cases_with_problems": s["cases_with_problems"],
        "expect_pass_cases": s["expect_pass_cases"], "expect_fail_cases": s["expect_fail_cases"],
        "both_directions_exercised": s["expect_pass_cases"] > 0 and s["expect_fail_cases"] > 0,
        "passed": passed,
    }
    if not passed:
        fail(ev, "A1 adversarial suite reported problems (or exercised only one verdict direction)")


def stage_A2(ev):
    """A2, with a criterion bug found and fixed DURING the round.

    The first version of this criterion compared the powerset maximum D(n) with the
    row-pair COUNT of legal 2n-sets and required them equal. They are different
    objects -- a maximum size versus a number of configurations -- so the criterion was
    ill-posed and failed for n=2 on the very first in-round run (D=4 vs count=1). This is
    recorded rather than quietly patched: the corrected criterion compares the two
    quantities that ARE the same object, namely the number of maximum legal sets from the
    powerset enumeration against the number of legal 2n-sets from the row-pair
    enumeration, and separately requires both methods to agree that D(n) = 2n.
    """
    out = os.path.join(OUT, "A2_ground_truth.json")
    run([sys.executable, "brute_force.py", "--powerset-max", "4", "--rowpair-max", "8",
         "--json", out], IV, "A2_brute_force.log", ev)
    g = jload(out)
    ps = {r["n"]: r for r in g["powerset"]}
    rp = {r["n"]: r for r in g["rowpair"]}
    overlap = sorted(set(ps) & set(rp))
    # n = 1 is excluded from the count comparison on purpose, and the reason is recorded:
    # the row-pair enumeration has no configurations there by construction (a 2n-certificate
    # needs 2 points and the grid has 1 cell), while the powerset enumeration finds the
    # single maximum legal set {(1,1)} of size 1. Both are correct; they are different
    # objects at n=1. For n >= 2 a maximum legal set IS a 2n-set in both enumerations.
    count_overlap = [n for n in overlap if n >= 2]
    counts_agree = all(ps[n]["n_legal_max_sets"] == rp[n]["legal_configurations"]
                       for n in count_overlap)
    n1_consistency = (ps[1]["D_n"] == 1 and rp[1]["legal_configurations"] == 0
                      and rp[1]["D_is_2n"] is False)
    # both methods must agree on the 2n question for n >= 2, and disagree at n = 1
    d_is_2n_powerset = {n: ps[n]["D_n"] == 2 * n for n in sorted(ps)}
    d_is_2n_rowpair = {n: rp[n]["D_is_2n"] for n in sorted(rp)}
    both_say_2n = {n: d_is_2n_powerset[n] for n in sorted(ps)}
    consistent_on_2n = all(d_is_2n_powerset[n] == d_is_2n_rowpair[n] for n in overlap)
    passed = bool(counts_agree and consistent_on_2n and n1_consistency
                  and all(d_is_2n_powerset[n] for n in overlap if n >= 2))
    ev["criteria"]["A2_ground_truth"] = {
        "powerset_D": {str(k): ps[k]["D_n"] for k in sorted(ps)},
        "powerset_max_legal_set_counts": {str(k): ps[k]["n_legal_max_sets"] for k in sorted(ps)},
        "rowpair_legal_2n_counts": {str(k): rp[k]["legal_configurations"] for k in sorted(rp)},
        "overlap_n": overlap,
        "count_comparison_overlap_n": count_overlap,
        "counts_agree_on_overlap": counts_agree,
        "n1_consistency_documented": n1_consistency,
        "n1_note": (
            "n=1 is excluded from the count comparison because the two enumerations count "
            "different things there: the row-pair enumeration has 0 configurations by "
            "construction (a 2n-certificate needs 2 points, the grid has 1 cell), while the "
            "powerset enumeration finds the single maximum legal set {(1,1)} of size 1. The "
            "criterion asserts both facts explicitly instead of treating them as a "
            "disagreement."),
        "consistent_on_the_2n_question": consistent_on_2n,
        "D1_is_not_2n": ps[1]["D_n"] == 1,
        "d_is_2n_powerset": {str(k): v for k, v in d_is_2n_powerset.items()},
        "criterion_bug_found_in_round": (
            "The acceptance criterion as first written compared D(n) (a maximum size) with "
            "the row-pair count of legal 2n-sets (a number of configurations) and required "
            "equality. That is ill-posed; it failed at n=2 (D=4 vs count=1) on the first "
            "in-round run. Recorded here rather than silently patched. The corrected "
            "criterion compares like with like: powerset n_legal_max_sets vs rowpair "
            "legal_configurations, plus agreement on the D(n)=2n question itself."),
        "passed": passed,
    }
    if not passed:
        fail(ev, "A2 ground truth: the two methods disagree, or D(1) is not 1")


def stage_A3(ev):
    """A3, run as a FULL-CORPUS sweep, with the frozen criterion reported as ill-posed.

    The acceptance as frozen said the teeth check must require "every
    decode-invariant-preserving mutation to become illegal". The first implementation tested
    a random sample of 400 lines and accepted a 90% rate, so it could not establish that
    statement (a reviewer noted exactly this). Running the check over EVERY corpus line with
    one deterministic mutation each shows the frozen statement is not merely unproven but
    FALSE: 2 of 34,051 legality-changing mutations produce another LEGAL 2n configuration.

    Both survivors were inspected: each is a single 2-character swap (differing positions
    (19,24) at n=21 and (3,43) at n=23) whose result has 2n distinct in-range points and no
    three collinear. They are legality-PRESERVING mutations, not verifier failures -- the
    verifier is right to accept them. The criterion was wrong, not the checker.
    """
    r1 = os.path.join(ROOT, "results", "r1")
    out = os.path.join(OUT, "A3_1997_corpus.json")
    run([sys.executable, "audit_r1_artifacts.py", "--r1", r1, "--json", out,
         "--teeth-all-lines"], IV, "A3_corpus_1997.log", ev)
    c = jload(out)
    f = c["flammenkamp_correct_mapper"]
    teeth = c.get("corpus_teeth_check", {})
    survivors = teeth.get("survivors_detail", [])
    all_survivors_legal = all(x.get("verified_legal_2n_set") for x in survivors) if survivors else True
    corpus_ok = bool(f["stats"].get("decoded") == 36912
                     and f["stats"].get("verify_fail", 0) == 0 and f["n_decode_errors"] == 0)
    ev["criteria"]["A3_1997_corpus"] = {
        "decoded": f["stats"].get("decoded"), "verify_pass": f["stats"].get("verify_pass"),
        "verify_fail": f["stats"].get("verify_fail", 0), "decode_errors": f["n_decode_errors"],
        "corpus_verification_passed": corpus_ok,
        "teeth_mode": teeth.get("mode"),
        "teeth_lines_used": teeth.get("lines_used"),
        "mutations_exercised": teeth.get("mutations_exercised"),
        "mutations_rejected": teeth.get("mutated_now_illegal"),
        "survivors": teeth.get("mutated_still_legal"),
        "teeth_fraction_illegal": teeth.get("teeth_fraction_illegal"),
        "survivors_detail": survivors,
        "all_survivors_confirmed_legal_2n_sets": all_survivors_legal,
        "criterion_as_frozen": ("every decode-invariant-preserving mutation must become illegal"),
        "frozen_criterion_literal_met": False,
        "criterion_status": "ILL_POSED_AS_FROZEN",
        "criterion_explanation": (
            "The frozen criterion is REFUTED, not merely unproven: 2 of 34,051 legality-changing "
            "mutations produce another legal 2n configuration, and both were inspected and "
            "confirmed (single 2-character swaps; 42 and 46 distinct in-range points; no three "
            "collinear). A mutation that maps one legal solution to another is not a verifier "
            "failure, so the criterion asked for something that is not true of the corpus. This "
            "is recorded as a criterion defect rather than silently restated, and A3 is reported "
            "as NOT MET against its frozen wording per the review instruction."),
        "restated_criterion_for_a_future_round": (
            "Of all single 2-character swaps between distinct rows over the whole corpus, every "
            "mutation must either be rejected by the verifier OR be independently confirmed to "
            "produce a legal 2n set. Equivalently: ZERO unexplained survivors. This is checkable "
            "and is what the evidence above establishes."),
        "restated_criterion_met": bool(all_survivors_legal and corpus_ok),
        "passed": False,
        "scope": ("full corpus sweep, one deterministic mutation per line; the whole mutation "
                  "space (~7e7) is not enumerated"),
    }
    fail(ev, "A3: the criterion AS FROZEN is refuted (2 legality-preserving mutations out of "
             "34,051) -- recorded as a criterion defect; the restated, checkable criterion IS "
             "met. A3 therefore counts as not met against its frozen wording.")


def stage_A4(ev):
    out = os.path.join(OUT, "A4_all_known.json")
    run([sys.executable, "verify_all_known.py", "--json", out], IV, "A4_all_known.log", ev)
    k = jload(out)
    missing = [n for n in range(2, 77) if n not in k["n_present"]]
    passed = bool(k["verify_fail"] == 0 and k["n_decode_errors"] == 0 and missing == [75]
                  and k["legacy_alphabet_mismatches_for_n_le_62"] == 0
                  and k["decoded"] == 431008)
    ev["criteria"]["A4_all_known_corpus"] = {
        "decoded": k["decoded"], "verify_pass": k["verify_pass"], "verify_fail": k["verify_fail"],
        "decode_errors": k["n_decode_errors"], "n_min": k["n_min"], "n_max": k["n_max"],
        "n75_present": k["n75_present"], "n75_count": k["n75_count"],
        "only_gap_is_75": missing == [75], "missing_n": missing,
        "legacy_alphabet_mismatches_n_le_62": k["legacy_alphabet_mismatches_for_n_le_62"],
        "passed": passed,
    }
    if not passed:
        fail(ev, "A4 the 431,008-configuration corpus re-verification did not pass")


def stage_A5(ev):
    recs, ok = [], True
    for n, symm in (("76", "o"), ("74", "o"), ("73", "c"), ("72", "o"), ("71", "c")):
        out = os.path.join(OUT, f"A5_record_n{n}.json")
        run([sys.executable, "cross_check_database.py", "--n", n, "--symm", symm,
             "--index", "1", "--json", out], IV, f"A5_record_n{n}.log", ev)
        d = jload(out)
        pa = d.get("path_a") or {}
        recs.append({"n": int(n), "symm": symm, "paths_agree": d.get("paths_agree"),
                     "points": pa.get("points"), "distinct": pa.get("distinct"),
                     "legal": pa.get("legal"), "rows_used": pa.get("rows_used"),
                     "cols_used": pa.get("cols_used"), "code_sha256": pa.get("code_sha256")})
        if not (d.get("paths_agree") and pa.get("legal") and pa.get("points") == 2 * int(n)
                and pa.get("rows_used") == int(n) and pa.get("cols_used") == int(n)):
            ok = False
    ev["criteria"]["A5_record_constructions"] = {"records": recs, "passed": ok}
    if not ok:
        fail(ev, "A5 a record construction did not agree across both retrieval paths")


def stage_A6(ev):
    out = os.path.join(OUT, "A6_calibration.json")
    run([sys.executable, "run_small_n_calibration.py", "--n-max", "7", "--json", out],
        NA, "A6_calibration.log", ev)
    c = jload(out)
    passed = bool(c["calibration_ok"] and not c["failures"])
    ev["criteria"]["A6_bench_calibration"] = {
        "calibration_ok": c["calibration_ok"], "failures": c["failures"],
        "cell_cases": len(c["cell_formulation"]), "orbit_cases": len(c["orbit_formulation"]),
        "unsat_controls": len(c["unsat_controls"]), "passed": passed,
    }
    if not passed:
        fail(ev, "A6 bench calibration reported failures")


def stage_A7(ev):
    a = run([sys.executable, "test_fetch_third_party.py"], LIT, "A7a_fetch_tests.log", ev)
    b = run([sys.executable, "test_cnf_audit_completeness.py"], NA, "A7b_cnf_tests.log", ev)
    c = run([sys.executable, "test_drat_exit_semantics.py"], NA, "A7c_drat_tests.log", ev)
    dout = os.path.join(OUT, "A7d_drat_roundtrip.json")
    d = run([sys.executable, "drat_roundtrip_test.py", "--json", dout],
            NA, "A7d_drat_roundtrip.log", ev)
    drat = jload(dout)["summary"] if os.path.exists(dout) else {}
    cnf_ok = "OK" in open(os.path.join(OUT, "A7b_cnf_tests.log"), encoding="utf-8").read()
    passed = bool(a.returncode == 0 and b.returncode == 0 and c.returncode == 0 and cnf_ok
                  and d.returncode != 0
                  and drat.get("overall_certification") == "BLOCKED"
                  and drat.get("checker_selftest_ok") is True)
    ev["criteria"]["A7_regression_and_drat"] = {
        "fetch_tests_exit": a.returncode, "cnf_tests_exit": b.returncode,
        "drat_semantics_tests_exit": c.returncode, "drat_roundtrip_exit": d.returncode,
        "cnf_tests_reported_OK": cnf_ok,
        "drat_final_status": drat.get("final_status"),
        "drat_overall_certification": drat.get("overall_certification"),
        "checker_selftest_ok": drat.get("checker_selftest_ok"),
        "drat_correctly_nonzero_when_blocked": d.returncode != 0,
        "passed": passed,
    }
    if not passed:
        fail(ev, "A7 regression suites or the DRAT precondition test did not behave as accepted")


def stage_A8(ev):
    out = os.path.join(OUT, "A8_benchmark.json")
    run([sys.executable, "benchmark.py", "--json", out], NA, "A8_benchmark.log", ev)
    b = jload(out)
    passed = bool(b["line_census"]["maximal_lines_ge3"] == 1336828
                  and set(b["parity_excluded_groups"]) == {"rot4", "full"}
                  and b["negative_controls"]["audit_has_teeth"])
    ev["criteria"]["A8_n75_bench_measurements"] = {
        "maximal_lines_ge3": b["line_census"]["maximal_lines_ge3"],
        "parity_excluded_groups": b["parity_excluded_groups"],
        "rot2_vars": b["rot2_instance"].get("vars"),
        "rot2_clauses": b["rot2_instance"].get("clauses"),
        "rot2_sha256": b["rot2_instance"].get("sha256"),
        "audit_has_teeth": b["negative_controls"]["audit_has_teeth"],
        "passed": passed,
    }
    if not passed:
        fail(ev, "A8 n=75 bench measurements changed or did not reproduce")


STAGES = {"A0": stage_A0, "A1": stage_A1, "A2": stage_A2, "A3": stage_A3, "A4": stage_A4,
          "A5": stage_A5, "A6": stage_A6, "A7": stage_A7, "A8": stage_A8}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    ap.add_argument("--only", default=",".join(ALL))
    ap.add_argument("--merge", default=None)
    args = ap.parse_args()

    if args.merge:
        base = (jload(args.json) if os.path.exists(args.json)
                else {"criteria": {}, "commands": [], "machine": {}, "failures": []})
        new = jload(args.merge)
        base.setdefault("criteria", {}).update(new.get("criteria", {}))
        base.setdefault("commands", []).extend(new.get("commands", []))
        base.setdefault("machine", {}).update(new.get("machine", {}))
        base["failures"] = sorted(set(base.get("failures", []) + new.get("failures", [])))
        base["round_id"] = ROUND_ID
        base["all_criteria_passed"] = not base["failures"]
        base["staged_runs"] = base.get("staged_runs", []) + [os.path.basename(args.merge)]
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(base, fh, indent=2, ensure_ascii=False)
        for k in sorted(base["criteria"]):
            v = base["criteria"][k]
            print(f"  [{'PASS' if v.get('passed') else 'FAIL'}] {k}")
        print("failures:", base["failures"] if base["failures"] else "none")
        return 0 if base["all_criteria_passed"] else 1

    only = [x.strip() for x in args.only.split(",") if x.strip()]
    os.makedirs(OUT, exist_ok=True)
    ev = {"round_id": ROUND_ID,
          "executed_at_utc":
              datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat(),
          "python": sys.version.split()[0],
          "output_dir": os.path.relpath(OUT, ROOT).replace("\\", "/"),
          "stages_run": only, "criteria": {}, "commands": [], "failures": [], "machine": {}}
    for tag in only:
        print(f"== {tag} ==", flush=True)
        STAGES[tag](ev)
    ev["all_criteria_passed"] = not ev["failures"]
    with open(args.json, "w", encoding="utf-8") as fh:
        json.dump(ev, fh, indent=2, ensure_ascii=False)
    for k in sorted(ev["criteria"]):
        v = ev["criteria"][k]
        print(f"  [{'PASS' if v.get('passed') else 'FAIL'}] {k}")
    print("failures:", ev["failures"] if ev["failures"] else "none")
    print(f"[written] {args.json}")
    return 0 if ev["all_criteria_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
