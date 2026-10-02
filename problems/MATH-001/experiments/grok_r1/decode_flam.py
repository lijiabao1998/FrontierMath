"""Decode Flammenkamp's published no-three-in-line codes.

The 90-character map is the table in no3in_functions.c dated 2026-07-12
(CHAR_TO_VAL, indexed by ord(c) - 32). 'a' is 36. The 1995-era TOPOS macro,
which sends 'a' to 43, is used only for even-length records with no symmetry
lead-in, matching decode() in that file.

Coordinates in the file are 0-based. to_one_based() shifts them onto {1,...,n}.
"""
from __future__ import annotations

XX = 90
# Indexed by ASCII - 32. Value 90 means unused. 'a' (index 65) is 36.
CHAR_TO_VAL = [
    XX, 68, XX, 62, 63, 64, 65, XX, 69, 70, 78, 79, 88, 81, 89, 82,
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 86, 87, 73, 77, 74, 67, 66, 10, 11,
    12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27,
    28, 29, 30, 31, 32, 33, 34, 35, 71, XX, 72, 84, 85, XX, 36, 37,
    38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53,
    54, 55, 56, 57, 58, 59, 60, 61, 75, 80, 76, 83, XX,
]
ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz#$%&@?!()[]<>{}=*+|-/~^_:;,."
SYMM = ".:/-ox+*c?"
IGN = "'"


def _assert_alphabet():
    if len(ALPHABET) != 90:
        raise RuntimeError(f"alphabet length {len(ALPHABET)}")
    if len(CHAR_TO_VAL) < 95:
        raise RuntimeError(f"char table length {len(CHAR_TO_VAL)}")
    for i, ch in enumerate(ALPHABET):
        got = CHAR_TO_VAL[ord(ch) - 32]
        if got != i:
            raise RuntimeError(f"{ch!r} maps to {got}, alphabet index {i}")
    if CHAR_TO_VAL[ord("a") - 32] != 36:
        raise RuntimeError("'a' is not 36")


_assert_alphabet()


def _old_topos(ch: str) -> int:
    o = ord(ch)
    if o < ord("@"):
        return o - ord("0")
    return o - (ord("A") - 1 - 10)


def decode_record(raw: str) -> dict:
    text = raw.split('"', 1)[0].strip()
    if not text:
        return {"ok": False, "reason": "empty"}
    # '@' is alphabet index 66 in the 2026 table. It is not a format flag.
    # The 1995 decode.c test for '@' does not apply to these records.
    nchar = len(text)
    leadin = nchar % 2 == 1 and text[0] in SYMM
    if nchar % 2 == 1 and not leadin:
        return {"ok": False, "reason": "odd length without symmetry lead-in", "head": text[:8]}
    payload = text[1:] if leadin else text
    if len(payload) % 2:
        return {"ok": False, "reason": "odd payload"}
    n = len(payload) // 2
    if n < 1 or n > 90:
        return {"ok": False, "reason": f"n {n} outside 1..90"}
    cols = [0] * n
    points = []
    use_new = leadin
    for h, ch in enumerate(payload):
        if ch == IGN:
            continue
        x = CHAR_TO_VAL[ord(ch) - 32] if use_new and 32 <= ord(ch) < 127 else (
            _old_topos(ch) if not use_new else XX
        )
        if not use_new and (ord(ch) < 32 or ord(ch) >= 127):
            x = XX
        if x == XX or x < 0:
            return {"ok": False, "reason": f"bad character {ch!r}", "n": n}
        if x >= n:
            return {"ok": False, "reason": f"column {x} >= n {n}", "n": n, "char": ch}
        y = h // 2
        cols[x] += 1
        if cols[x] > 2:
            return {"ok": False, "reason": f"column {x} has more than 2 points", "n": n}
        points.append((x, y))
    return {
        "ok": True,
        "reason": "",
        "n": n,
        "symmetry": text[0] if leadin else "",
        "points0": points,
        "leadin": leadin,
    }


def to_one_based(decoded: dict):
    return [(x + 1, y + 1) for x, y in decoded["points0"]], decoded["n"]
