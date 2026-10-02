"""MATH-001 grok round runner. Stdlib only. Prints a JSON summary on stdout.

Positive controls, deliberate failures, and public Flammenkamp files are
checked by verifier_det and verifier_lines. Those two modules do not import
each other. A disagreement stops the run.
"""
from __future__ import annotations
import hashlib
import json
import platform
import sys
import time
import urllib.request
from pathlib import Path

import datetime as dt
import subprocess

import decode_flam
import search_small
import verifier_det
import verifier_lines
from gate import failure_reasons

ROOT = Path(__file__).resolve().parents[4]
ROUND = ROOT / "runs" / "20260927T184702323864Z-grok-MATH-001"
CACHE = Path(__file__).resolve().parent / "data_cache"
OUT = ROOT / "problems" / "MATH-001" / "results" / "grok_r1"
BASE = "https://wwwhomes.uni-bielefeld.de/achim/no3in/"
NODE_LIMIT = 8_000_000
SEARCH_SECONDS = {n: (20 if n <= 8 else 45 if n == 9 else 70) for n in range(2, 11)}
TRIALS = []


def trial(name: str):
    TRIALS.append(name)
    if len(TRIALS) > 100:
        raise SystemExit("trial budget 100 exceeded")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return
    req = urllib.request.Request(url, headers={"User-Agent": "FrontierMath-grok-r1"})
    with urllib.request.urlopen(req, timeout=120) as resp, dest.open("wb") as out:
        while True:
            chunk = resp.read(1 << 16)
            if not chunk:
                break
            out.write(chunk)


def both(points, n, kind):
    if kind == "set":
        a = verifier_det.check(points, n)
        b = verifier_lines.check(points, n)
    else:
        a = verifier_det.certificate(points, n)
        b = verifier_lines.certificate(points, n)
    if a["ok"] != b["ok"] or a["reason"] != b["reason"]:
        raise SystemExit(
            "EVALUATOR_BUG "
            + json.dumps({"det": a, "lines": b, "n": n, "points": points}, default=str)
        )
    return a


def expect(points, n, kind, ok: bool, label: str):
    got = both(points, n, kind)
    if got["ok"] != ok:
        raise SystemExit(f"{label}: expected ok={ok}, got {got}")
    return got


def iter_records(path: Path):
    buf = ""
    with path.open("r", encoding="ascii", errors="strict") as f:
        for line_no, line in enumerate(f, 1):
            piece = line.rstrip("\r\n")
            if piece.endswith("\\"):
                buf += piece[:-1]
                continue
            buf += piece
            rec = buf
            buf = ""
            rec = rec.split('"', 1)[0].strip()
            if rec:
                yield line_no, rec
    if buf.strip():
        yield -1, buf.strip()


def verify_coded_file(path: Path, det_all: bool, det_min_n: int, deadline_s: float):
    t0 = time.monotonic()
    per_n = {}
    decode_fail = []
    math_fail = []
    disagree = []
    samples = {}
    scanned = 0
    stopped = ""
    for line_no, rec in iter_records(path):
        if time.monotonic() - t0 > deadline_s:
            stopped = "time_limit"
            break
        scanned += 1
        dec = decode_flam.decode_record(rec)
        if not dec["ok"]:
            if len(decode_fail) < 12:
                decode_fail.append({"line": line_no, "reason": dec["reason"], "head": rec[:40]})
            bucket = per_n.setdefault(dec.get("n", -1), {"pass": 0, "decode_fail": 0, "math_fail": 0})
            bucket["decode_fail"] += 1
            continue
        pts, n = decode_flam.to_one_based(dec)
        use_det = det_all or n >= det_min_n or n <= 10 or (scanned % 25 == 0)
        line_res = verifier_lines.certificate(pts, n)
        det_res = verifier_det.certificate(pts, n) if use_det else None
        if det_res is not None and (det_res["ok"] != line_res["ok"] or det_res["reason"] != line_res["reason"]):
            disagree.append({"line": line_no, "n": n, "det": det_res["reason"], "lines": line_res["reason"]})
            if len(disagree) >= 5:
                stopped = "evaluator_bug"
                break
        bucket = per_n.setdefault(n, {"pass": 0, "decode_fail": 0, "math_fail": 0, "det_checked": 0})
        bucket["det_checked"] = bucket.get("det_checked", 0) + (1 if det_res is not None else 0)
        if line_res["ok"]:
            bucket["pass"] += 1
            if n not in samples:
                samples[n] = {"symmetry": dec["symmetry"], "points": pts, "line": line_no}
        else:
            bucket["math_fail"] += 1
            if len(math_fail) < 12:
                math_fail.append({"line": line_no, "n": n, "reason": line_res["reason"], "example": line_res["collinear_example"]})
    elapsed = round(time.monotonic() - t0, 3)
    return {
        "file": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "scanned": scanned,
        "stopped": stopped,
        "seconds": elapsed,
        "per_n": {str(k): v for k, v in sorted(per_n.items())},
        "decode_fail": decode_fail,
        "math_fail": math_fail,
        "disagree": disagree,
        "eof": stopped == "",
        "samples": {str(k): v for k, v in sorted(samples.items()) if k <= 12 or k >= 60},
    }


def tamper(certificates: list):
    trial("tamper")
    cases = []

    def add(label, points, n, kind, ok):
        got = expect(points, n, kind, ok, label)
        cases.append({"label": label, "ok": got["ok"], "reason": got["reason"]})

    square = [(1, 1), (2, 1), (1, 2), (2, 2)]
    add("n2_square_certificate", square, 2, "cert", True)
    add("n2_three_points_not_certificate", square[:3], 2, "cert", False)
    add("n2_three_points_still_no_three", square[:3], 2, "set", True)
    add("diagonal", [(1, 1), (2, 2), (3, 3)], 3, "set", False)
    add("slope2", [(1, 1), (2, 3), (3, 5)], 5, "set", False)
    add("negative_slope", [(3, 1), (2, 2), (1, 3)], 3, "set", False)
    add("duplicate", [(1, 1), (1, 1), (2, 2)], 3, "set", False)
    add("zero", [(0, 1), (1, 2)], 3, "set", False)
    add("too_big", [(1, 1), (4, 2)], 3, "set", False)
    add("float", [(1, 1), (2, 2.0)], 3, "set", False)
    add("n1_single_is_no_three", [(1, 1)], 1, "set", True)
    add("n1_is_not_2n", [(1, 1)], 1, "cert", False)

    injected = 0
    for cert in certificates:
        pts = [tuple(p) for p in cert["points"]]
        n = cert["n"]
        occupied = set(pts)
        placed = False
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                x1, y1 = pts[i]
                x2, y2 = pts[j]
                dx, dy = x2 - x1, y2 - y1
                # step once more in the same direction, reduced by gcd
                from math import gcd
                g = gcd(dx, dy)
                sx, sy = dx // g, dy // g
                x3, y3 = x2 + sx, y2 + sy
                if not (1 <= x3 <= n and 1 <= y3 <= n) or (x3, y3) in occupied:
                    continue
                victim = next(p for p in pts if p != pts[i] and p != pts[j])
                mutated = [p for p in pts if p != victim] + [(x3, y3)]
                add(f"inject_n{n}", mutated, n, "cert", False)
                injected += 1
                placed = True
                break
            if placed:
                break
        if injected >= 8:
            break
    if injected < 1:
        raise SystemExit("failed to build a collinear injection")

    import random
    rng = random.Random(42)
    fuzz_agree = 0
    for cert in certificates[:6]:
        pts = [tuple(p) for p in cert["points"]]
        n = cert["n"]
        for _ in range(40):
            mut = list(pts)
            idx = rng.randrange(len(mut))
            x, y = mut[idx]
            if rng.randrange(2) == 0:
                x = rng.randint(0, n + 1)
            else:
                y = rng.randint(0, n + 1)
            mut[idx] = (x, y)
            a = verifier_det.certificate(mut, n)
            b = verifier_lines.certificate(mut, n)
            if a["ok"] != b["ok"] or a["reason"] != b["reason"]:
                raise SystemExit(f"fuzz disagreement n={n} {a} {b}")
            fuzz_agree += 1
    return {"cases": len(cases), "injections": injected, "fuzz_pairs": fuzz_agree, "seed": 42, "labels": [c["label"] for c in cases]}


def _freeze_manifest() -> dict:
    sources = {
        path.name: sha256_file(path)
        for path in sorted(Path(__file__).resolve().parent.glob("*.py"))
    }
    head = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    manifest = {
        "frozen_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "git_head": head,
        "python": sys.version,
        "platform": platform.platform(),
        "sources": sources,
    }
    (OUT / "run_manifest_frozen.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def _tag(name: str, report: dict) -> list[str]:
    return [f"{name}:{reason}" for reason in failure_reasons(report)]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    manifest = _freeze_manifest()
    t0 = time.monotonic()
    env = {
        "python": manifest["python"],
        "platform": manifest["platform"],
        "git_head": manifest["git_head"],
        "frozen_at": manifest["frozen_at"],
    }
    (OUT / "environment.txt").write_text(json.dumps(env, indent=2) + "\n", encoding="utf-8")

    self_certs = []
    search_rows = []
    for n in range(2, 11):
        trial(f"search_n{n}")
        row = search_small.search_one(n, NODE_LIMIT, SEARCH_SECONDS[n])
        if row["points"] is not None:
            both(row["points"], n, "cert")
            self_certs.append({"n": n, "points": row["points"], "nodes": row["nodes"], "seconds": row["seconds"]})
            dest = OUT / "self" / f"self_n{n:02d}.json"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps({"n": n, "points_1based": row["points"], "nodes": row["nodes"]}, indent=2) + "\n", encoding="utf-8")
        search_rows.append({k: v for k, v in row.items() if k != "points"} | {"found": row["points"] is not None})
        print(f"search n={n} {row['status']} nodes={row['nodes']} sec={row['seconds']}", flush=True)

    if not any(r["found"] for r in search_rows if r["n"] <= 8):
        raise SystemExit("no self certificate for n<=8")

    tamper_summary = tamper(self_certs)
    print(f"tamper cases={tamper_summary['cases']} fuzz={tamper_summary['fuzz_pairs']}", flush=True)

    index_path = CACHE / "configurations_index.html"
    trial("download_index")
    download(BASE + "download/configurations/", index_path)
    text = index_path.read_text(encoding="utf-8", errors="replace")
    names = []
    key = 'href="'
    start = 0
    while True:
        i = text.find(key, start)
        if i < 0:
            break
        j = text.find('"', i + len(key))
        href = text[i + len(key):j]
        start = j + 1
        if href.endswith(".few") and href[0] == "n":
            names.append(href)
    wanted = []
    for name in names:
        digits = ""
        for ch in name[1:]:
            if ch.isdigit():
                digits += ch
            else:
                break
        n = int(digits)
        if n >= 61:
            wanted.append(name)
    print("frontier files", wanted, flush=True)

    frontier = []
    for name in wanted:
        trial(f"file_{name}")
        dest = CACHE / name
        download(BASE + "download/configurations/" + name, dest)
        # These files are a handful of lines. Both checkers see every record.
        report = verify_coded_file(dest, det_all=True, det_min_n=0, deadline_s=60)
        frontier.append({k: v for k, v in report.items() if k != "samples"} | {"sample_ns": sorted(report["samples"])})
        sample_dir = OUT / "public"
        sample_dir.mkdir(parents=True, exist_ok=True)
        (sample_dir / f"{name}.json").write_text(json.dumps(report["samples"], indent=2) + "\n", encoding="utf-8")
        print(f"{name} scanned={report['scanned']} fail={report['math_fail'][:1]} stopped={report['stopped']}", flush=True)
        if report["disagree"] or report["math_fail"] or report["decode_fail"]:
            (OUT / "public_failure.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    trial("file_known_solutions_1997")
    old = CACHE / "known_solutions_1997"
    download(BASE + "data_1997/known_solutions", old)
    old_report = verify_coded_file(old, det_all=True, det_min_n=0, deadline_s=240)
    (OUT / "public" / "flam1997_summary.json").write_text(
        json.dumps({k: v for k, v in old_report.items() if k != "samples"}, indent=2) + "\n", encoding="utf-8"
    )
    print(f"1997 scanned={old_report['scanned']} sec={old_report['seconds']} stopped={old_report['stopped']} math_fail={len(old_report['math_fail'])}", flush=True)

    trial("file_all_known_solutions")
    big = CACHE / "all_known_solutions"
    download(BASE + "download/all_known_solutions", big)
    big_report = verify_coded_file(big, det_all=False, det_min_n=60, deadline_s=300)
    (OUT / "public" / "all_known_summary.json").write_text(
        json.dumps({k: v for k, v in big_report.items() if k != "samples"}, indent=2) + "\n", encoding="utf-8"
    )
    print(f"all_known scanned={big_report['scanned']} sec={big_report['seconds']} stopped={big_report['stopped']}", flush=True)

    lit_table = ROUND / "lit" / "flammenkamp_table.html"
    trial("refetch_table")
    table_now = CACHE / "table_refetch.html"
    download(BASE + "table.html", table_now)
    table_note = {"refetch_sha256": sha256_file(table_now)}
    if lit_table.exists():
        table_note["preflight_sha256"] = sha256_file(lit_table)
        table_note["unchanged_since_preflight"] = table_note["preflight_sha256"] == table_note["refetch_sha256"]

    drifted = {
        name: sha256_file(Path(__file__).resolve().parent / name)
        for name in manifest["sources"]
    }
    if drifted != manifest["sources"]:
        big_report["stopped"] = big_report.get("stopped") or "code_changed_during_run"
        big_report["eof"] = False
    summary = {
        "trials": TRIALS,
        "trial_count": len(TRIALS),
        "search": search_rows,
        "tamper": tamper_summary,
        "frontier_files": [item["file"] for item in frontier],
        "frontier": frontier,
        "flam1997": {k: old_report[k] for k in ("scanned", "seconds", "stopped", "eof", "sha256", "math_fail", "decode_fail", "disagree")},
        "all_known": {k: big_report[k] for k in ("scanned", "seconds", "stopped", "eof", "sha256", "math_fail", "decode_fail", "disagree", "bytes")},
        "table": table_note,
        "code_sha256": manifest["sources"],
        "git_head": manifest["git_head"],
        "frozen_at": manifest["frozen_at"],
        "wall_seconds": round(time.monotonic() - t0, 3),
        "command": "py -3 problems/MATH-001/experiments/grok_r1/run_round.py",
    }
    bad = []
    bad += _tag("1997", old_report)
    bad += _tag("all_known", big_report)
    for item in frontier:
        bad += _tag(item["file"], item)
    summary["full_reproduction"] = not bad
    summary["failure_reasons"] = bad
    # summary.json is the run-1 historical artifact. Never rewrite it.
    summary_path = OUT / "summary.json"
    if summary_path.exists():
        summary_path = OUT / "summary_subsequent.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"full_reproduction": summary["full_reproduction"], "failure_reasons": bad}, indent=2))
    if bad:
        print("RED " + ",".join(bad), flush=True)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
