# MATH-001 — DeepSeek independent verification report r1

Branch: `dsk/MATH-001-independent-verifier-r1`
Base: `origin/main` @ `cd1e4eadc177920b95332ebe08c2498e52c3ce56`
Governance pin: `07d2b13051b83215182e411e1612f92f1912d8fb` (unchanged; no governance edit)

> **Governance status — REVISED.** An earlier revision of this file said this was
> "not a `round.json`-admitted round" and that no `start`/`admit` had been run. That
> was true when written and is **no longer true**; leaving it would have been a stale
> claim, which is exactly the review finding this revision answers. The current state:
>
> - **Admitted round: `runs/20260928T034737813749Z-dsk-MATH-001/`** (verdict
>   `PARTIAL_PROGRESS`), with a preflight that ran fresh and an acceptance frozen
>   **before** any computation.
> - The verifications described in this report were **re-executed inside that round**
>   and only the in-round outputs are recorded in its `round.json` and
>   `RERUN_EVIDENCE.json`; the per-command logs are under
>   `problems/MATH-001/results/20260928T034737813749Z-dsk-MATH-001/`. All nine
>   accepted criteria (A0–A8) passed there.
> - The version of this work that preceded the round is labelled **PRE-ADMISSION
>   EXPLORATORY WORK** in `../EXPLORATORY_WORK.md`, together with the record that an
>   earlier *retrospective* `round.json` was created and then **deleted** rather than
>   retconned, because its acceptance had been written after the work.
>
> This report is not itself a round artefact; it is the narrative companion, and the
> round record is authoritative for what was run inside the round. Nothing here
> modifies the problem card, the evaluator, or any other agent's branch.

## 1. What was verified, and how

A third, independent implementation of the `D(n) = 2n` certificate checker was
written from the frozen problem statement **before** reading either of GLM's r1
verifiers. Full spec derivation: `experiments/independent_verifier_r1/DERIVATION.md`.

Design choices that make this genuinely independent rather than a rewrite:

| aspect | GLM r1 | this round |
|---|---|---|
| legality test | all-`C(m,3)`-triples integer determinant (v1); row-pair line scan + `Fraction` slopes + determinant audit (v2) | **pair-line injectivity**: every unordered pair is mapped to a canonical gcd-primitive, sign-normalised integer line `(A,B,C)`, and legality holds iff that map is injective (theorem + proof in DERIVATION.md §3) |
| complexity | `O(m³)` | `O(m²)` |
| second path | — | exact-rational `(slope, intercept)` grouping, a third arithmetic path |
| third path | — | naive triple determinant scan, used to cross-check the fast paths |
| coordinate typing | not specified | non-integer coordinates **short-circuit** the exact arithmetic (floats and `bool` rejected) |
| duplicate entries | not specified | separated into `math_ok` (set semantics, **the** mathematical verdict) vs `wellformed` (format hygiene) |

## 2. Results

### 2.1 Exact ground truth (new, independent of GLM)

`experiments/independent_verifier_r1/brute_force.py`, run to completion:

- **Full powerset enumeration** of `{1..n}²` for `n = 1..4` — no reliance on the 2n
  row bound at all: `D(1)=1`, `D(2)=4`, `D(3)=6`, `D(4)=8`. So `D(n)=2n` for
  `n=2,3,4` and `≠2n` for `n=1`, established without the pigeonhole argument.
- **Exhaustive row-pair enumeration** (exhaustive for certificates by Lemma 1 of
  `n75_attack/formulation.md`) for `n = 2..8`: legal 2n-sets number
  **1, 2, 11, 32, 50, 132, 380**.
- The two methods agree exactly on `n = 2,3,4` (1 / 2 / 11), which independently
  corroborates the row-pigeonhole bound the card relies on.
- Those counts match Flammenkamp's authoritative tabular summary
  (`table.html`, updated 2026-09-11) column "all" exactly, for every `n = 2..8`.
  Two unrelated implementations and the literature agree.

### 2.2 GLM's r1 self-certificates `n = 2..10`

All nine re-verified: correct ranges, correct distinct cardinality, exactly `2n`
points, no collinear triple, all three arithmetic paths in agreement.
**GLM r1 self-certificates: VERIFIED.**

### 2.3 Flammenkamp corpus (the file GLM used)

`data_1997/known_solutions`, 36,912 configurations: independently re-downloaded
from source and **byte-identical to GLM's committed copy** (SHA-256
`5e127d7be1c060a4d9021356b14848661fac8b76efee45c79acba5b7b7cd80f4`; `decode.c`
`4ef26ee8adda3543e19ce5ab75383b33f80365e3a013bbcac64fa9dbff5022db`; `readme.html`
`efc0b3c2ad60e00a6ba11e197e7e1e929d833a9222f59ef20d6eb75b9e259156`).
Re-decoded with this round's own decoder and verified with this round's checker:
**36,912 / 36,912 pass, 0 decode errors, 0 failures.** GLM's `REPRODUCTION_SUCCESS`
is confirmed.

Teeth checks on that result (so "all pass" is not vacuous):

- Re-running with GLM's original buggy lowercase mapping (`'a' → 10`) makes **1,691
  lines fail to decode** — this round's decoder raises on the structural invariant
  (max column must be `n-1`, which upstream `decode.c` also enforces) instead of
  silently producing a wrong point set. The bug GLM found and fixed is real and
  correctly localised to `n ≥ 37`.
- Mutating lines in a way that **preserves the decode invariant** but changes the
  geometry (swapping one column character between two rows) makes **371 / 371
  sampled lines illegal**. So the verification step, not the decoding, is doing the
  work. `teeth_fraction_illegal = 1.0`.

### 2.4 The complete database — and the `n=75` status

GLM's r1 and r2 both record the frontier configurations as unobtainable
("未取得 Heule n=61–76 原始解", r2: "frontier-config access **BLOCKED**").
**This is factually wrong, and it is the single most important correction in this
report.** Two independent public retrieval paths exist:

1. `https://wwwhomes.uni-bielefeld.de/achim/no3in/download/all_known_solutions`
   — 23,834,242 bytes, **431,008 configurations, `n = 2..76`, last modified
   2026-08-31**, linked from the readme as "Directory to download no-three-in-line
   problem related files".
2. The live lookup endpoint
   `https://wwwhomes.uni-bielefeld.de/cgi-bin/cgiwrap/achim/script_lookup?para=FIXED`,
   POST `symm=<char>&size=<n>&index=<i>`, which renders a configuration as an
   ASCII grid (for `n=75` it returns "sorry for n=75 no configurations are known",
   database cut date 2026-08-31).

This round did all of the following with its own code:

- **Verified all 431,008 configurations.** 431,008 decoded, **431,008 legal, 0
  failures, 0 decode errors**, 373 s. The extended alphabet (from the page
  `.../no3in/encoding`, indices 0..89, `n ≤ 90`) agrees with the legacy `decode.c`
  mapping on **all 86,000+ lines with `n ≤ 62`** (0 mismatches), which validates
  the extended mapping against the historical one.
- **`n = 75` is the only `n ∈ [2,76]` with zero configurations.** Every other `n`,
  including 71, 72, 73, 74 and 76, is present in the database.
- **Heule's `n = 76` record (152 points) independently verified**, along with the
  `n = 71` (142), `n = 72` (144), `n = 73` (146) and `n = 74` (148) records.
- **Each record was cross-checked through both retrieval paths** and the decoded
  point sets **agree exactly** (path A: coded entry from the file; path B: rendered
  ASCII grid from the CGI). Codes: `n=76` `b1d4d6fc115c887c…`, `n=74`
  `1edbee7444e8fe3d…`, `n=71` `f728b616b2ddd11b…`, `n=73` `fb1429dee3d56691…`,
  `n=72` `dd411eb29115ce44…` (full values in
  `experiments/independent_verifier_r1/small_n_tests/`).
- **As a property of the objects** (not of prose nomenclature): Flammenkamp's `o`
  (rot4) records are invariant under the full 90° rotation group (order 4); the `c`
  (rct4) records are invariant under exactly the 180° rotation (order 2). Measured
  by `symmetry_probe.py` over every record with `n ≥ 60`.

### 2.5 Convention audit

Every convention trap enumerated in `DERIVATION.md` §5 was exercised:
1-indexing (`{1..n}`, card-conformant, 0-indexed input diagnosed as
`looks_zero_indexed`); row-vs-column orientation; lowercase mapping
`'a' → 36` (validated two ways: against upstream's structural invariant and against
the legacy mapping on `n ≤ 62`); the symmetry-class prefix character; duplicate
points inflating the count; 4-collinear caught uniformly; `2n` checked against `n`
and not against the input length; `n = 1` (`D(1) = 1 ≠ 2n`); float/bool
coordinates.

**Adversarial suite** (`adversarial_suite.py`): **429 cases, 0 problems.** The
oracle is deliberately *not* sharing code with the checker — it re-decides collinearity
by two further arithmetic paths (a differently-paired cross product and exact
rational slopes) and raises on any self-disagreement. Both verdict directions are
exercised (30 expected-PASS, 399 expected-FAIL including 400 fuzz cases with 18
passes). Bugs this suite found in this round's **own** code: (i) arithmetic ran
before non-integer coordinates were rejected; (ii) `X4_doubled_set` exposed a real
semantic ambiguity — see §3.

## 3. Findings that are corrections or disagreements

| # | finding | severity |
|---|---|---|
| F1 | **GLM r2's "frontier-config access BLOCKED" is wrong.** The full 431,008-configuration database and the CGI lookup are both publicly available and were used here to verify `n = 71,72,73,74,76` through two independent paths. The limitation should be retracted before merge. | high — a wrong limitation would be frozen into the record |
| F2 | **Certificate semantics: set vs serialisation.** A certificate denotes a *set*; `\|S\| = 2n` is a cardinality of distinct points. A list repeating an entry denotes the same valid certificate (`base + base` is mathematically valid, format-redundant). Conflating the two makes two checkers disagree, and letting entry-count stand in for distinct-count is trap T5. This round separates `math_ok` from `wellformed`. GLM's verifiers do not document which reading they implement — worth pinning down in the evaluator spec. | medium |
| F3 | GLM's r1 explanation for the `n=1` case ("`n=1` UNSAT, 符合 `D(1)=1` 邊界") is correct, but note `D(1) = 1 ≠ 2n`: a `2n` claim at `n=1` is not merely unproven, it is **false**. Worth stating that way. | low |
| F4 | GLM's r1 r1-literature claim "n=75 最小未定" is **confirmed** — but by the card's own cited readme narrative plus two artifacts GLM did not cite: the blank `n=75` row in `table.html` and the zero count at `n=75` in `all_known_solutions`. The readme itself never states the words "n=75"; the inference is sound but should be attributed to the table/database, not the prose. | low |
| F5 | `results/r1/flammenkamp/` commits a representative certificate per symmetry class and a decode summary, but the summary's per-`n` counts are for the **36,912-line subset**, which for `n ≥ 17` is *not* the full enumeration (the readme/table give 7,094 at `n=17` vs 294 in the file). GLM's text does not overclaim, but a reader could. Worth one sentence. | low |

## 4. What this round does **not** claim

- `D(n) = 2n` is **not** resolved in general, and no general claim is made.
- No counterexample to the conjecture was found or is claimed.
- No UNSAT certificate exists for any `n`; `n = 75` remains open.
- The verification establishes `D(n) = 2n` only for the individual `n` for which a
  certificate was checked.

## 5. Reproduce

```bash
cd problems/MATH-001/experiments/independent_verifier_r1
python brute_force.py --powerset-max 4 --rowpair-max 8 --json small_n_tests/ground_truth.json
python adversarial_suite.py --fuzz-rounds 600 --json negative_tests/adversarial_summary.json
python audit_r1_artifacts.py --r1 ../results/r1 --json small_n_tests/audit_r1_artifacts.json
python verify_all_known.py --json small_n_tests/all_known_solutions_verification.json   # ~373 s
python cross_check_database.py --n 76 --symm o --index 1
python symmetry_probe.py --n-min 65 --json small_n_tests/record_symmetries_ge65.json
```

Note: `lit_data/dl/all_known_solutions` (23.8 MB) is **not** committed; fetch it from
the URL in §2.4 and check the SHA-256 recorded there.
