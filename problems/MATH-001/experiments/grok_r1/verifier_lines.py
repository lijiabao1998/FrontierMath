"""Exact no-three-in-line check by canonical line keys.

A line through two grid points is the reduced direction (dx, dy),
sign-normalised, together with the invariant dx*y - dy*x.
Any key that collects three or more distinct points is a collinear triple.
No 2x2 minor is computed here, and this file does not import the other checker.
Points are 1-based and must lie in {1,...,n}^2.
"""
from __future__ import annotations
from math import gcd


def check(points, n: int) -> dict:
    reason = _shape(points, n)
    if reason:
        return _bad(n, points, reason, None)
    pts = [(int(x), int(y)) for x, y in points]
    bags: dict = {}
    m = len(pts)
    for i in range(m):
        x1, y1 = pts[i]
        for j in range(i + 1, m):
            x2, y2 = pts[j]
            dx, dy = x2 - x1, y2 - y1
            g = gcd(dx, dy)
            dx //= g
            dy //= g
            if dx < 0 or (dx == 0 and dy < 0):
                dx, dy = -dx, -dy
            key = (dx, dy, dx * y1 - dy * x1)
            bag = bags.get(key)
            if bag is None:
                bag = {pts[i], pts[j]}
                bags[key] = bag
            else:
                bag.add(pts[i])
                bag.add(pts[j])
                if len(bag) >= 3:
                    example = sorted(bag)[:3]
                    return _bad(n, pts, "collinear", example)
    return _ok(n, pts)


def certificate(points, n: int) -> dict:
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
        "checker": "lines",
    }


def _bad(n, pts, reason, example):
    return {
        "ok": False,
        "reason": reason,
        "n": n,
        "count": len(list(pts)),
        "is_2n_certificate": False,
        "collinear_example": example,
        "checker": "lines",
    }
