"""Fail-closed gate for a reproduction report.

A full reproduction success requires every record to have been scanned, no
stop condition, and zero decode, mathematical, or checker-disagreement failures.
A non-empty `stopped` is enough. So is a failure list or a failure count.
"""
from __future__ import annotations


def _count(report: dict, key: str) -> int:
    value = report.get(key, 0)
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, (list, tuple, dict)):
        return len(value)
    return 0


def failure_reasons(report: dict) -> list[str]:
    reasons = []
    stopped = report.get("stopped") or ""
    if stopped != "":
        reasons.append(f"stopped:{stopped}")
    if _count(report, "decode_fail") or _count(report, "decode_fail_count"):
        reasons.append("decode_fail")
    if _count(report, "math_fail") or _count(report, "math_fail_count"):
        reasons.append("math_fail")
    if _count(report, "disagree") or _count(report, "disagree_count"):
        reasons.append("disagree")
    if report.get("eof") is not True:
        reasons.append("incomplete")
    scanned = report.get("scanned")
    expected = report.get("record_count")
    if expected is not None and scanned != expected:
        reasons.append("count_mismatch")
    return reasons


def reproduction_ok(report: dict) -> bool:
    return not failure_reasons(report)
