"""Second pass after removing the false '@' format flag.

Every configurations/*.few record is checked by both verifiers.
all_known_solutions records with n>=55 are checked by the line verifier;
the determinant verifier also checks each .few record and the first three
all_known records of each such n. Disagreement raises SystemExit.
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path

import decode_flam
import verifier_det
import verifier_lines

CACHE = Path(__file__).resolve().parent / "data_cache"
OUT = Path(__file__).resolve().parents[2] / "results" / "grok_r1" / "public"


def records(path: Path):
    buf = ""
    with path.open("r", encoding="ascii", errors="strict") as f:
        for line_no, line in enumerate(f, 1):
            piece = line.rstrip("\r\n")
            if piece.endswith("\\"):
                buf += piece[:-1]
                continue
            buf += piece
            rec = buf.split('"', 1)[0].strip()
            buf = ""
            if rec:
                yield line_no, rec


def check_pair(pts, n):
    a = verifier_det.certificate(pts, n)
    b = verifier_lines.certificate(pts, n)
    if a["ok"] != b["ok"] or a["reason"] != b["reason"]:
        raise SystemExit(json.dumps({"n": n, "det": a, "lines": b}))
    return a


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    few_reports = []
    for path in sorted(CACHE.glob("n*.few")):
        passed = 0
        failed = []
        for line_no, rec in records(path):
            dec = decode_flam.decode_record(rec)
            if not dec["ok"]:
                failed.append({"line": line_no, "stage": "decode", "reason": dec["reason"]})
                continue
            pts, n = decode_flam.to_one_based(dec)
            got = check_pair(pts, n)
            if got["ok"]:
                passed += 1
            else:
                failed.append({"line": line_no, "stage": "math", "n": n, "reason": got["reason"], "example": got["collinear_example"]})
        few_reports.append({"file": path.name, "passed": passed, "failed": failed})
        print(f"{path.name} passed={passed} failed={len(failed)}", flush=True)

    per_n = {}
    scanned = 0
    high = 0
    t1 = time.monotonic()
    big = CACHE / "all_known_solutions"
    for line_no, rec in records(big):
        scanned += 1
        dec = decode_flam.decode_record(rec)
        if not dec["ok"]:
            bucket = per_n.setdefault("decode_fail", {"pass": 0, "fail": 0, "examples": []})
            bucket["fail"] += 1
            if len(bucket["examples"]) < 8:
                bucket["examples"].append({"line": line_no, "reason": dec["reason"], "head": rec[:48]})
            continue
        n = dec["n"]
        if n < 55:
            continue
        high += 1
        pts, n = decode_flam.to_one_based(dec)
        bucket = per_n.setdefault(str(n), {"pass": 0, "fail": 0, "det_checked": 0, "examples": []})
        line_res = verifier_lines.certificate(pts, n)
        if bucket["det_checked"] < 3 or not line_res["ok"]:
            det_res = check_pair(pts, n)
            bucket["det_checked"] += 1
            line_res = det_res
        if line_res["ok"]:
            bucket["pass"] += 1
        else:
            bucket["fail"] += 1
            if len(bucket["examples"]) < 4:
                bucket["examples"].append({"line": line_no, "reason": line_res["reason"]})
    report = {
        "few": few_reports,
        "all_known_records_read": scanned,
        "all_known_n_ge_55": high,
        "per_n": per_n,
        "seconds": round(time.monotonic() - t0, 3),
        "high_seconds": round(time.monotonic() - t1, 3),
    }
    dest = OUT / "recheck_at_alphabet.json"
    dest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"few_failed": sum(len(x["failed"]) for x in few_reports), "high": high, "scanned": scanned, "seconds": report["seconds"]}, indent=2))
    if any(x["failed"] for x in few_reports):
        return 2
    if any(v.get("fail") for v in per_n.values()):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
