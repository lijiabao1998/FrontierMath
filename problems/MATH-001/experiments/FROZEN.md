# FROZEN — superseded as the canonical merge unit

This directory tree (on `dsk/MATH-001-independent-verifier-r1`, PR #5) is **frozen**. It is kept
as history and as a benchmark of the review process; it is **not** the merge unit for MATH-001
evidence any more.

| unit | branch | PR |
|---|---|---|
| **canonical evidence** (the facts, with the merge gate) | `dsk/MATH-001-canonical-evidence` | #6 |
| **compute tooling** (encoders, audits, DRAT tooling, protocol) | `dsk/MATH-001-compute-tooling` | #7 |
| **in-round execution evidence** | `dsk/MATH-001-round-execution` | — |
| this tree (frozen history) | `dsk/MATH-001-independent-verifier-r1` | #5 |

## Claim hygiene applied before freezing

Per the owner's instruction, no active canonical document in this tree publishes a withdrawn
claim. The corrections are:

- `independent_verifier_r1/REPORT.md` — the claim that the round was executed and all criteria
  passed is **withdrawn** and marked NOT RUN IN THIS PR (the evidence was split out).
- `independent_verifier_r1/PROVENANCE.md` — the reference-script hash and the packaging decision
  are recorded with the LF-normalisation caveat.
- `n75_attack/limitations.md` — the DRAT/G4 blockers are recorded as environment limitations.
- `n75_attack/COMPUTE_PHASE_PROTOCOL.md` — G2 states plainly that it is NOT yet satisfied for
  `n=75`, and the commands now pass the manifest the audit requires.

The full register of every withdrawn claim from this line of work lives in the canonical branch at
`problems/MATH-001/experiments/canonical_evidence/SUPERSEDED_CLAIMS.md` (21 entries).

## No new functionality

This freeze adds no proof pipeline, no audit framework and no compute plumbing. Anything further
belongs on the tooling branch, which may continue to receive review passes without gating the
canonical evidence merge.
