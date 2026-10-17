"""Deterministic search for one 2n-point no-three-in-line set.

A 2n-point subset of {1,...,n}^2 has exactly two points in every row and every
column. The search places those two columns row by row. It is existence search,
not an enumeration, and a timeout is not a proof that no solution exists.
No random seed is used.
"""
from __future__ import annotations
import time


def search_one(n: int, node_limit: int, seconds: float):
    cols = [0] * (n + 1)
    pts = []
    nodes = 0
    deadline = time.monotonic() + seconds
    status = "not_found"
    found = None

    def hits(x, y):
        m = len(pts)
        for i in range(m):
            x1, y1 = pts[i]
            dx, dy = x - x1, y - y1
            for j in range(i + 1, m):
                x2, y2 = pts[j]
                if dx * (y2 - y1) - (x2 - x1) * dy == 0:
                    return True
        return False

    def feasible(row):
        rows_left = n - row + 1
        for c in range(1, n + 1):
            if 2 - cols[c] > rows_left:
                return False
        return True

    def rec(row):
        nonlocal nodes, status, found
        if found is not None:
            return
        nodes += 1
        if nodes > node_limit:
            status = "node_limit"
            return
        if (nodes & 4095) == 0 and time.monotonic() > deadline:
            status = "time_limit"
            return
        if row == n + 1:
            found = list(pts)
            status = "found"
            return
        if not feasible(row):
            return
        for c1 in range(1, n + 1):
            if cols[c1] >= 2 or hits(c1, row):
                continue
            cols[c1] += 1
            pts.append((c1, row))
            for c2 in range(c1 + 1, n + 1):
                if status != "not_found" and found is None:
                    break
                if cols[c2] >= 2 or hits(c2, row):
                    continue
                cols[c2] += 1
                pts.append((c2, row))
                rec(row + 1)
                pts.pop()
                cols[c2] -= 1
                if found is not None:
                    break
            pts.pop()
            cols[c1] -= 1
            if found is not None or status != "not_found":
                return

    rec(1)
    return {
        "n": n,
        "status": status if found is None else "found",
        "nodes": nodes,
        "seconds": round(time.monotonic() - (deadline - seconds), 6),
        "points": found,
    }
