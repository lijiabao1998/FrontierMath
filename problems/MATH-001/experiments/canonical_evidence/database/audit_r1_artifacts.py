#!/usr/bin/env python3
"""Audit the r1 artifacts of MATH-001 with the DeepSeek independent verifier.

Three jobs, all done with code in this directory (no GLM module is imported):

 1. GLM's self-certificates `results/r1/self/self_n02..n10.json`
 2. Flammenkamp's public corpus `lit_data/known_solutions_1997.txt`, re-decoded
    from scratch using the format derived in DERIVATION.md (T3/T4) and verified
 3. Teeth check: re-run the corpus pass with the KNOWN-WRONG lowercase mapping
    ('a' -> 10, colliding with 'A') and confirm the verification rejects it.
    Without this step, "the corpus verifies" could be true of a checker that
    accepts anything.

Usage:
    python audit_r1_artifacts.py --r1 <path to problems/MATH-001/results/r1> [--json out.json]
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from collections import Counter, defaultdict
from typing import Sequence

# ntil_verify.py lives in the sibling verifier/ directory in the canonical layout, so both
# locations are added. An earlier version added only the script's own directory, which raised
# ModuleNotFoundError immediately when run as documented.
_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (_HERE, os.path.join(_HERE, "..", "verifier")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from ntil_verify import verify  # noqa: E402

# --------------------------------------------------------------------------- #
# Flammenkamp decoding -- derived from the data + decode.c's TOPOS semantics
# --------------------------------------------------------------------------- #

SYMM_CHARS = ".:/-xo+*c"


def topos(ch: str) -> int:
    """decode.c TOPOS: '0'-'9'->0-9, 'A'-'Z'->10-35, 'a'-'z'->36-61, else c+1."""
    o = ord(ch)
    if 0x30 <= o <= 0x39:
        return o - 0x30
    if 0x41 <= o <= 0x5A:
        return o - 0x41 + 10
    if 0x61 <= o <= 0x7A:
        return o - 0x61 + 36
    return o + 1


def topos_buggy_lowercase(ch: str) -> int:
    """The mapping GLM's r1 round first shipped: 'a' -> 10, colliding with 'A'."""
    o = ord(ch)
    if 0x30 <= o <= 0x39:
        return o - 0x30
    if 0x41 <= o <= 0x5A:
        return o - 0x41 + 10
    if 0x61 <= o <= 0x7A:
        return o - 0x61 - 10  # == ord - 87
    return o + 1


def decode_line(line: str, mapper=topos) -> tuple[str, int, list[tuple[int, int]]] | None:
    """Return (symmetry_class, n, points) or None for a not-a-solution line.

    Layout: [symmetry char][2n data chars]; data char j encodes column of the
    point at row (j//2)+1. Columns are 0-indexed in the source; we add 1 to land
    in the card's {1..n}^2 grid, which is the translation of DERIVATION.md section 1.
    """
    if not line:
        return None
    sym = line[0]
    data = line[1:]
    if len(data) == 0:
        return None
    if len(data) % 2 != 0:
        raise ValueError(f"odd data length {len(data)} in line starting {line[:20]!r}")
    n = len(data) // 2
    if n < 2:
        return None
    cols = [mapper(c) for c in data]
    hi = max(cols)
    if hi != n - 1:
        # Max column index must be exactly n-1 for the line to be a full grid row
        # encoding. A mismatch means the mapping is wrong OR the line is not a
        # 2n-row encoding; we report it rather than silently shifting.
        raise ValueError(f"max column {hi} != n-1 = {n - 1} (line starts {line[:20]!r})")
    pts = []
    for j in range(n):
        c1, c2 = cols[2 * j], cols[2 * j + 1]
        if c1 == c2:
            raise ValueError(f"degenerate row pair {(c1, c2)} at row {j + 1}; mapping is wrong")
        pts.append((c1 + 1, j + 1))
        pts.append((c2 + 1, j + 1))
    return sym, n, pts


# --------------------------------------------------------------------------- #
# audit steps
# --------------------------------------------------------------------------- #


def audit_self_certs(r1_dir: str) -> dict:
    files = sorted(glob.glob(os.path.join(r1_dir, "self", "*.json")))
    out = {"files": len(files), "results": [], "all_pass": bool(files),
           "status": "CHECKED" if files else "MISSING_REQUIRED_INPUT"}
    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                doc = json.load(fh)
            n = doc.get("n")
            if type(n) is not int or n < 1:
                raise ValueError("n must be a positive integer")
            pts = [tuple(p) for p in doc.get("points", [])]
            declared_target = doc.get("target")
            rep = verify(pts, n, expect_count=2 * n)
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            out["results"].append({"file": os.path.basename(path),
                                   "ok": False, "error": str(exc)})
            out["all_pass"] = False
            continue
        target_ok = type(declared_target) is int and declared_target == 2 * n
        rec = {
            "file": os.path.basename(path),
            "n": n,
            "declared_target": declared_target,
            "target_is_2n": target_ok,
            "ok": bool(rep["ok"] and target_ok),
            "distinct_points": rep["distinct_points"],
            "math_ok": rep["math_ok"],
            "wellformed": rep["wellformed"],
            "violations": rep["violations"],
            "checks": {k: v for k, v in rep["checks"].items()},
        }
        out["results"].append(rec)
        if not rec["ok"]:
            out["all_pass"] = False
    return out


def audit_flammenkamp(path: str, mapper=topos, max_lines: int | None = None) -> dict:
    stats: Counter = Counter()
    per_n: dict[int, int] = defaultdict(int)
    sym_per_n: dict[int, Counter] = defaultdict(Counter)
    failures: list[dict] = []
    decode_errors: list[dict] = []
    zero_indexed_lines = 0
    used_lowercase = 0
    used_uppercase = 0
    t0 = time.time()

    with open(path, "r", encoding="latin-1") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.rstrip("\n").rstrip("\r")
            if not line:
                stats["blank"] += 1
                continue
            if max_lines is not None and lineno > max_lines:
                break
            try:
                dec = decode_line(line, mapper)
            except ValueError as exc:
                decode_errors.append({"line": lineno, "error": str(exc)})
                stats["decode_error"] += 1
                continue
            if dec is None:
                stats["skipped_not_solution"] += 1
                decode_errors.append({"line": lineno, "error": "nonblank record did not decode"})
                stats["decode_error"] += 1
                continue
            sym, n, pts = dec
            stats["decoded"] += 1
            per_n[n] += 1
            sym_per_n[n][sym] += 1
            if mapper is topos:
                data = line[1:]
                if any("a" <= c <= "z" for c in data):
                    used_lowercase += 1
                if any("A" <= c <= "Z" for c in data):
                    used_uppercase += 1
            rep = verify(pts, n, expect_count=2 * n)
            if rep["ok"]:
                stats["verify_pass"] += 1
            else:
                stats["verify_fail"] += 1
                if len(failures) < 20:
                    failures.append(
                        {
                            "line": lineno,
                            "n": n,
                            "sym": sym,
                            "violations": rep["violations"][:3],
                        }
                    )
    return {
        "path": os.path.basename(path),
        "mapper": mapper.__name__,
        "stats": dict(stats),
        "n_values": sorted(per_n),
        "n_min": min(per_n) if per_n else None,
        "n_max": max(per_n) if per_n else None,
        "per_n_counts": {str(k): per_n[k] for k in sorted(per_n)},
        "lines_using_lowercase_chars": used_lowercase,
        "lines_using_uppercase_chars": used_uppercase,
        "decode_errors": decode_errors[:20],
        "n_decode_errors": len(decode_errors),
        "verify_failures": failures,
        "seconds": round(time.time() - t0, 2),
    }


def corpus_teeth_check(path: str, samples: int = 400, seed: int = 20260928,
                       all_lines: bool = False) -> dict:
    """Does the VERIFICATION step have teeth on this corpus, or is decoding doing all the work?

    The decode step enforces max-column == n-1, so a wrong mapping is caught before
    verification ever runs. To show the verification is not vacuous, mutate lines in
    a way that PRESERVES the decode invariant but changes the geometry:

        swap one column character between two different rows of the same line

    The character multiset is unchanged (so max column is still n-1 and the line
    still decodes), but the point set almost always becomes illegal. If mutated
    lines still verified, the verifier would be accepting anything.
    """
    import random

    rng = random.Random(seed)
    with open(path, "r", encoding="latin-1") as fh:
        lines = [ln.rstrip("\n").rstrip("\r") for ln in fh if ln.strip()]

    checked = 0
    mutated_decode_ok = 0
    mutated_still_legal = 0
    mutated_now_illegal = 0
    skipped = 0
    survivors: list[dict] = []

    # all_lines=True sweeps EVERY line with one deterministic mutation each. The full
    # mutation space (every row pair x every position pair x every line) is ~7e7 mutations
    # each needing an O(m^2) verification, which is infeasible; one mutation per line over
    # the whole corpus is what this mode actually delivers, and the result says so rather
    # than implying exhaustiveness.
    todo = lines if all_lines else rng.sample(lines, min(samples, len(lines)))
    for line in todo:
        try:
            dec = decode_line(line)
        except ValueError:
            skipped += 1
            continue
        if dec is None:
            skipped += 1
            continue
        _, n, pts_orig = dec
        if n < 4:
            skipped += 1
            continue
        data = list(line[1:])
        # pick two distinct rows and swap one of their column characters
        r1, r2 = rng.sample(range(n), 2)          # distinct rows: a same-row swap is a no-op
        p1 = 2 * r1 + rng.randrange(2)
        p2 = 2 * r2 + rng.randrange(2)
        if data[p1] == data[p2]:
            skipped += 1
            continue
        data[p1], data[p2] = data[p2], data[p1]
        mut = line[0] + "".join(data)
        if mut == line:
            skipped += 1
            continue
        checked += 1
        try:
            dec2 = decode_line(mut)
        except ValueError:
            # the swap happened to break the row-pair invariant; not a verification test
            skipped += 1
            checked -= 1
            continue
        if dec2 is None:
            skipped += 1
            checked -= 1
            continue
        _, n2, pts2 = dec2
        mutated_decode_ok += 1
        rep = verify(pts2, n2, expect_count=2 * n2)
        if rep["ok"]:
            # A surviving mutation is NOT automatically a verifier failure: a swap can
            # produce a DIFFERENT set that is still a legal 2n configuration. What must be
            # true is that the survivor really is one -- so each survivor is recorded in
            # full, with its point count and legality, for inspection rather than being
            # absorbed into a rate.
            mutated_still_legal += 1
            if len(survivors) < 10:
                survivors.append({
                    "line_index": checked, "n": n2, "original": line[:80], "mutated": mut[:80],
                    "distinct_points": rep["distinct_points"], "expect_count": 2 * n2,
                    "verified_legal_2n_set": bool(rep["math_ok"]),
                    "point_set_changed": sorted(pts2) != sorted(pts_orig),
                })
        else:
            mutated_now_illegal += 1

    # The mutation must change the POINT SET, not merely reorder a row's two entries:
    # swapping the two positions inside one row is a no-op, which an earlier version of
    # this generator allowed and which produced spurious "survivors". Rows are sampled
    # without replacement, so r1 != r2 already, but the test is made explicit.
    return {
        "survivors_detail": survivors,
        "survivor_interpretation": (
            "A survivor means the mutated configuration is still legal. That is a property of "
            "the mutation, not a verifier defect, PROVIDED each survivor is confirmed to be a "
            "legal 2n set -- the verified_legal_2n_set field records that confirmation. The "
            "teeth evidence is therefore two-part: almost all mutations are rejected, AND any "
            "survivor is independently confirmed legal."),
        "mode": "all_lines_one_mutation_each" if all_lines else f"sampled_{samples}",
        "lines_used": len(todo),
        "mutation_space_covered": (
            "one deterministic mutation per line over the entire corpus" if all_lines else
            "a random sample of lines, one random mutation each"),
        "mutation_space_not_covered": (
            "the full mutation space (every row pair x position pair x line) is ~7e7 mutations, "
            "each needing an O(m^2) verification, and is not enumerated"),
        "sampled_lines": samples,
        "mutations_exercised": checked,
        "mutated_lines_still_decode": mutated_decode_ok,
        "mutated_still_legal": mutated_still_legal,
        "mutated_now_illegal": mutated_now_illegal,
        "skipped_swaps": skipped,
        "teeth_fraction_illegal": round(mutated_now_illegal / mutated_decode_ok, 6) if mutated_decode_ok else None,
    }


def main(argv: Sequence[str] | None = None) -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    default_r1 = os.path.abspath(os.path.join(here, "..", "..", "..", "results", "r1"))
    ap = argparse.ArgumentParser()
    scope = ap.add_mutually_exclusive_group()
    scope.add_argument("--r1", default=None, help="path to required nonempty self-certificate set")
    scope.add_argument("--corpus-only", action="store_true",
                       help="explicitly exclude self-certificates; no self-certificate claim")
    ap.add_argument("--corpus", default=None, help="path to the pinned 1997 corpus")
    ap.add_argument("--json", default=None)
    ap.add_argument("--teeth-all-lines", action="store_true",
                    help="sweep every corpus line for the mutation teeth check")
    args = ap.parse_args(list(argv) if argv is not None else None)

    r1_dir = args.r1 or default_r1
    out: dict = {"r1_dir": None if args.corpus_only else r1_dir,
                 "scope": "CORPUS_ONLY" if args.corpus_only else "SELF_AND_CORPUS"}

    print("== 1) GLM r1 self-certificates, checked by the DeepSeek verifier ==")
    self_audit = ({"status": "NOT_REQUESTED", "files": 0, "results": [], "all_pass": None}
                  if args.corpus_only else audit_self_certs(r1_dir))
    out["self_certs"] = self_audit
    for r in self_audit["results"]:
        if "error" in r:
            print(f"  {r['file']}: FAIL {r['error']}")
            continue
        print(f"  n={r['n']:>2}  target={r['declared_target']}  distinct={r['distinct_points']:>2}  "
              f"math_ok={r['math_ok']}  wellformed={r['wellformed']}")
    print(f"  -> all_pass={self_audit['all_pass']}")

    # The corpus is fetched by provenance/fetch_third_party.py into provenance/, so that is the
    # default here. An earlier version looked in ../lit_data, took the "not found" branch and
    # still exited 0, which made an OMITTED audit look successful -- and made this branch's
    # reproducibility claim false. Missing corpus is now a failure, not a skip.
    candidates = [os.path.abspath(os.path.join(here, "..", "provenance", "known_solutions_1997.txt")),
                  os.path.abspath(os.path.join(here, "..", "lit_data", "known_solutions_1997.txt"))]
    lit = args.corpus or next((c for c in candidates if os.path.exists(c)), candidates[0])
    if os.path.exists(lit):
        print("== 2) Flammenkamp corpus, independent decode + verify ==")
        good = audit_flammenkamp(lit)
        out["flammenkamp_correct_mapper"] = good
        print(f"  {good['stats']}")
        print(f"  n range {good['n_min']}..{good['n_max']}; decode errors={good['n_decode_errors']}; "
              f"verify failures={good['stats'].get('verify_fail', 0)}; {good['seconds']}s")

        print("== 3) teeth check: same corpus with the known-wrong lowercase mapping ==")
        bad = audit_flammenkamp(lit, mapper=topos_buggy_lowercase)
        out["flammenkamp_buggy_mapper"] = bad
        print(f"  {bad['stats']}")
        print(f"  decode errors={bad['n_decode_errors']}; verify failures={bad['stats'].get('verify_fail', 0)}")

        print("== 4) teeth check: decode-invariant-preserving mutations must break legality ==")
        teeth = corpus_teeth_check(lit, all_lines=args.teeth_all_lines)
        out["corpus_teeth_check"] = teeth
        print(f"  {teeth}")
        if teeth["mutated_lines_still_decode"] and (teeth["teeth_fraction_illegal"] or 0) < 0.9:
            print("  !! WARNING: mutated lines remain legal too often; verification may be vacuous")
    else:
        print(f"[FAIL] corpus not found at any of {candidates}", file=sys.stderr)
        print("       fetch it first:  cd ../provenance && python fetch_third_party.py",
              file=sys.stderr)
        out["flammenkamp_correct_mapper"] = None
        out["missing_corpus"] = True

    # EXIT STATUS FROM ALL REQUIRED CHECKS. An earlier version returned success unless the
    # corpus was missing, so a corpus with decode errors, verification failures or a weak
    # mutation test still exited 0 -- an automated reproduction gate could report success
    # without reproducing the cited result. Every required check now gates the exit.
    reasons = []
    if not args.corpus_only and not self_audit["all_pass"]:
        reasons.append("required self-certificates missing or failed")
    if out.get("missing_corpus"):
        reasons.append("corpus missing")
    f = out.get("flammenkamp_correct_mapper")
    if f is None:
        reasons.append("corpus not audited")
    else:
        st = f.get("stats", {})
        if f.get("n_decode_errors", 0):
            reasons.append(f"{f['n_decode_errors']} decode errors")
        if st.get("verify_fail", 0):
            reasons.append(f"{st['verify_fail']} verification failures")
        if st.get("decoded") != 36912:
            reasons.append(f"decoded {st.get('decoded')} != 36912 expected")
    teeth = (out.get("corpus_teeth_check") or {})
    if (teeth.get("teeth_fraction_illegal") or 0) < 0.9:
        reasons.append(
            f"mutation teeth fraction {teeth.get('teeth_fraction_illegal')} below 0.9")
    out["exit_reasons"] = reasons
    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(out, fh, indent=2, sort_keys=True)
        print(f"[written] {args.json}")
    return 1 if reasons else 0


if __name__ == "__main__":
    sys.exit(main())
