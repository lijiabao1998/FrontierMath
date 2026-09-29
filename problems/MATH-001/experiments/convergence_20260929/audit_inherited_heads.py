"""Read-only committed-byte manifest audit of the r2 PR head reviewed in this pass."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
HEAD = "beaf8427afe541361a577d21428edbafafdec0d9"
BASE = "problems/MATH-001/"


def main():
    reports = []
    for name in ("results/r1/hashes.txt", "results/r2/hashes.txt"):
        content = subprocess.check_output(["git", "show", HEAD + ":" + BASE + name], cwd=ROOT).decode()
        failures = []
        for line in content.splitlines():
            if not line.strip():
                continue
            expected, path = line.split(maxsplit=1)
            path = path.lstrip("*")
            try:
                raw = subprocess.check_output(["git", "show", HEAD + ":" + BASE + path],
                                              cwd=ROOT, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                failures.append({"path": path, "status": "MISSING_IN_COMMIT"})
                continue
            actual = hashlib.sha256(raw).hexdigest()
            if actual != expected:
                failures.append({"path": path, "status": "MISMATCH",
                                 "expected": expected, "actual": actual})
        reports.append({"head": HEAD, "manifest": name,
                        "entries": len(content.splitlines()), "failures": failures})
    output = {"purpose": "Read-only triage; no changes to the r2 branch",
              "hash_of": "committed Git blob bytes", "reports": reports,
              "decision": "HOLD" if any(r["failures"] for r in reports) else "HASHES_PASS_ONLY"}
    print(json.dumps(output, indent=2))
    return 1 if output["decision"] == "HOLD" else 0


if __name__ == "__main__":
    raise SystemExit(main())
