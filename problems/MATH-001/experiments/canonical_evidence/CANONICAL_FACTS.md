# MATH-001 — canonical evidence

This branch is the **canonical merge unit for MATH-001 evidence**. It carries only facts that
are supported by committed evidence in this same tree, each with a path a reader can follow.
It deliberately excludes the compute-phase plumbing; see "What is not here" at the end.

**Nothing in this branch claims a resolution of MATH-001.** No `D(75)` result is claimed in
either direction, no UNSAT certificate exists, and the general conjecture is untouched.

Commands are reproducible from this directory unless stated otherwise. Third-party corpora are
not committed; fetch and hash-check them first with
`provenance/fetch_third_party.py` (see `provenance/THIRD_PARTY_SOURCES.md` for the licence
audit — the Flammenkamp pages carry **no licence**, so raw bytes are fetched, never vendored).

---

## C1 — A third, independent certificate verifier exists and is validated

**Claim.** Legality of a `D(n)=2n` certificate is decided by a criterion *different* from the
one used by the FrontierMath r1 verifiers: map every unordered pair to its canonical
gcd-primitive, sign-normalised integer line `(A,B,C)`; a set is legal **iff** that map is
injective.

**Where the criterion is derived and proved:** `verifier/DERIVATION.md` §3 (theorem with proof),
§2 (the `D(n) ≤ 2n` row-pigeonhole bound, derived rather than assumed), §5 (the nine convention
traps: 1-indexing, row/column orientation, the `'a' → 36` lowercase mapping, the symmetry-class
prefix, duplicate entries, 4-collinear, count vs `n`, the `n=1` boundary, float coordinates).

**Evidence:** `evidence/adversarial_summary.json` — 429 cases, 0 problems, both verdict
directions exercised, and an oracle that shares no code with the checker (it re-decides
collinearity by two further arithmetic paths and raises on self-disagreement). The suite also
found two defects in this verifier's own code, which are fixed and recorded in that JSON.

**Reproduce** (executed from this tree):
```bash
cd verifier && python adversarial_suite.py --fuzz-rounds 300 --json /tmp/adv.json
#   -> suite_ok True, cases 228, problems 0   (600 rounds gives 429 cases, also 0 problems)
```

## C2 — Exact small-`n` ground truth, by two independent methods

**Claim.** `D(1)=1`, `D(2)=4`, `D(3)=6`, `D(4)=8` by **full powerset enumeration**, which does
not use the `2n` row bound at all; and, by exhaustive row-pair enumeration for `n = 2..8`, the
number of legal `2n`-sets is `1, 2, 11, 32, 50, 132, 380`.

**Cross-checks.** The two methods agree on the count of maximum legal sets for every
overlapping `n ≥ 2` (1, 2, 11). Those counts also equal Flammenkamp's authoritative
`table.html` column `all` for every `n = 2..8`. `n = 1` is excluded from the count comparison
and asserted separately: the powerset finds the single maximum set `{(1,1)}` of size 1 while the
row-pair enumeration has 0 configurations there by construction (2 points do not fit in a
1-cell grid) — both correct, different objects.

**Evidence:** `evidence/small_n_ground_truth.json`.

**Reproduce** (executed from this tree):
```bash
cd verifier && python brute_force.py --powerset-max 4 --rowpair-max 6 --json /tmp/gt.json
#   -> powerset D(1..4) = {1:1, 2:4, 3:6, 4:8}
#      rowpair legal-2n counts n=2..6 = {2:1, 3:2, 4:11, 5:32, 6:50}
#      (--rowpair-max 8 additionally gives 7:132, 8:380 and takes ~250 s)
```

## C3 — The complete public database is verified, and `n=75` is its only gap

**Claim.** Flammenkamp's `all_known_solutions` contains **431,008 configurations** covering
`n = 2..76`, and **all 431,008 verify as legal `2n` configurations** (0 failures, 0 decode
errors). **`n = 75` is the only `n` in `[2,76]` with zero configurations.** The extended
alphabet agrees with the legacy `decode.c` mapping on every line with `n ≤ 62` (0 mismatches).

**Independent retrieval paths (two, agreeing).** (i) the coded corpus at
`…/no3in/download/all_known_solutions`; (ii) the live lookup endpoint
`…/cgi-bin/cgiwrap/achim/script_lookup?para=FIXED`, which renders a configuration as an ASCII
grid. For `n=75` the endpoint answers *"sorry for n=75 no configurations are known"* (database
cut date 2026-08-31).

**Record constructions verified through both paths, with identical decoded point sets:**
`n=76` (152 points, Heule's record), `n=74` (148), `n=73` (146), `n=72` (144), `n=71` (142).
All use every row and column. Per-record code hashes are in the evidence file.

**Evidence:** `evidence/all_known_solutions_verification.json`,
`evidence/record_symmetries_ge65.json`, `evidence/r1_artifact_verification.json`.

**Reproduce** (these exact commands were executed from this tree, and their outputs are the
numbers quoted above):
```bash
cd provenance && python fetch_third_party.py     # fetch + hash-verify; ends "all present and verified"
cd ../database
python verify_all_known.py --file ../provenance/dl/all_known_solutions --json /tmp/ak.json
#   -> decoded 431008, verify_pass 431008, verify_fail 0, n 2..76, n75 present False,
#      legacy_alphabet_mismatches_for_n_le_62 0
python cross_check_database.py --file ../provenance/dl/all_known_solutions        --n 76 --symm o --index 1 --json /tmp/cc.json
#   -> paths_agree True, points 152, legal True   (repeat for --n 74 o, 73 c, 72 o, 71 c)
python symmetry_probe.py --file ../provenance/dl/all_known_solutions        --n-min 65 --json /tmp/sym.json
```

**Caveat on `evidence/r1_artifact_verification.json`.** That file was produced against the r1
tree on `glm/MATH-001-baseline-r1`; its Flammenkamp-corpus portion is reproducible here with
`database/audit_r1_artifacts.py`, but its self-certificate portion requires that branch (without
it the script finds zero self-certificate files and reports an empty, vacuous pass — which is
why this branch cites the corpus result and not the self-certificate result).

## C4 — Measured symmetry classes of the published records

**Claim** (a property of the objects, measured, not read from prose): Flammenkamp's `o`
(rot4) records are invariant under the full 90° rotation group (order 4); the `c` (rct4)
records are invariant under exactly the 180° rotation (order 2). Recorded because the
nomenclature alone is ambiguous — the source's own page says the `rct4` class "is not a
symmetry class of the grid".

**Evidence:** `evidence/record_symmetries_ge65.json`.

## C5 — What is explicitly NOT claimed

- **No `D(75) = 150`.** No certificate exists in this branch for `n=75`.
- **No `D(75) < 150`.** Nothing here produces or could produce that; it would require an
  UNSAT over the unrestricted formulation together with a checkable proof.
- **No UNSAT certificate of any kind, for any `n`.** No DRAT/LRAT trace is committed here, and
  no solver UNSAT is presented as a result.
- **No resolution of MATH-001.** `n=75` is `COMPUTE_REQUIRED`; the general conjecture is open.
- The finite-frontier facts (C3) are statements about which `n` have a *known* solution and
  about a database's contents — a search-status source, not an impossibility result.

## C6 — Frontier status (with the scope separate from the fact)

`D(n) = 2n` is verified here for the individual `n` whose certificates were checked, and the
published record states solutions are known for all `n ≤ 74` and for `n = 76`, leaving `n = 75`
the smallest open case. Three scope separations that must not be blurred:

1. **finite ≠ general.** A certificate gives `D(n)=2n` for one `n`; it says nothing about other
   `n` and nothing about `∀n ≥ 2`.
2. **record ≠ coverage.** "the record is `n=76`" and "every `n ≤ 76` except 75 is covered" are
   different statements with different evidence. Both happen to hold here.
3. **search status ≠ impossibility.** The absence of an `n=75` configuration in a database is
   not a theorem that none exists.

## What is not here, and where it is

| excluded from this branch | where it lives |
|---|---|
| CNF / orbit encoders, manifest and gadget audits | `dsk/MATH-001-compute-tooling` |
| DRAT/LRAT tooling and proof-checker integration (unfinished: the environment cannot currently emit a trace that closes) | `dsk/MATH-001-compute-tooling` |
| compute-phase protocol implementation and performance work | `dsk/MATH-001-compute-tooling` |
| the in-round execution logs and JSON | `dsk/MATH-001-round-execution` |
| the exploratory tree as originally written | `dsk/MATH-001-independent-verifier-r1` (PR #5, superseded by this branch) |

The compute plumbing is excluded on purpose: it is not needed to support any claim above, it is
the part still under active review, and it should not gate a merge of the facts.

## Superseded and retracted claims

See `SUPERSEDED_CLAIMS.md`. No active document in this branch publishes a withdrawn number.
