# MATH-001 convergence maintenance — acceptance frozen before edits

- Started: 2026-09-29T13:35:00Z.
- Classification: software/provenance repair of existing evidence, not a new research round.
- Exact repair base: FrontierMath PR #6, `d90aa6410a89e2c88c85bdb4f8b3e4f5b9ee4f35`.
- Fetched main: `cd1e4eadc177920b95332ebe08c2498e52c3ce56`.
- Governance: `07d2b13051b83215182e411e1612f92f1912d8fb`.
- Budget: 30 minutes, USD 0, at most 100 test/verification invocations. No n=75 solve.
- Ownership: `gpt/MATH-001-convergence-20260929`, separate worktree; existing GLM,
  dsk and grok branches and dirty files are preserved. The owner authorized this
  convergence repair; a replacement PR records scope without posting to other PRs.

## Fixed acceptance

1. A rejected, malformed or empty required self-certificate set must cause nonzero
   exit. Corpus-only use must explicitly opt out, report NOT_REQUESTED, and make
   no claim about self-certificates. A declared target inconsistent with 2n fails.
2. Every nonblank database record must decode. Empty, malformed, truncated or
   geometrically invalid corpora fail. Full mode requires exactly 431,008 decoded
   records; sample mode is explicitly labelled and never certifies the full corpus.
3. CLI regression tests exercise known legal input plus each failure path. Do not
   alter the mathematical checker, problem statement, success threshold, or old
   research acceptance. The existing 36,912 count and 0.9 mutation gate stay fixed.
4. Preserve previous evidence as historical output. Regenerate the stale 1997
   corpus artifact using the repaired command, retaining exit reasons and explicit
   self-certificate scope. Only reuse the already-recorded SHA-256 corpus bytes.
   Full 431,008 verification is a regression of that same snapshot, not a new claim
   about current literature or an n=75 result. Unrun work remains NOT_RUN/HOLD.
5. Record commands, runtime, raw output, input/code/artifact SHA-256 and compare
   hashes with committed Git blobs; no system installs or third-party vendoring.
6. Existing P1/P2 and superseded branches remain HOLD until separately resolved or
   explicitly superseded. CI success alone is not review approval. No merge here.

No new `round.json` or refreshed literature claim is created: this repairs the
software exit contract and provenance of a fixed historical snapshot. Any later
research round still requires new four-way source checks and admission.
