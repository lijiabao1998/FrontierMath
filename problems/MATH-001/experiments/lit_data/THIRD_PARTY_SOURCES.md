# Third-party sources — licence status and fetch instructions

This directory's practice is **URL + SHA-256 + fetch script instead of vendoring**.
Raw third-party files are deliberately not tracked by git either here or on
`dsk/MATH-001-independent-verifier-r1`.

## Licence audit (performed 2026-09-28)

| source | licence found? | where checked | decision |
|---|---|---|---|
| Flammenkamp no-three-in-line pages (`wwwhomes.uni-bielefeld.de/achim/no3in/`) | **NO.** The readme contains no licence, copyright, or redistribution statement. Its only related phrase is "The algorithm … are downloadable for free", which describes availability of a C program, not a redistribution grant. | full-text search of `readme.html` for `licen[cs]`, `copyright`, `©`, `reproduc`, `redistribut`, `permission`, `free of charge` | **do not vendor.** Files below are fetched on demand and hash-verified. |
| `wustep/maths` (prior-art attack log) | **YES — MIT**, "Copyright (c) 2026 Stephen Wu" (`gh api repos/wustep/maths/license` → `spdx_id: MIT`) | GitHub licence API | **may be redistributed with the notice.** `../prior_art/` keeps the two quoted logs and carries the required MIT attribution in `../prior_art/ATTRIBUTION.md`. |

No licence statement was found for the Flammenkamp material in the fetched pages.
"Publicly downloadable" is not a redistribution grant, so the conservative reading is
applied until the owner or upstream says otherwise.

## Fetch + verify

```bash
python fetch_third_party.py            # fetch everything, verify every hash
python fetch_third_party.py --check    # verify files already on disk, no network
python fetch_third_party.py --skip-corpus   # small files only (skips the 23.8 MB database)
```

Anything downloaded lands in this directory (and `dl/`, `records/`) and is
`.gitignore`d. Hashes are of the **upstream bytes**.

| file | URL | bytes | SHA-256 |
|---|---|---|---|
| `decode.c` | https://wwwhomes.uni-bielefeld.de/achim/no3in/decode.c | 2,324 | `4ef26ee8adda3543e19ce5ab75383b33f80365e3a013bbcac64fa9dbff5022db` |
| `no3in_readme.html` | https://wwwhomes.uni-bielefeld.de/achim/no3in/readme.html | 34,559 | `efc0b3c2ad60e00a6ba11e197e7e1e929d833a9222f59ef20d6eb75b9e259156` |
| `known_solutions_1997.txt` | https://wwwhomes.uni-bielefeld.de/achim/no3in/data_1997/known_solutions | 1,654,852 | `5e127d7be1c060a4d9021356b14848661fac8b76efee45c79acba5b7b7cd80f4` |
| `dl/all_known_solutions` | https://wwwhomes.uni-bielefeld.de/achim/no3in/download/all_known_solutions | 23,834,242 | `c27f8f53286be5b047a46bf1e469985e44efd4e6955783e8d0fb5ad66b7effde` |
| `t_table.html` | https://wwwhomes.uni-bielefeld.de/achim/no3in/table.html | 9,396 | `6fd563d23b1bc5064bd9ae4bf8a3933c5f153b7c3b32a622c4652b2a19d04ff4` |
| `r_encoding` | https://wwwhomes.uni-bielefeld.de/achim/no3in/encoding | 734 | `8c576ef0e894f098ae62aa8d0e679e703e261ea5104edf96b59549b4508bdebb` |
| `r_new_results.html` | https://wwwhomes.uni-bielefeld.de/achim/no3in/new_results.html | 2,118 | `c2707340016b2054ab34889ab9db986cd78324a506f5e652b0eac47b17d5de19` |
| `r_odd_results.html` | https://wwwhomes.uni-bielefeld.de/achim/no3in/odd_results.html | 2,278 | `e11aafdf6379633891e26a3d44d50f99a8ee6af83334671c357a281ed8146270` |
| `records/rot4_72.png` | https://wwwhomes.uni-bielefeld.de/achim/no3in/rot4_72.png | 7,682 | `536c821f8ccb8036ab61e0f616982fa5d8de75c26429238c9debc89f147c57dc` |
| `records/rot4_74.png` | https://wwwhomes.uni-bielefeld.de/achim/no3in/rot4_74.png | 8,088 | `1205b4f6b6108346d322454dd75f209959eb2109beaff1c4dce4b00ae1ba716a` |
| `records/rot4_76.png` | https://wwwhomes.uni-bielefeld.de/achim/no3in/rot4_76.png | 8,029 | `8e2ff7df5a9915a95e635e62d62fc14e2894542ca30f484bc0ff4e9efd3aac5e` |

**Scope of these hashes.** They are the SHA-256 of the bytes **this round downloaded on
2026-09-28**, and they are recorded *after* the fact — they are not a pre-registered
upstream commitment. For `all_known_solutions` the stronger integrity evidence is the
**content** check this round actually performed: 431,008 lines decode, every one
verifies as a legal 2n configuration, and the per-`n` counts reconcile with
`table.html`. That result is in
`../independent_verifier_r1/small_n_tests/all_known_solutions_verification.json`.
`fetch_third_party.py --check` compares a re-fetch against the table above, so tampering
with the upstream file after 2026-09-28 would be detectable.

## What is *not* redistributed, and why it does not weaken reproducibility

Removing the raw bytes loses nothing that matters, because every conclusion this round
drew from them is either (a) reproduced by committed code from a fetched file, or
(b) already stated with attribution in this branch's own documents:

- the frontier status and the `n=75` gap → asserted from `readme.html`, `table.html`
  and the database itself, and re-derivable in one command by the fetch script;
- the lowercase-alphabet bug analysis → derived from `decode.c`'s `TOPOS` macro, whose
  relevant lines are quoted in
  `../independent_verifier_r1/DERIVATION.md` §5 (trap T3);
- the record constructions → decodable from the database or the live lookup endpoint,
  and the decoded point sets are hash-recorded in
  `../independent_verifier_r1/small_n_tests/`.
