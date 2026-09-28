# n=75 compute-phase protocol (frozen contract)

**Status: this is a pre-registration. No compute has been run under it, and its gates
are designed to be checked before any solver time is spent.**

Written 2026-09-28 by DeepSeek (verifier role) for the round that takes n=75 into a
compute phase. It fixes, in advance: what may be claimed, what only counts as a
certificate, and which environment gaps must be closed first. Nothing here may be
relaxed after a solver returns — that is the point of freezing it now.

## 0. The one rule that governs everything

> **A timeout is not UNSAT. A solver's `s UNSAT` is not a theorem. Only an UNSAT with
> an independently checked proof trace is a theorem. A SAT answer with a checked
> witness is a theorem.**

Corollaries that must appear verbatim in the round report:
- `UNKNOWN` / timeout / externally-killed / out-of-memory → **not** UNSAT, **no**
  inference about D(75).
- `s UNSAT` with no trace, or with a trace that fails to check → `COMPUTE_RESULT_UNVERIFIED`.
- `s UNSAT` with a trace checked by an independent checker → may be reported as a
  certified exclusion **of the instance**, and only then, with its scope named.

## 1. Preconditions that must be satisfied BEFORE the solver starts

### G1 — the instance must be reproducible from a committed generator
- Frozen encoder: `encoder.py` on branch `dsk/MATH-001-independent-verifier-r1`.
- The DIMACS must be regenerated and its SHA-256 compared to the recorded value.
  The `rot2` instance measured this round: 1,648,125 vars, 36,418,316 clauses,
  SHA-256 `2b47bce655ec925d9cdb91d689461a995c1d0d2c83e1f4430f68b1490f1569da`,
  build ~140 s. It is **not** committed (695 MB); regenerate and compare.
- The DIMACS header (`p cnf V C`) must match the actual clause and variable counts.

### G2 — link (1) of certification: the formula must express the problem
Run `benchmark.py`'s CNF audit (or `encoder.audit_cnf_covers_lines`) and require
`complete: true` from `encoder.audit_cnf_covers_lines`, which means **all** of:

- **layer 1 (exact):** for every maximal line encoded with explicit triple clauses, the
  DIMACS contains **every** `C(k,3)` clause `(¬a ∨ ¬b ∨ ¬c)` over that line's triples —
  not merely at least one. (An earlier revision of this protocol accepted "at least one
  clause", which is unsound for `k > 3` and was the subject of a review finding.)
- **layer 2 (encoding-agnostic):** for every line encoded by a cardinality network, every
  3-subset `T` must make `F ∧ T` UNSAT — unit propagation first, escalating to a real SAT
  call. Lines left unchecked force `complete: false`.
- **vacuity guard, LOCAL not global:** for each line the audit takes the sub-formula of
  clauses mentioning that line's variables and requires it to be satisfiable on its own
  before using it to refute violations. An earlier version asked whether the WHOLE formula
  is satisfiable, which two reviewers correctly rejected: it marked a genuinely UNSAT target
  vacuous — exactly the outcome the compute phase investigates — and required solving the
  36M-clause instance synchronously. The local check is unaffected by clauses outside the
  line, so it is neither vacuous on a broken formula nor blind to a real contradiction.
  Without any guard an unrelated contradictory unit pair makes the semantic layer pass on a
  formula whose line constraints have been deleted; a reviewer demonstrated exactly that.

**G2 must be run on the actual target instance, not on a small-n control.** The command is:

```bash
python encoder.py --n 75 --formulation orbits --group rot2 --out rot2_n75.cnf     --gadget-manifest rot2_n75_manifest.json
python benchmark.py --audit-instance rot2_n75.cnf --n 75 --group rot2     --gadget-manifest rot2_n75_manifest.json
```

`--gadget-manifest` is **required**, not optional. The manifest records every clause the
encoder emitted, and the audit requires the instance's clause multiset to equal it exactly --
so both a MISSING clause (an underconstrained line) and an EXTRA clause (a unit that forces
variables false and could manufacture an UNSAT unrelated to the problem) are detected. Without
a manifest the audit fails closed and G2 always fails, which is why the commands above pass
one. An earlier revision of this section omitted the argument, so following the frozen
commands could never satisfy G2.

Passing `--group` is **required** for an orbit instance: it selects `audit_orbit_cnf`, which
reconstructs the orbits and the per-line weighted items from the same group the encoder used.
Without it the cell audit applies a row-major cell variable mapping to an encoding where many
cells share one variable, and reports a valid orbit formula as incomplete (a reviewer
reproduced 7 of 8 lines "missing" on an intact n=3 rot2 instance).

`benchmark.py`'s `negative_controls` only tests the *audit itself* on a deliberately broken
n=5 instance; it does not audit the n=75 formula. An earlier revision of this section told
the reader to run `benchmark.py` and could therefore have marked G2 complete without ever
checking the target formula. That is the finding this text answers.

**STATUS: G2 is NOT yet satisfied for n=75.** The audit has been executed only on small-n
instances, where it passes. Running it on the hashed `rot2` instance
(SHA-256 `2b47bce655ec925d9cdb91d689461a995c1d0d2c83e1f4430f68b1490f1569da`) is a required
pre-compute step and has not been done. Until it is, no solver run may be reported under
this protocol.

An UNSAT on a formula whose line constraints are incomplete, or which is unsatisfiable for
an unrelated reason, is worthless.

### G3 — the symmetry-breaking claim must be one of the two proved kinds
Only these two are allowed, and each must be labelled with its scope:

| device | claim it licenses | claim it does NOT license |
|---|---|---|
| **orbit restriction** (search only `G`-invariant sets, `G ≤ D4`) | `SAT` ⇒ `D(n)=2n` (the model is a real certificate) | `UNSAT` ⇒ nothing about `D(n)`; it only excludes `G`-invariant certificates. `rot4` and full-`D4` are already **excluded for n=75 by counting** (`formulation.md` §4), so `rot2` (180°) is the only rotation route left |
| **`S ≤lex Sᵀ` breaking** (`lex_break=True`) | sound for the existence question: every `D4`-orbit retains ≥1 representative (proof in `formulation.md` §5) | it is **not** a canonical form; it is sound but weak, and is untested above n=7 |

Any *other* symmetry reduction is `heuristic-only` and must be labelled as such, with
the reasoning that it preserves equivalence classes stated explicitly or absent.

### G4 — an UNSAT-certifying pipeline must actually exist  ← **BLOCKED as of 2026-09-28**

`drat_roundtrip_test.py` was written to settle this before any compute, and it found
three independent blockers. Re-run it first; it must report
`SOLVED_WITH_CHECKED_PROOF` for a search-requiring instance before G4 is met.

| # | blocker | evidence |
|---|---|---|
| G4.1 | PySAT's CaDiCaL accepts `with_proof=True` and emits learned clauses and deletions, but the **retrieved trace contains no empty clause**, so it never closes the proof | `PHP(7,6)`: 1932 lines, 980 additions verified RUP, 952 deletions applied, **0 empty-clause lines** |
| G4.2 | **Kissat refuses proof logging** in PySAT | `NotImplementedError: Proof logging is not supported by Kissat in PySAT` — so the solver behind the actual `n=71..76` records cannot run in proof mode here |
| G4.3 | **No independent checker** present | `drat-trim`, `cake_lpr`, `gratgen` all absent; this round's own RUP-only checker is self-written and does not implement RAT |

**Consequence: an UNSAT at n=75 produced in this environment today must be recorded as
`COMPUTE_RESULT_UNVERIFIED`.** To lift this: provision a standalone proof-capable
solver (CaDiCaL or Kissat invoked directly with `--proof` / `--lrat`, not through
PySAT's wrapper) plus an independent checker (`drat-trim` or `cake_lpr`), then re-run
`drat_roundtrip_test.py` and require a green result *before* launching n=75.

### G5 — the run must be bounded and its residue recorded
- Name the solver, version, and exact invocation.
- Fix a wall-clock budget **in advance**; record it.
- On any non-SAT outcome, preserve: the instance hash, the solver log, the conflict
  and propagation counts, and the elapsed time. `wustep/maths` did exactly this
  (a restricted-slice UNSAT at 499 s with no trace, a full `UNKNOWN` at 1,350 s, two
  externally-killed runs at ~1,650 s) and correctly refused to call any of it a result;
  the same standard applies here.

## 2. Output vocabulary (use these exact labels)

| label | meaning |
|---|---|
| `COMPUTE_SAT_VERIFIED` | solver SAT; the model was decoded to a 150-point file, re-verified for no-three-in-line by an **independent** checker, and checked against the row bound. Only then: `D(75) = 150`. |
| `COMPUTE_UNSAT_VERIFIED` | solver UNSAT **and** the trace was checked by an independent checker **and** the instance passed G1–G3 with `iden` scope (or the scope is named explicitly, e.g. `rot2`). |
| `COMPUTE_UNSAT_RESTRICTED` | UNSAT on a symmetry-restricted instance whose trace was checked. Excludes `G`-invariant certificates only. Never a statement about `D(75)`. |
| `COMPUTE_RESULT_UNVERIFIED` | any UNSAT without a checked trace — including `s UNSAT` from PySAT today (G4). |
| `COMPUTE_UNKNOWN` | timeout / killed / OOM / `s UNKNOWN`. **No** inference of any kind. |
| `COMPUTE_REQUIRED` | nothing run yet. The current status. |

## 3. What a purely restricted UNSAT would and would not mean for n=75

To be stated in any report that includes a restricted UNSAT:

- `rot4` and full-`D4` are **already excluded for n=75 by arithmetic**, not by a
  solver: 150 ≡ 2 (mod 4) while the orbit sizes are {1,4}; and 150 is not of the form
  `8a+4b+c`. No solver run is warranted for either.
- `rot2` (180°) has **no** cardinality obstruction, so `rot2 UNSAT` would be the first
  non-trivial restricted exclusion — and it would still say only "no 180°-symmetric
  150-set exists". Certificates need not have any symmetry at all.
- A **full, unrestricted** UNSAT is the only UNSAT that would establish
  `D(75) < 150` — and it would need a checked proof, because a solver's word is not
  evidence.

## 4. Honest expectation

The `rot2` instance is ~15× the clauses of the prior-art canonical-rct4 instance
(996,434 vars / 2,398,895 clauses) that already returned `UNKNOWN` on a full run and
needed ~500 s to refute only a *restricted slice*. A different outcome for the larger
instance is unlikely inside one session. The deliverable that is realistically
achievable is therefore **not** a resolution but the following, which this protocol
exists to make trustworthy: a reproducible instance, a proved sound restriction, a
bounded run, and an exactly-labelled residue.

## 5. Definition of done for the compute round

1. G1–G3 satisfied with recorded hashes and audit output.
2. G4 **either** satisfied (pipeline re-tested green) **or** explicitly recorded as
   unmet — in which case no UNSAT may be reported as anything but
   `COMPUTE_RESULT_UNVERIFIED`.
3. One bounded solver run per formulation, with logs and residue preserved.
4. Every SAT model verified by an independent checker before any `D(75)` claim.
5. A round report using the §2 vocabulary, with the scope of every claim named.
6. No edit to `problem.json`, the evaluator, or `completion_criterion`. n=75 remains
   `OPEN` regardless of the outcome; a finite result does not complete the general
   conjecture.
