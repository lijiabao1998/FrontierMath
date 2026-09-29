"""Hash evidence as Git blobs, and bind fixed-snapshot runs to executed source bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PREFIX = "problems/MATH-001/experiments/"
MANIFEST = PREFIX + "convergence_20260929/COMMITTED_BYTES.sha256"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def blob(tree, path):
    return git("show", (":" if tree == "INDEX" else tree + ":") + path)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def tracked(tree):
    raw = (git("ls-files", "-z") if tree == "INDEX"
           else git("ls-tree", "-r", "--name-only", "-z", tree))
    return sorted(name for name in raw.decode().split("\0") if name and name != MANIFEST
                  and (name.startswith(PREFIX + "canonical_evidence/")
                       or name.startswith(PREFIX + "convergence_20260929/")
                       or name in (".github/workflows/evidence-tools.yml", ".gitattributes")))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tree", choices=("HEAD", "INDEX"), default="HEAD")
    parser.add_argument("--write-index", action="store_true")
    args = parser.parse_args()
    if args.write_index:
        lines = [digest(blob("INDEX", name)) + "  " + name for name in tracked("INDEX")]
        (ROOT / MANIFEST).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        print(f"Wrote {len(lines)} staged Git-blob hashes; stage the manifest before verification")
        return 0
    expected = {}
    for line in blob(args.tree, MANIFEST).decode().splitlines():
        sha, name = line.split("  ", 1)
        if name in expected:
            raise SystemExit("duplicate manifest entry: " + name)
        expected[name] = sha
    failures = []
    if set(expected) != set(tracked(args.tree)):
        failures.append("manifest coverage differs from tracked evidence files")
    for name, sha in expected.items():
        if digest(blob(args.tree, name)) != sha:
            failures.append("Git-blob hash mismatch: " + name)
    for job, result in (("audit", "r1_artifact_verification.json"),
                        ("database", "all_known_solutions_verification.json")):
        run_path = PREFIX + "convergence_20260929/evidence/" + job + "_run.json"
        record = json.loads(blob(args.tree, run_path))
        if not record["passed"]:
            failures.append(job + " regression did not pass")
        for name, sha in record["source_sha256"].items():
            if digest(blob(args.tree, name)) != sha:
                failures.append("executed source differs from committed blob: " + name)
        for name, sha in ((PREFIX + "canonical_evidence/evidence/" + result, record["result_sha256"]),
                          (PREFIX + "convergence_20260929/evidence/" + job + ".log", record["log_sha256"])):
            if digest(blob(args.tree, name)) != sha:
                failures.append("runtime artifact differs from committed blob: " + name)
    print(json.dumps({"tree": args.tree, "files_checked": len(expected), "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
