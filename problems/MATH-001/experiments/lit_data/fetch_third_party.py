#!/usr/bin/env python3
"""Fetch and hash-verify the third-party sources used by the MATH-001 work.

None of these files are tracked by git: the Flammenkamp pages carry no licence or
redistribution grant (see THIRD_PARTY_SOURCES.md for the audit), so they are fetched
on demand instead of vendored. This script is what makes that safe -- it reproduces
every input the committed code needs, and verifies each byte against the SHA-256
recorded on 2026-09-28.

FAIL-CLOSED CONTRACT (this is the whole point of the script):
  For every selected, REQUIRED source, each of
      * file missing
      * size mismatch
      * hash mismatch
      * download failure
  is a verification failure. Any such failure makes the process exit non-zero. The
  success line is printed ONLY when run() returned ok, so a `--check` run can never
  certify provenance it did not observe.

Usage:
    python fetch_third_party.py                # fetch all, verify all
    python fetch_third_party.py --check        # verify what is already on disk, no network
    python fetch_third_party.py --skip-corpus  # small files only (skips the 23.8 MB DB)
    python fetch_third_party.py --code-inputs-only
    python fetch_third_party.py --root DIR     # treat DIR as the origin of every path
    python fetch_third_party.py --sources-json F   # replace the built-in table (testing hook)

Exit code 0 only when every selected required source is present, correctly sized and
hash-verified (or, for entries with no recorded hash, fetched and reported).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import ssl
import sys
import time
import urllib.request
from typing import Callable, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "https://wwwhomes.uni-bielefeld.de/achim/no3in/"

# local path (relative to the root) -> (url, bytes, sha256 or None)
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

SKIP_WITH_SKIP_CORPUS = {"dl/all_known_solutions"}
CODE_INPUTS = {"known_solutions_1997.txt", "dl/all_known_solutions"}


def load_sources(sources_json: str | None) -> dict[str, tuple[str, int | None, str | None]]:
    if not sources_json:
        return dict(SOURCES)
    with open(sources_json, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    out: dict[str, tuple[str, int | None, str | None]] = {}
    for rel, spec in raw.items():
        if isinstance(spec, dict):
            out[rel] = (spec["url"], spec.get("bytes"), spec.get("sha256"))
        else:  # [url, bytes, sha256]
            out[rel] = (spec[0], spec[1], spec[2])
    return out


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: str, expect_bytes: int | None, retries: int = 6,
             log: Callable[[str], None] = print) -> bool:
    """Download with resume + retries. Returns True only on a complete transfer."""
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
            log(f"    attempt {attempt}/{retries} failed: {type(exc).__name__}: {exc}")
            time.sleep(2 * attempt)
            continue
        got = os.path.getsize(part)
        if expect_bytes is None or got == expect_bytes:
            break
        log(f"    attempt {attempt}/{retries}: have {got}/{expect_bytes} bytes, resuming")
    if os.path.exists(part) and (expect_bytes is None or os.path.getsize(part) == expect_bytes):
        os.replace(part, dest)
        return True
    return False


def run(sources: dict[str, tuple[str, int | None, str | None]], root: str, *,
        check: bool = False, skip_corpus: bool = False, code_inputs_only: bool = False,
        allow_unhashed: bool = False, log: Callable[[str], None] = print) -> bool:
    """Verify (and if needed fetch) `sources` under `root`. Returns True iff all good."""
    selected = {
        rel: spec for rel, spec in sources.items()
        if not (skip_corpus and rel in SKIP_WITH_SKIP_CORPUS)
        and not (code_inputs_only and rel not in CODE_INPUTS)
    }
    if not selected:
        log("FAIL: no sources selected -- refusing to report success on an empty set")
        return False

    ok = True
    for rel, (url, nbytes, digest) in selected.items():
        path = os.path.join(root, rel)

        if os.path.exists(path):
            # present on disk: always verify size and hash, in --check mode too
            got = sha256_of(path)
            size = os.path.getsize(path)
            size_ok = nbytes is None or size == nbytes
            hash_ok = digest is None or got == digest
            if size_ok and hash_ok:
                log(f"OK       {rel}  {size} bytes  {got[:32]}...")
            else:
                ok = False
                if not size_ok:
                    log(f"MISMATCH {rel}  size {size} != expected {nbytes}")
                if not hash_ok:
                    log(f"MISMATCH {rel}\n  expected {digest}\n  got      {got}")
            continue

        # absent
        if check:
            ok = False
            log(f"MISSING  {rel}  (expected {nbytes if nbytes else '?'} bytes; "
                f"--check performs no download)")
            continue

        log(f"fetching {rel}  ({nbytes if nbytes else '?'} bytes)  <- {url}")
        if not download(url, path, nbytes, log=log):
            ok = False
            log(f"FAILED   {rel}  download incomplete")
            continue
        got = sha256_of(path)
        size = os.path.getsize(path)
        if digest is None:
            log(f"FETCHED  {rel}  {size} bytes  sha256={got}")
            if not allow_unhashed:
                log("         (no hash recorded in advance; printed above for review)")
        elif got != digest:
            ok = False
            log(f"MISMATCH {rel}\n  expected {digest}\n  got      {got}")
        else:
            log(f"OK       {rel}  {size} bytes  sha256 verified")

    return ok


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify on-disk files only")
    ap.add_argument("--skip-corpus", action="store_true", help="skip the 23.8 MB database")
    ap.add_argument("--allow-unhashed", action="store_true")
    ap.add_argument("--code-inputs-only", action="store_true",
                    help="only the two files the committed code reads")
    ap.add_argument("--root", default=HERE, help="root the relative paths are resolved against")
    ap.add_argument("--sources-json", default=None,
                    help="replace the built-in source table (testing hook)")
    args = ap.parse_args(list(argv) if argv is not None else None)

    sources = load_sources(args.sources_json)
    ok = run(sources, args.root, check=args.check, skip_corpus=args.skip_corpus,
             code_inputs_only=args.code_inputs_only, allow_unhashed=args.allow_unhashed)

    # The success banner is printed ONLY when the run actually succeeded. There is no
    # code path that prints it after a MISSING / MISMATCH / FAILED.
    if ok:
        print("\nRESULT: all present and verified")
        return 0
    print("\nRESULT: PROBLEMS FOUND (see above)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
