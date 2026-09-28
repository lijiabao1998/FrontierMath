#!/usr/bin/env python3
"""Cross-check Flammenkamp's record constructions via a SECOND retrieval path.

Path A: the coded database file `download/all_known_solutions` (431,008 entries),
        decoded with the alphabet from https://.../no3in/encoding.
Path B: the live CGI lookup endpoint, which renders the same configurations as an
        ASCII-art grid:
            https://wwwhomes.uni-bielefeld.de/cgi-bin/cgiwrap/achim/script_lookup?para=FIXED
        POST: symm=<symmetry char>&size=<n>&index=<1-based index>

The two paths share no code and no representation: one is a compact character
encoding of the two selected columns per row, the other is a rendered bitmap of
the grid. If they agree, the decoding in path A is confirmed by an independent
presentation of the same object - and the resulting point set is then verified
for no-three-in-line by this round's own checker.

Usage:
    python cross_check_database.py --n 76 --symm o --index 1 [--json out.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from typing import Sequence

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_all_known import decode as decode_code, check_legal  # noqa: E402

ENDPOINT = "https://wwwhomes.uni-bielefeld.de/cgi-bin/cgiwrap/achim/script_lookup?para=FIXED"

# symmetry characters as documented in the readme:
#   . iden | : rot2 | / dia1 | - ort1 | o rot4 | c rct4 | x dia2 | + ort2 | * full
SYM_NAME = {
    ".": "iden", ":": "rot2", "/": "dia1", "-": "ort1",
    "o": "rot4", "c": "rct4", "x": "dia2", "+": "ort2", "*": "full",
}


def fetch_grid(symm: str, size: int, index: int, timeout: int = 90) -> str:
    body = urllib.parse.urlencode({"symm": symm, "size": size, "index": index}).encode()
    req = urllib.request.Request(ENDPOINT, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("latin-1")


def parse_grid(html: str, n: int) -> tuple[list[tuple[int, int]], dict]:
    """Extract the ASCII grid from the CGI response and return 1-indexed points.

    The response contains <pre> blocks; a grid row is a sequence of n tokens, each
    either '.' (empty) or 'o' (selected). Rows are separated by newlines.
    """
    pre = re.findall(r"<pre>(.*?)</pre>", html, re.S)
    text = "\n".join(pre)
    # drop the leading "  1. solution:     symmetry rot4" header line(s)
    header = [ln.strip() for ln in text.splitlines() if "solution" in ln or "symmetry" in ln]
    rows: list[list[str]] = []
    for ln in text.splitlines():
        toks = ln.replace("\r", "").split()
        # a grid row is exactly n tokens, all '.' or 'o'
        if len(toks) == n and all(t in (".", "o") for t in toks):
            rows.append(toks)
    meta = {
        "header_lines": header,
        "grid_rows_parsed": len(rows),
        "expected_rows": n,
        "rows_complete": len(rows) == n,
        "raw_pre_chars": len(text),
    }
    pts: list[tuple[int, int]] = []
    for r, toks in enumerate(rows, 1):
        for c, t in enumerate(toks, 1):
            if t == "o":
                pts.append((c, r))
    return pts, meta


def coded_entry_from_file(path: str, n: int, symm: str, index: int) -> str | None:
    found: list[str] = []
    with open(path, "r", encoding="latin-1") as fh:
        for ln in fh:
            ln = ln.rstrip("\n").rstrip("\r")
            if ln and ln[0] == symm and (len(ln) - 1) // 2 == n:
                found.append(ln)
    if 0 < index <= len(found):
        return found[index - 1]
    return None


def main(argv: Sequence[str] | None = None) -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    default_file = os.path.abspath(
        os.path.join(here, "..", "lit_data", "dl", "all_known_solutions")
    )
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--symm", required=True)
    ap.add_argument("--index", type=int, default=1)
    ap.add_argument("--file", default=default_file)
    ap.add_argument("--json", default=None)
    args = ap.parse_args(list(argv) if argv is not None else None)

    n = args.n
    out: dict = {"n": n, "symm": args.symm, "symmetry_name": SYM_NAME.get(args.symm), "index": args.index}

    print(f"== path A: coded entry from {os.path.basename(args.file)} ==")
    code = coded_entry_from_file(args.file, n, args.symm, args.index)
    if code is None:
        print("  NOT FOUND")
        out["path_a"] = None
    else:
        sym, nn, pts_a = decode_code(code)
        out["path_a"] = {
            "code_sha256": hashlib.sha256(code.encode()).hexdigest(),
            "code_len": len(code),
            "points": len(pts_a),
            "distinct": len(set(pts_a)),
            "legal": check_legal(pts_a),
            "rows_used": len({p[1] for p in pts_a}),
            "cols_used": len({p[0] for p in pts_a}),
        }
        print(f"  {out['path_a']}")

    print("== path B: ASCII grid from the live CGI endpoint ==")
    html = fetch_grid(args.symm, n, args.index)
    pts_b, meta = parse_grid(html, n)
    out["path_b"] = {
        **meta,
        "points": len(pts_b),
        "distinct": len(set(pts_b)),
        "legal": check_legal(pts_b) if pts_b else None,
        "no_configurations_known": "no configurations are known" in html,
        "count_line": next((l.strip() for l in html.splitlines() if "configurations in database" in l), None),
    }
    print(f"  {out['path_b']}")

    if code is not None and pts_b:
        same = set(pts_a) == set(pts_b)
        out["paths_agree"] = same
        out["points_only_in_A"] = sorted(set(pts_a) - set(pts_b))[:10]
        out["points_only_in_B"] = sorted(set(pts_b) - set(pts_a))[:10]
        print(f"== agreement: {same} ==")
        if not same:
            print(f"  A-only {out['points_only_in_A']}  B-only {out['points_only_in_B']}")
    else:
        out["paths_agree"] = None

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2, sort_keys=True)
        print(f"[written] {args.json}")
    return 0 if out.get("paths_agree") else 1


if __name__ == "__main__":
    sys.exit(main())
