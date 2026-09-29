#!/usr/bin/env python3
"""MATH-001 exact verifier (implementation v1, brute-force triples).

Checks a no-three-in-line certificate with pure integer arithmetic:
  - grid range {1..n}^2, points distinct, exactly `target` points (default 2n)
  - every 3-point subset has non-zero integer determinant (no collinear triple)

Exit code 0 = PASS, 1 = FAIL, 2 = usage/IO error. PASS lines print "PASS";
any violation prints "FAIL: <reason>" to stderr. Stdlib only.

Certificate JSON schema:
  {"n": int, "points": [[x, y], ...], "target": int (optional, default 2n),
   "source": str, "origin_ref": str, "generated": str}
"""
from __future__ import annotations
import itertools
import json
import sys
from pathlib import Path


def load_cert(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise ValueError("certificate must be a JSON object")
    return obj


def verify(cert: dict) -> list[str]:
    """Return list of violation strings; empty list means PASS."""
    errors: list[str] = []
    n = cert.get("n")
    points = cert.get("points")
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        return [f"invalid n: {n!r}"]
    if not isinstance(points, list) or not points:
        return ["missing or empty points"]
    target = cert.get("target", 2 * n)
    if not isinstance(target, int) or target < 1:
        return [f"invalid target: {target!r}"]
    if len(points) != target:
        errors.append(f"point count {len(points)} != target {target}")
    seen = set()
    norm: list[tuple[int, int]] = []
    for p in points:
        if not (isinstance(p, list) and len(p) == 2):
            errors.append(f"malformed point: {p!r}")
            continue
        x, y = p[0], p[1]
        if not (isinstance(x, int) and not isinstance(x, bool)
                and isinstance(y, int) and not isinstance(y, bool)):
            errors.append(f"non-integer coordinates: {p!r}")
            continue
        if not (1 <= x <= n and 1 <= y <= n):
            errors.append(f"out of grid {n}x{n}: ({x},{y})")
            continue
        if (x, y) in seen:
            errors.append(f"duplicate point: ({x},{y})")
        seen.add((x, y))
        norm.append((x, y))
    if errors:
        return errors
    # brute force over all triples: 2*(y2-y1) etc. -> integer determinant
    for (x1, y1), (x2, y2), (x3, y3) in itertools.combinations(norm, 3):
        det = x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)
        if det == 0:
            errors.append(f"collinear triple: ({x1},{y1}),({x2},{y2}),({x3},{y3})")
            if len(errors) >= 5:
                errors.append("... further violations suppressed")
                break
    return errors


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: verifier.py <cert.json> [cert2.json ...]", file=sys.stderr)
        return 2
    rc = 0
    for arg in argv[1:]:
        path = Path(arg)
        try:
            cert = load_cert(path)
            errors = verify(cert)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"FAIL {path}: unreadable certificate: {exc}", file=sys.stderr)
            rc = 1
            continue
        n = cert.get("n")
        if errors:
            print(f"FAIL {path.name} (n={n}): {errors[0]}", file=sys.stderr)
            rc = 1
        else:
            print(f"PASS {path.name} (n={n}, {len(cert['points'])} points, "
                  f"source={cert.get('source', 'unknown')})")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
