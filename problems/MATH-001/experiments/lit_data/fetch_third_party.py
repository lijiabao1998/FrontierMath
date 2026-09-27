#!/usr/bin/env python3
"""Fetch and hash-verify the third-party sources used by the MATH-001 work.

None of these files are tracked by git: the Flammenkamp pages carry no licence or
redistribution grant (see THIRD_PARTY_SOURCES.md for the audit), so they are fetched
on demand instead of vendored. This script is what makes that safe -- it reproduces
every input the committed code needs, and verifies each byte against the SHA-256
recorded on 2026-09-28.

Usage:
    python fetch_third_party.py                # fetch all, verify all
    python fetch_third_party.py --check        # verify what is already on disk, no network
    python fetch_third_party.py --skip-corpus  # small files only (skips the 23.8 MB DB)
    python fetch_third_party.py --allow-unhashed  # fetch files with no recorded hash and print it

Exit code 0 when everything present verifies, 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import ssl
import sys
import time
import urllib.request
from typing import Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "https://wwwhomes.uni-bielefeld.de/achim/no3in/"

# local path (relative to this file) -> (url, bytes, sha256 or None)
SOURCES: dict[str, tuple[str, int | None, str | None]] = {
    "decode.c": (BASE + "decode.c", 2324,
                 "4ef26ee8adda3543e19ce5ab75383b33f80365e3a013bbcac64fa9dbff5022db"),
    "no3in_readme.html": (BASE + "readme.html", 34559,
                          "efc0b3c2ad60e00a6ba11e197e7e1e929d833a9222f59ef20d6eb75b9e259156"),
    "known_solutions_1997.txt": (BASE + "data_1997/known_solutions", 1654852,
                                 "5e127d7be1c060a4d9021356b14848661fac8b76efee45c79acba5b7b7cd80f4"),
    "dl/all_known_solutions": (BASE + "download/all_known_solutions", 23834242,
                               "c27f8f53286be5b047a46bf1e469985e44efd4e6955783e8d0fb5ad66b7effde"),
    "t_table.html": (BASE + "table.html", 9396,
                     "6fd563d23b1bc5064bd9ae4bf8a3933c5f153b7c3b32a622c4652b2a19d04ff4"),
    "r_encoding": (BASE + "encoding", 734,
                   "8c576ef0e894f098ae62aa8d0e679e703e261ea5104edf96b59549b4508bdebb"),
    "r_new_results.html": (BASE + "new_results.html", 2118,
                           "c2707340016b2054ab34889ab9db986cd78324a506f5e652b0eac47b17d5de19"),
    "r_odd_results.html": (BASE + "odd_results.html", 2278,
                           "e11aafdf6379633891e26a3d44d50f99a8ee6af83334671c357a281ed8146270"),
    "records/rot4_72.png": (BASE + "rot4_72.png", 7682,
                            "536c821f8ccb8036ab61e0f616982fa5d8de75c26429238c9debc89f147c57dc"),
    "records/rot4_74.png": (BASE + "rot4_74.png", 8088,
                            "1205b4f6b6108346d322454dd75f209959eb2109beaff1c4dce4b00ae1ba716a"),
    "records/rot4_76.png": (BASE + "rot4_76.png", 8029,
                            "8e2ff7df5a9915a95e635e62d62fc14e2894542ca30f484bc0ff4e9efd3aac5e"),
}

SMALL_ONLY_SKIP = {"dl/all_known_solutions"}

# The text pages are third-party prose/graphics kept only for provenance; the two
# files the committed code actually reads are known_solutions_1997.txt (audit) and
# dl/all_known_solutions (full verification). Everything else is evidence of the
# retrieval, not an input.
CODE_INPUTS = {"known_solutions_1997.txt", "dl/all_known_solutions"}


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: str, expect_bytes: int | None, retries: int = 6) -> bool:
    """Download with resume + retries; the upstream host is intermittently flaky."""
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    part = dest + ".part"
    for attempt in range(1, retries + 1):
        have = os.path.getsize(part) if os.path.exists(part) else 0
        if expect_bytes is not None and have == expect_bytes:
            break
        req = urllib.request.Request(url)
        if have:
            req.add_header("Range", f"bytes={have}-")
        try:
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=120, context=ctx) as resp:
                mode = "ab" if (have and resp.status == 206) else "wb"
                if mode == "wb":
                    have = 0
                with open(part, mode) as out:
                    while True:
                        chunk = resp.read(1 << 20)
                        if not chunk:
                            break
                        out.write(chunk)
        except Exception as exc:  # noqa: BLE001
            print(f"    attempt {attempt}/{retries} failed: {type(exc).__name__}: {exc}", file=sys.stderr)
            time.sleep(2 * attempt)
            continue
        got = os.path.getsize(part)
        if expect_bytes is None or got == expect_bytes:
            break
        print(f"    attempt {attempt}/{retries}: have {got}/{expect_bytes} bytes, resuming", file=sys.stderr)
    if os.path.exists(part):
        os.replace(part, dest)
    return os.path.exists(dest)


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify on-disk files only")
    ap.add_argument("--skip-corpus", action="store_true", help="skip the 23.8 MB database")
    ap.add_argument("--allow-unhashed", action="store_true")
    ap.add_argument("--code-inputs-only", action="store_true",
                    help="fetch only the two files the committed code reads")
    args = ap.parse_args(list(argv) if argv is not None else None)

    selected = {
        rel: spec for rel, spec in SOURCES.items()
        if not (args.skip_corpus and rel in SMALL_ONLY_SKIP)
        and not (args.code_inputs_only and rel not in CODE_INPUTS)
    }

    ok = True
    for rel, (url, nbytes, digest) in selected.items():
        path = os.path.join(HERE, rel)
        if args.check or (os.path.exists(path) and digest):
            if not os.path.exists(path):
                print(f"MISSING  {rel}")
                if not args.check:
                    ok = False
                continue
            got = sha256_of(path)
            size = os.path.getsize(path)
            size_ok = nbytes is None or size == nbytes
            hash_ok = digest is None or got == digest
            status = "OK      " if (size_ok and hash_ok) else "MISMATCH"
            if not (size_ok and hash_ok):
                ok = False
            print(f"{status} {rel}  {size} bytes  {got[:32]}...")
            continue

        if args.check:
            print(f"MISSING  {rel}")
            ok = False
            continue

        print(f"fetching {rel}  ({nbytes if nbytes else '?'} bytes)  <- {url}")
        if not download(url, path, nbytes):
            print(f"FAILED   {rel}")
            ok = False
            continue
        got = sha256_of(path)
        size = os.path.getsize(path)
        if digest is None:
            print(f"FETCHED  {rel}  {size} bytes  sha256={got}")
            if not args.allow_unhashed:
                print("         (no hash was recorded in advance; printed above for review)")
        elif got != digest:
            print(f"MISMATCH {rel}\n  expected {digest}\n  got      {got}")
            ok = False
        else:
            print(f"OK       {rel}  {size} bytes  sha256 verified")

    print("\nRESULT:", "all present and verified" if ok else "PROBLEMS FOUND (see above)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
