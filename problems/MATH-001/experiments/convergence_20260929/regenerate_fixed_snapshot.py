"""Mechanical regression of pinned historical corpus bytes; never downloads data."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

HERE = Path(__file__).resolve().parent
CANONICAL = HERE.parent / "canonical_evidence"
ROOT = HERE.parents[3]
JOBS = {
    "audit": ("known_solutions_1997.txt",
              "5e127d7be1c060a4d9021356b14848661fac8b76efee45c79acba5b7b7cd80f4",
              "audit_r1_artifacts.py", "r1_artifact_verification.json"),
    "database": ("dl/all_known_solutions",
                 "c27f8f53286be5b047a46bf1e469985e44efd4e6955783e8d0fb5ad66b7effde",
                 "verify_all_known.py", "all_known_solutions_verification.json"),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("job", choices=JOBS)
    args = parser.parse_args()
    corpus_name, expected, script, result_name = JOBS[args.job]
    corpus = CANONICAL / "provenance" / corpus_name
    if not corpus.is_file() or digest(corpus) != expected:
        raise SystemExit("Pinned historical corpus missing or SHA-256 mismatch; refusing execution")
    output = CANONICAL / "evidence" / result_name
    command = [sys.executable, script]
    if args.job == "audit":
        command += ["--corpus-only"]
    command += ["--json", "../evidence/" + result_name]
    sources = sorted((CANONICAL / "database").glob("*.py"))
    sources += sorted((CANONICAL / "verifier").glob("*.py"))
    sources += [Path(__file__).resolve()]
    record = {
        "classification": "FIXED_HISTORICAL_SNAPSHOT_SOFTWARE_REGRESSION",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "python": sys.version, "platform": platform.platform(),
        "command": command,
        "cwd": str((CANONICAL / "database").relative_to(ROOT)).replace("\\", "/"),
        "input_sha256": expected,
        "source_sha256": {str(p.relative_to(ROOT)).replace("\\", "/"): digest(p) for p in sources},
    }
    evidence = HERE / "evidence"
    evidence.mkdir(exist_ok=True)
    log = evidence / (args.job + ".log")
    # Refuse to reuse an old output after any failed invocation.
    output.unlink(missing_ok=True)
    with log.open("w", encoding="utf-8", newline="\n") as stream:
        try:
            result = subprocess.run(command, cwd=CANONICAL / "database", stdout=stream,
                                    stderr=subprocess.STDOUT, timeout=780)
            record["exit_code"] = result.returncode
        except subprocess.TimeoutExpired:
            record["exit_code"] = 124
            record["failure"] = "fixed 780-second software regression timeout"
    record["finished_at"] = datetime.now(timezone.utc).isoformat()
    record["input_unchanged"] = digest(corpus) == expected
    record["sources_unchanged"] = all(digest(ROOT / name) == sha for name, sha in record["source_sha256"].items())
    record["log_sha256"] = digest(log)
    record["result_sha256"] = digest(output) if output.exists() else None
    record["passed"] = (record["exit_code"] == 0 and record["input_unchanged"]
                        and record["sources_unchanged"] and output.exists())
    (evidence / (args.job + "_run.json")).write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: record[k] for k in ("exit_code", "passed", "result_sha256", "finished_at")}))
    return 0 if record["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
