"""Resumable fail-closed scan of a Flammenkamp code file.

The manifest is written before the first record is checked. A later edit of
the source or the dataset makes resume refuse, instead of attaching new
hashes to old results. Exit status is 0 only when gate.reproduction_ok.

Checkpoint fields are counts, not the configurations themselves.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import decode_flam
import verifier_det
import verifier_lines
from gate import failure_reasons, reproduction_ok

HERE = Path(__file__).resolve().parent
SOURCE_NAMES = (
    "decode_flam.py",
    "verifier_det.py",
    "verifier_lines.py",
    "gate.py",
    "full_scan.py",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head(start: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(start), "rev-parse", "HEAD"], text=True
    ).strip()


def source_hashes() -> dict:
    return {name: sha256_file(HERE / name) for name in SOURCE_NAMES}


def freeze_manifest(dataset: Path, git_start: Path) -> dict:
    dataset_hash = sha256_file(dataset)
    manifest = {
        "frozen_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "git_head": git_head(git_start),
        "python": sys.version,
        "platform": platform.platform(),
        "sources": source_hashes(),
        "dataset_path": str(dataset),
        "dataset_bytes": dataset.stat().st_size,
        "dataset_sha256": dataset_hash,
    }
    return manifest


def _atomic_write(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def iter_records(path: Path):
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
    if buf.strip():
        yield -1, buf.split('"', 1)[0].strip()


def _empty_state(manifest: dict) -> dict:
    return {
        "manifest": manifest,
        "next_index": 0,
        "scanned": 0,
        "pass_count": 0,
        "decode_fail_count": 0,
        "math_fail_count": 0,
        "disagree_count": 0,
        "stopped": "",
        "eof": False,
        "record_count": None,
        "per_n": {},
        "examples": [],
        "both_checkers": True,
    }


def _note(state: dict, kind: str, detail: dict) -> None:
    if len(state["examples"]) >= 12:
        return
    state["examples"].append({"kind": kind, **detail})


def _check_both(points, n) -> tuple[dict, dict]:
    det = verifier_det.certificate(points, n)
    lines = verifier_lines.certificate(points, n)
    return det, lines


def scan(dataset: Path, checkpoint: Path, manifest: dict, deadline_s: float | None) -> dict:
    if checkpoint.exists():
        state = json.loads(checkpoint.read_text(encoding="utf-8"))
        if state.get("manifest") != manifest:
            state["stopped"] = "manifest_mismatch"
            state["eof"] = False
            _atomic_write(checkpoint, state)
            return state
        if state.get("eof") and not failure_reasons(_view(state)):
            return state
    else:
        state = _empty_state(manifest)
        _atomic_write(checkpoint, state)
    deadline_at = None if deadline_s is None else time.monotonic() + deadline_s
    next_index = state["next_index"]
    index = -1
    for index, (line_no, rec) in enumerate(iter_records(dataset)):
        if index < next_index:
            continue
        if deadline_at is not None and time.monotonic() >= deadline_at:
            state["stopped"] = "time_limit"
            state["eof"] = False
            _atomic_write(checkpoint, state)
            return state
        state["scanned"] += 1
        dec = decode_flam.decode_record(rec)
        if not dec["ok"]:
            state["decode_fail_count"] += 1
            _note(state, "decode", {"line": line_no, "reason": dec.get("reason", "")})
        else:
            pts, n = decode_flam.to_one_based(dec)
            det, lines = _check_both(pts, n)
            bucket = state["per_n"].setdefault(str(n), {"pass": 0, "fail": 0})
            if det["ok"] != lines["ok"] or det["reason"] != lines["reason"]:
                state["disagree_count"] += 1
                bucket["fail"] += 1
                _note(state, "disagree", {"line": line_no, "n": n, "det": det["reason"], "lines": lines["reason"]})
            elif not lines["ok"]:
                state["math_fail_count"] += 1
                bucket["fail"] += 1
                _note(state, "math", {"line": line_no, "n": n, "reason": lines["reason"]})
            else:
                state["pass_count"] += 1
                bucket["pass"] += 1
        state["next_index"] = index + 1
        if state["scanned"] % 2000 == 0:
            _atomic_write(checkpoint, state)
    state["eof"] = True
    state["record_count"] = index + 1 if index >= 0 else 0
    state["stopped"] = ""
    _atomic_write(checkpoint, state)
    return state


def _view(state: dict) -> dict:
    return {
        "stopped": state.get("stopped") or "",
        "decode_fail_count": state.get("decode_fail_count", 0),
        "math_fail_count": state.get("math_fail_count", 0),
        "disagree_count": state.get("disagree_count", 0),
        "eof": state.get("eof") is True,
        "scanned": state.get("scanned"),
        "record_count": state.get("record_count"),
    }


def exit_code(state: dict) -> int:
    return 0 if reproduction_ok(_view(state)) else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--manifest-out", type=Path, required=True)
    parser.add_argument("--deadline", type=float, default=None)
    parser.add_argument("--git-start", type=Path, default=HERE.parents[3])
    args = parser.parse_args(argv)
    if args.checkpoint.exists():
        state = json.loads(args.checkpoint.read_text(encoding="utf-8"))
        manifest = state["manifest"]
        fresh = freeze_manifest(args.dataset, args.git_start)
        if fresh["sources"] != manifest["sources"] or fresh["dataset_sha256"] != manifest["dataset_sha256"]:
            print("RED manifest_mismatch", flush=True)
            return 2
    else:
        manifest = freeze_manifest(args.dataset, args.git_start)
        _atomic_write(args.manifest_out, manifest)
    state = scan(args.dataset, args.checkpoint, manifest, args.deadline)
    view = _view(state)
    reasons = failure_reasons(view)
    print(json.dumps({
        "exit_reasons": reasons,
        "scanned": state.get("scanned"),
        "record_count": state.get("record_count"),
        "pass_count": state.get("pass_count"),
        "decode_fail_count": state.get("decode_fail_count"),
        "math_fail_count": state.get("math_fail_count"),
        "disagree_count": state.get("disagree_count"),
        "stopped": state.get("stopped"),
        "eof": state.get("eof"),
        "per_n_keys": sorted(state.get("per_n", {}), key=lambda s: int(s) if s.lstrip("-").isdigit() else 10**9),
    }, ensure_ascii=False), flush=True)
    return exit_code(state)


if __name__ == "__main__":
    sys.exit(main())
