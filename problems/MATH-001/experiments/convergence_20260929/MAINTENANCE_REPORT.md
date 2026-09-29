# MATH-001 convergence repair

This is a software/provenance repair of PR #6 at
`d90aa6410a89e2c88c85bdb4f8b3e4f5b9ee4f35`, preserving dsk's authorship of the
canonical mathematical evidence. It adds no new mathematical construction, solver
run, theorem, literature search, or independent research result. The original
problem and research acceptance remain unchanged; n=75 remains unresolved here.

## Changes

- `audit_r1_artifacts.py` now fails for missing, malformed, mathematically rejected
  or incorrectly declared self-certificates. The canonical corpus audit explicitly
  uses `--corpus-only`, which reports NOT_REQUESTED rather than a vacuous pass.
- `verify_all_known.py` rejects undecodable nonblank records, empty inputs,
  incomplete full scans, illegal configurations and legacy alphabet disagreement.
  Full mode binds its 431,008-record claim to the already-pinned SHA-256; sample
  mode reports SAMPLE_ONLY and cannot be mistaken for the full-database result.
- Historical pre-repair JSON is preserved in `canonical_evidence/evidence/history/d90aa641/`.
  Current artifacts are mechanically regenerated from the same corpus bytes.
- Exact commands, producer runtime, source/input/output hashes and stdout live in
  `evidence/*_run.json` and `evidence/*.log`. The Git-blob manifest also compares
  committed source and result bytes to the executed bytes, avoiding Windows EOL
  ambiguity. The proposed Windows/Linux CI configuration is preserved in
  `evidence-tools.workflow-proposal.yml`; it is not installed as a workflow.

## Reproduction

From the repository root:

```text
python -m unittest discover -s problems/MATH-001/experiments/canonical_evidence/database -p test_fail_closed.py -v
python problems/MATH-001/experiments/convergence_20260929/regenerate_fixed_snapshot.py audit
python problems/MATH-001/experiments/convergence_20260929/regenerate_fixed_snapshot.py database
python problems/MATH-001/experiments/convergence_20260929/verify_committed_evidence.py
```

The two corpus regressions require the exact locally cached bytes in canonical
`provenance/` and never download data. Their runner refuses a mismatching input
hash and has a fixed 780-second per-process limit. Sources are checked before and
after execution. The source corpora remain ignored and are not redistributed.

The 11 test methods include real CLI positive/negative geometry, malformed/empty/
truncated data, actual self-certificate verification and its exit status, target
mismatch, malformed JSON, missing required inputs, explicit corpus-only scope,
and conflicting options. Expensive corpus functions are isolated only for the
self-certificate exit tests; the real-corpus regressions are separate evidence.

## Observed validation (2026-09-29)

| Check | Actual result |
|---|---|
| Exit-contract regression suite | 11 test methods PASS; raw output `evidence/regression.log` |
| Fixed 1997 corpus audit | Exit 0 at 13:46:50Z; 36,912 decoded and legal, zero decode/verification failures; 371 of 371 exercised mutations rejected; explicit CORPUS_ONLY / self NOT_REQUESTED |
| Fixed complete corpus regression | Exit 0 at 13:45:24Z; 431,008 decoded and legal; zero decode/verification failures; FULL_PINNED_CORPUS; empty exit reasons |
| Runtime integrity | Both executions confirm input and all recorded source hashes unchanged |
| Pinned governance metadata validation | PASS: 10 problem records; only metadata validity, not proof of openness or discovery |

The repaired JSON retains the prior per-n corpus counts. A negative-input test
passing means the CLI rejected that input; it is not a new mathematical result.
Remote CI and independent review remain separate gates after publication.
The current GitHub OAuth credential rejected a push that introduced a workflow
without its `workflow` scope. The proposal was therefore moved outside `.github/`
before publication. Existing Lean and metadata CI remain unchanged; the new
regression and committed-byte checks have local execution evidence only.

## Other PRs stay separate

| PR | Reviewed head | Convergence decision |
|---|---|---|
| #6 canonical evidence | d90aa641 | This repair supersedes its three current-head findings; reviewer confirmation remains required. |
| #5 exploratory verification | 15a2f887 | Already closed without merge; #6 replaced its evidence scope. No changes here. |
| #4 GLM r2 bench | beaf8427 | HOLD. Exact committed-byte audit finds 11/17 r1 and 5/6 r2 manifest mismatches. Its current head also lacks a completed current-head re-review. |
| #2 GLM r1 | 0578fc74 | HOLD. Same-head review has 1 P1 and 3 P2: admission ordering, incomplete decoding, extension alphabet and hashes. |
| #3 grok r1 | 3f263076 | HOLD. Same-head review has 2 P1 and 1 P2: incomplete corpus/tail coverage and pre-execution source hashing. Local uncommitted fixes are preserved, not adopted as reviewed evidence. |
| #7 compute tooling | 7d8443f1 | HOLD as draft follow-up. No completed review or checked n=75 SAT/UNSAT certificate is inferred from green CI. |

These decisions are a snapshot of the exact heads above, not a claim that every
historical review thread remains an unfixed defect on every descendant. The #4
hash defects were independently checked against its committed objects; rerun
`audit_inherited_heads.py` to reproduce `evidence/r2_head_manifest_audit.json`
(expected exit 1, decision HOLD). Its existing local dirty manifests were untouched.

No PR is merged or closed by this repair. Integration, scientific claim approval,
and decisions about superseded PRs remain with the authorized governance reviewer.
