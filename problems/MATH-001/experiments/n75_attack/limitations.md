# n=75 attack bench — limitations and open engineering (DeepSeek r1)

## 1. Nothing here is a result about D(75)

- `D(75) = 150` is **not** claimed: the `rot2` instance was generated and hashed,
  never handed to a solver in this round.
- `D(75) < 150` is **not** claimed and cannot be claimed from anything here. That
  would need an UNSAT over the *unrestricted* formulation plus a checked proof.
- No UNSAT produced by this bench is a theorem. **No DRAT/LRAT trace was
  generated.** Solver `UNSAT` without a checkable trace is residue, and this bench
  labels it that way. (`wustep/maths` reached the same conclusion about its own
  restricted UNSAT runs; this bench inherits the standard, not a weaker one.)

## 2. Why n=75 was not attempted with the solver

The `rot2` instance is 1,648,125 variables / 36,418,316 clauses / 695 MB on disk.
For scale, the prior-art canonical-rct4 instance (996,434 vars / 2,398,895 clauses)
already returned UNKNOWN on a full run and needed ~500 s to refute only a
*restricted slice*. The `rot2` instance is ~15× the clauses, is a strictly weaker
restriction (so a larger search space), and there is no reason to expect a
different outcome inside a single work session. Spending the session on a run whose
only reportable outcomes are `UNKNOWN` or uncertified residue would be worse
evidence than the measurements recorded here. Status: `COMPUTE_REQUIRED`.

## 3. Formulation A is not buildable as stated for n=75

`estimated_clauses` for the cell formulation at n=75 is ~15.5 × 10⁶ by the
hybrid-cost model in `benchmark.py`, and the *measured* orbit instance came out at
36.4 × 10⁶ clauses — i.e. the estimate in `benchmark.py` is optimistic by ~2.4×.
The gap is because the orbit formulation's line constraints are encoded with the
enumerative `C(m,3)` path for medium-length lines, not the network path the
estimate assumed. Both numbers are recorded; the estimate should not be quoted
without the measured value beside it.

Making the cell formulation genuinely tractable for n=75 needs, at minimum:
- a real weighted-at-most-2 network for lines (the current weighted encoding is
  enumerative), and
- a Cardinality Network (not sequential counter) for the size equality, or a
  native solver pseudo-Boolean constraint.
Neither is implemented here. Both are engineering, not mathematics.

## 4. The `rot2` restriction is a restricted search, and the bench says so

A `rot2`-invariant certificate would settle `D(75) = 150`, but:
- `rot2` UNSAT at n=75 proves only "no 180°-symmetric 150-set exists".
- The centre cell is forced empty (150 is even and the centre is a fixed orbit of
  size 1), so the search covers 2812 two-orbits, exactly 75 selected.
- Every certificate without 180° symmetry is outside the model entirely.

## 5. The `lex_break` symmetry breaking is proven sound, not proven tight

`formulation.md` §5 proves `S ≤_lex Sᵀ` deletes no `D4`-orbit, so it cannot make a
satisfiable existence question unsatisfiable. It is *not* a canonical form: several
members of one orbit may remain. It is therefore recorded as **sound but weak**,
never as "symmetry breaking" in the sense of a full lex-leader scheme. It is also
**untested above n=7**; only the small-n calibration exercises it.

## 6. UNSAT controls: what they do and do not establish

- "≤1 per row with 2n points forced is UNSAT" is provable by hand (a row is a line).
- `rot4` and `full` at n=75 are excluded by orbit counting, which is a *finite
  counting* argument and is checkable by hand from the orbit multisets in
  `benchmark.json`.
- Neither of these is a statement about `D(75)`.

## 7. Dependency and provenance notes

- Solver: CaDiCaL 1.9.x and Glucose via `python-sat` (`pysat`), already present in
  the environment. **No package was installed by this round.** `pysat.pb` is
  *unavailable* (missing `pypblib` backend) and is deliberately not used.
- Cardinality networks come from `pysat.card` (pure Python, part of `python-sat`).
  This is a third-party component inside the encoder; it is used only for
  cardinality equalities, and the line-coverage audit in `encoder.py` checks the
  geometry independently of it.
- The 695 MB `rot2` DIMACS is **not** committed; only its SHA-256
  `2b47bce655ec925d9cdb91d689461a995c1d0d2c83e1f4430f68b1490f1569da` and the
  generator. Reproduce with
  `python encoder.py --n 75 --formulation orbits --group rot2 --out rot2_n75.cnf`
  and compare the hash.
- Flammenkamp data files are third-party. This round re-downloaded them from source
  rather than copying a sibling branch, and recorded SHA-256 for each. The 23.8 MB
  `all_known_solutions` is **not** committed; the fetch URL and hash are. See the
  packaging discussion in the PR review.

## 8. Uncovered work, listed so it is not mistaken for done

- No rct4 formulation was built (deliberately: the prior art already has one, and
  the point of this bench was to be independent of it).
- No local-search / MCTS arm was implemented, despite being listed as an option in
  the task. Only the two Boolean formulations exist.
- No attempt at n=77 or beyond, and no attempt to extrapolate the n=75 status.

## 9. The compute phase is blocked at G4 — an UNSAT here cannot be certified

`COMPUTE_PHASE_PROTOCOL.md` freezes the contract for the round that takes n=75 into a
compute phase. Its precondition **G4** ("an UNSAT-certifying pipeline must exist") was
tested in advance by `drat_roundtrip_test.py`, and it **fails**. Three independent
blockers, each reproduced:

| # | blocker | reproduction |
|---|---|---|
| G4.1 | PySAT's CaDiCaL emits learned clauses and deletions but the retrieved trace **contains no empty clause**, so the proof never closes | `PHP(7,6)`: 1,932 lines, 980 additions verified RUP, 952 deletions, **0 empty-clause lines** (`small_n_tests/drat_roundtrip.json`) |
| G4.2 | **Kissat refuses proof logging** in PySAT | `NotImplementedError: Proof logging is not supported by Kissat in PySAT` |
| G4.3 | **No independent DRAT/LRAT checker** exists here | `drat-trim`, `cake_lpr`, `gratgen` absent; the checker in `drat_roundtrip_test.py` is this round's own RUP-only code and does not implement RAT |

**Consequence, stated in the strongest available terms: any UNSAT produced at n=75 in
this environment must be recorded as `COMPUTE_RESULT_UNVERIFIED` and must not be
presented as a result.** This is not a formality — it is the same standard that
`wustep/maths` applied to its own restricted UNSAT runs (no trace ⇒ residue), and it
applies to this bench's own output.

To lift G4: invoke a standalone proof-capable solver directly (CaDiCaL or Kissat with
`--proof` / `--lrat`, not through PySAT's wrapper), add `drat-trim` or `cake_lpr`, and
re-run `drat_roundtrip_test.py` until it reports `SOLVED_WITH_CHECKED_PROOF`.

Also worth recording as a side effect: **every UNSAT instance this encoder produces at
small n is refuted at the root by unit propagation alone**, so CaDiCaL emits no
learned clauses at all for them. They are valid UNSAT controls (the contradiction is
provable by hand), but they cannot exercise a proof pipeline. A compute round should
therefore expect the n=75 trace — if a trace appears at all — to come from genuine
search, and should not be surprised by an empty trace on the easy controls.

