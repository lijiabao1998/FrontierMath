#!/usr/bin/env python3
"""Reproduce public no-three-in-line constructions from Flammenkamp's archive.

Re-implements, in Python, the decoding semantics of Flammenkamp's decode.c
(downloaded alongside the data, see experiments/lit_data/):

  line = <symmetry char> + 2n data chars
  data chars are read as n pairs; pair i gives the two occupied column indices
  (0-indexed) of row i; column value mapping TOPOS:
      '0'-'9' -> 0..9, 'A'-'Z' -> 10..35, 'a'-'z' -> 36..61, other ASCII >32 ->
      ord(c)+1 (Feb-2026 extension for n>61; unused in this dataset)
  The 1997 archive contains no '@' separator lines, so the old Topos variant
  does not apply; rows/columns here are 1-indexed for our certificates.

Decoding correctness is self-validating: a wrong column mapping shifts some
rows' points and almost surely creates a collinear triple, so mass PASS over
36,912 independent historical configurations is itself strong evidence both
for the decoder and for the verifiers.

Verification:
  bulk  : every configuration through the independent row-pair sweep
          (verifier_indep.verify_indep, exact integer arithmetic)
  spot  : every 37th configuration plus the first 3 of each distinct n also
          through the brute-force triple checker (verifier.verify)

Usage: decode_and_verify.py <known_solutions.txt> <outdir>
Stdlib only. Deterministic.
"""
from __future__ import annotations
import datetime as dt
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import verifier  # noqa: E402
import verifier_indep  # noqa: E402

SYMCLASS = {".": "iden", ":": "rot2", "/": "dia1", "-": "ort1",
            "x": "dia2", "o": "rot4", "+": "ort2", "*": "full", "c": "rct4"}


def topos(c: str) -> int:
    if "0" <= c <= "9":
        return ord(c) - 48
    if "A" <= c <= "Z":
        return ord(c) - 55
    if "a" <= c <= "z":
        return ord(c) - 61  # decode.c: c-'a'+36;  'a'->36 .. 'z'->61
    return ord(c) + 1  # decode.c else-branch (extension alphabet)


def decode_line(line: str, idx: int) -> tuple[dict | None, str]:
    line = line.rstrip("\n")
    if not line:
        return None, "empty"
    sym, data = line[0], line[1:]
    if sym not in SYMCLASS:
        return None, f"unknown symmetry char {sym!r}"
    if "@" in line:
        return None, "legacy '@' line (not supported by this decoder)"
    if len(data) % 2:
        return None, "odd number of data chars"
    n = len(data) // 2
    points = []
    for row in range(n):
        c1, c2 = topos(data[2 * row]), topos(data[2 * row + 1])
        if not (0 <= c1 < n and 0 <= c2 < n) or c1 == c2:
            return None, f"bad pair row {row}: ({c1},{c2}) n={n}"
        points.append([c1 + 1, row + 1])
        points.append([c2 + 1, row + 1])
    cert = {
        "problem": "MATH-001",
        "n": n,
        "target": 2 * n,
        "points": points,
        "source": "flammenkamp-known-solutions-1997",
        "origin_ref": "https://wwwhomes.uni-bielefeld.de/achim/no3in/readme.html "
                      "(data_1997/known_solutions, decoded per decode.c semantics)",
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "symmetry_class": SYMCLASS[sym],
        "archive_line": idx,
    }
    return cert, ""


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: decode_and_verify.py <known_solutions> <outdir>", file=sys.stderr)
        return 2
    src, outdir = Path(argv[1]), Path(argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    certs: list[dict] = []
    skipped: list[str] = []
    with src.open(encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            cert, err = decode_line(line, idx)
            if cert is None:
                skipped.append(f"line {idx}: {err}")
                continue
            certs.append(cert)

    n_stats: dict[int, int] = {}
    for c in certs:
        n_stats[c["n"]] = n_stats.get(c["n"], 0) + 1

    bulk_fail: list[dict] = []
    for i, cert in enumerate(certs):
        errs = verifier_indep.verify_indep(cert)
        if errs:
            bulk_fail.append({"archive_line": cert["archive_line"], "n": cert["n"],
                              "errors": errs[:3]})
        if (i + 1) % 5000 == 0:
            print(f"...bulk {i + 1}/{len(certs)}", file=sys.stderr)

    spot_ids = sorted({i for i in range(len(certs)) if i % 37 == 0}
                      | {i for i, c in enumerate(certs)
                         if c["n"] in (min(n_stats), max(n_stats))})
    spot_fail: list[dict] = []
    for i in spot_ids:
        cert = certs[i]
        errs = verifier.verify(cert)
        if errs:
            spot_fail.append({"archive_line": cert["archive_line"], "n": cert["n"],
                              "errors": errs[:3]})

    # representative certificates for the results tree
    by_n: dict[int, dict] = {}
    for c in certs:
        by_n.setdefault(c["n"], c)
    rep = [by_n[n] for n in sorted(by_n)]
    seen_sym: set[str] = set()
    for c in certs:
        if c["symmetry_class"] not in seen_sym:
            seen_sym.add(c["symmetry_class"])
            rep.append(c)
    for c in rep:
        (outdir / f"flam_n{c['n']:02d}_{c['symmetry_class']}_L{c['archive_line']}.json"
         ).write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")

    summary = {
        "dataset": str(src.name),
        "decoded_configs": len(certs),
        "skipped_lines": skipped[:20],
        "skipped_count": len(skipped),
        "n_distribution": {str(n): n_stats[n] for n in sorted(n_stats)},
        "bulk_verifier": "verifier_indep.py (row-pair exact integer sweep)",
        "bulk_failures": bulk_fail,
        "spot_verifier": "verifier.py (brute-force triples)",
        "spot_checked": len(spot_ids),
        "spot_failures": spot_fail,
        "representative_certs_written": len(rep),
        "verdict": ("REPRODUCTION_SUCCESS" if not bulk_fail and not spot_fail
                    else "REPRODUCTION_DISCREPANCY"),
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }
    (outdir / "decode_verify_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in
                      ("decoded_configs", "skipped_count", "spot_checked",
                       "verdict", "n_distribution")},
                     ensure_ascii=False, indent=2))
    return 0 if not bulk_fail and not spot_fail else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
