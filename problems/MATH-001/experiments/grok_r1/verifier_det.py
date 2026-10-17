"""Exact no-three-in-line check by the integer 2x2 minor.

Three distinct points are collinear exactly when
(x2-x1)*(y3-y1) - (x3-x1)*(y2-y1) == 0.
Points are 1-based and must lie in {1,...,n}^2.
This file imports nothing from the other checker.
"""
from __future__ import annotations


def check(points, n: int) -> dict:
    reason = _shape(points, n)
    if reason:
        return _bad(n, points, reason, None)
    pts = [(int(x), int(y)) for x, y in points]
    m = len(pts)
    for i in range(m):
        x1, y1 = pts[i]
        for j in range(i + 1, m):
            x2, y2 = pts[j]
            dx, dy = x2 - x1, y2 - y1
            for k in range(j + 1, m):
                x3, y3 = pts[k]
                if dx * (y3 - y1) - (x3 - x1) * dy == 0:
                    return _bad(n, pts, "collinear", [pts[i], pts[j], pts[k]])
    return _ok(n, pts)


def certificate(points, n: int) -> dict:
    """A 2n-certificate is a no-three-in-line set of size exactly 2n."""
    base = check(points, n)
    if not base["ok"]:
        return base
    if len(points) != 2 * n:
        return _bad(n, points, f"size {len(points)} != {2 * n}", None)
    out = dict(base)
    out["is_2n_certificate"] = True
    return out


def _shape(points, n: int):
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        return "bad n"
    seen = set()
    for p in points:
        if not (isinstance(p, (tuple, list)) and len(p) == 2):
            return "bad point"
        x, y = p
        if type(x) is not int or type(y) is not int:
            return "non-integer coordinate"
        if not (1 <= x <= n and 1 <= y <= n):
            return "out of range"
        if (x, y) in seen:
            return "duplicate point"
        seen.add((x, y))
    return None


def _ok(n, pts):
    return {
        "ok": True,
        "reason": "",
        "n": n,
        "count": len(pts),
        "is_2n_certificate": len(pts) == 2 * n,
        "collinear_example": None,
        "checker": "det",
    }


def _bad(n, pts, reason, example):
    return {
        "ok": False,
        "reason": reason,
        "n": n,
        "count": len(list(pts)),
        "is_2n_certificate": False,
        "collinear_example": example,
        "checker": "det",
    }
