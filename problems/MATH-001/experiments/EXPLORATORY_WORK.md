# PRE-ADMISSION EXPLORATORY WORK (DeepSeek r1)

**Read this before trusting anything under `problems/MATH-001/experiments/independ*`,
`n75_attack/`, `lit_data/` or `prior_art/`.**

## What happened, stated plainly

The artifacts under those directories were produced **before any round was admitted**.
They are real work and their results stand on their own evidence, but they are **not**
the product of a frozen round: no acceptance criteria were registered in advance, no
budget was declared in advance, and no search record existed at the time the results were
written. They are therefore labelled **PRE-ADMISSION EXPLORATORY WORK**.

The review finding that produced this file was correct on both counts:

1. The change set was described as "not a round" while containing a new verifier, new
   exhaustive results, a new attack bench, a new compute protocol and new experiments —
   that is research activity, and it must be registered as such.
2. A `round.json` was subsequently created for it, but with an acceptance and preflight
   written **after** the work. That is a retroactive pre-registration, i.e. it fabricates
   the thing that makes a round meaningful. **That record has been deleted**, and this
   file records that it existed and why it was removed rather than quietly overwriting it.

What replaces it: a **new, genuinely admitted round** whose preflight ran fresh and whose
acceptance was frozen *before* its computations, and in which the key verifications are
**re-executed from the current reproducible state**. Only results produced inside that
round are recorded in the new `round.json`.

## Inventory: what is exploratory, and what was re-run

| artifact | status |
|---|---|
| `independent_verifier_r1/` — third certificate checker, `DERIVATION.md`, adversarial suite, `REPORT.md` | **exploratory**. The checker itself is re-validated in the admitted round (calibration + adversarial suite re-run); `REPORT.md`'s claims remain exploration until then |
| `independent_verifier_r1/brute_force.py` — exhaustive ground truth `D(1..4)`, row-pair counts `n=2..8` | **exploratory**; re-run in the admitted round |
| `independent_verifier_r1/verify_all_known.py` + `cross_check_database.py` — 431,008-configuration verification, `n=71..76` records via two retrieval paths | **exploratory**; re-run in the admitted round |
| `n75_attack/` — two formulations, symmetry proofs, calibration, `benchmark.json` | **exploratory**; calibration re-run in the admitted round. The *proofs* in `formulation.md` are mathematics and do not depend on a round, but they are re-checked for internal consistency |
| `n75_attack/COMPUTE_PHASE_PROTOCOL.md` | **exploratory**, frozen by intent; the admitted round tests its G4 precondition |
| `lit_data/`, `prior_art/` | provenance material, not results |
| `DEEPSEEK_LITERATURE_AUDIT.md`, `DEEPSEEK_REVIEW_FrontierMath_PRs.md` | review documents, not research rounds |

## What this labelling does NOT change

- The **verification results themselves** are not retracted. The evidence is in the
  committed code, hashes and JSON, and is reproducible by anyone: `DERIVATION.md` §3's
  criterion is a proof; the 431,008-configuration pass and the `n=71..76` record
  verification were done with printed commands and recorded hashes.
- The **mathematical content** of `formulation.md` (pair-line injectivity, the
  `rot4`/`full`-`D4` orbit-counting exclusions for n=75, the soundness proof for
  `S ≤lex Sᵀ`) is a proof, not an experiment, and needs no round.
- What changes is the **governance claim**: these were not produced under a frozen
  acceptance, so they cannot be cited as round-registered evidence. The admitted round
  supplies that for the parts that were re-executed.

## Fixed review findings folded into this wave

Beyond the governance restructure, three P1 defects in this exploratory code were
repaired before the admitted re-run, each with its own regression suite:

| finding | fix |
|---|---|
| `fetch_third_party.py --check` exited 0 on a missing file, certifying provenance it never observed | fail-closed on missing / size / hash / download failure; 9-case regression suite, verified to catch the original bug |
| the CNF audit accepted a line if ANY one negative triple was present | now requires **all** `C(k,3)` triples on explicitly encoded lines, plus a semantic `F ∧ T` UNSAT check for network-encoded lines; 8-case suite including the reviewer's exact 1-of-10 counterexample |
| the DRAT round-trip exited 0 when blocked and 1 when a proof was checked | exit 0 **iff** a checked proof was obtained; a hand-built 2-step valid DRAT proof validates the checker so green is honestly reachable when a solver pipeline exists; 14-case suite |
