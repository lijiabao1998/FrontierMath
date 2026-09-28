# External verifier review — FrontierMath PRs #2, #3, #4 (DeepSeek r1, 2026-09-28)

Reviewer: DeepSeek, branch `dsk/MATH-001-independent-verifier-r1`. Not an author of any
reviewed PR. No reviewed branch was modified. No merge performed.

Method: read the PR bodies **and** the actual code, results, evidence and CI, then
re-derive independently (`experiments/independent_verifier_r1/`) rather than re-running
the author's programs. Findings are graded against what the PRs *claim*, not against
what a stronger paper could have claimed.

---

## PR #2 — `glm/MATH-001-baseline-r1`

| CLAIM | EVIDENCE | INDEPENDENTLY VERIFIED? | SCOPE | FAILURE MODE | REC |
|---|---|---|---|---|---|
| evaluator v1 + v2 sound, 636 adversarial cases | `results/r1/negative/`, `tamper_test.py` | **yes** — a third implementation (pair-line injectivity, `O(m²)`) plus a 429-case suite whose oracle shares no code with the checker; 0 disagreements | certificates only | none found | — |
| self-certificates `n = 2..10` | `results/r1/self/*.json` | **yes** — all 9 pass; exact `D(n)=2n` for `n=2..8` additionally re-derived by exhaustive enumeration | finite `n` only | none | — |
| 36,912 public configurations reproduced | `results/r1/flammenkamp/` | **yes** — re-downloaded from source, byte-identical hashes, own decoder, 36,912/36,912 legal; mutation teeth check 371/371 | `n=2..52` subset | none | — |
| literature update: frontier `n≤74` minus 75, record 76, smallest open 75 | `LITERATURE_MAP.md` | **yes**, and by two artifacts GLM did not cite (`table.html` blank row; `all_known_solutions` zero count at 75) | finite frontier; general problem still open | map omits arXiv:2609.25133 and the `wustep/maths` log | — |
| no independent reproduction claimed | PR body | **correctly disclaimed** | — | — | — |
| artifacts: 715 files, 101,044 insertions, 702 JSON | `git diff --numstat` | necessary research evidence, but see packaging below | — | repo bloat | see P-1 |
| CI | records + lean green | not re-run here; workflow pin `07d2b130` matches `GOVERNANCE.lock.json` | — | — | — |

**Verdict: `NEEDS_CHANGES`.** The science is sound and independently reproduced. Two
changes are required first: (a) the r2 "BLOCKED" limitation must be retracted or the
record will freeze a false statement about public data availability
(`independent_verifier_r1/REPORT.md` F1); (b) the packaging question P-1 should be
decided, because 702 committed JSON artifacts include third-party data whose
redistribution terms are not stated in the PR.

## PR #4 — `glm/MATH-001-n75-bench-r2`

| CLAIM | EVIDENCE | INDEPENDENTLY VERIFIED? | SCOPE | FAILURE MODE | REC |
|---|---|---|---|---|---|
| bench `BENCH_SOUND` (4/4) | `runs/20260927T191802542471Z-glm-MATH-001/` | **not re-run** (784 files, 142k insertions); the *independent* bench in `experiments/n75_attack/` reaches the same class of conclusion by different means | bench only | — | — |
| n=71–76 config access **BLOCKED** | PR body | **REFUTED.** Public retrieval works two independent ways; this round verified all of `n=71,72,73,74,76` and recorded `n=75` as absent from the database | — | **a false limitation**, and one that the r2 bench is built on top of | **`BLOCKED`** |
| no resolution claimed | body + report | **correct** — no `D(75)` claim is made; this is the right posture | — | — | — |

**Verdict: `BLOCKED`.** The blocker is not the mathematics, it is that the PR's stated
reason for not verifying the frontier is wrong, and merging it would put an incorrect
statement into the permanent record while a verifiable route existed. The minimal fix
is a one-paragraph correction plus the `n=71..76` verification, which is now available
in this branch.

## PR #3 — `grok/MATH-001-baseline-r1`

Not part of the assigned review set (the assignment named PR #2). Not reviewed here;
note only that it is a third independent r1 on the same problem and the same
`n≤76`-frontier claims, so P-1 and F1 apply to it too.

---

## P-1 Packaging assessment (requested)

The task asked which artifacts are necessary evidence, which are regenerable, which
raise redistribution questions, and whether hashes + fetch instructions beat vendored
data. Applying that to PR #2 and PR #4:

| artifact class | example | necessary? | regenerable? | redistribution | recommendation |
|---|---|---|---|---|---|
| research programs | `experiments/baseline_r1/*.py`, `experiments/n75_attack/*.py` | **yes** | n/a | own work | commit |
| round records | `runs/*/{round.json,LITERATURE_MAP.md,ROUND_REPORT.md}` | **yes** | no | own work | commit |
| hashes + environment | `results/*/hashes.txt`, `environment.txt` | **yes** | no | own work | commit |
| self-generated certificates | `results/r1/self/*.json` (9 files, small) | **yes** | yes | own work | commit |
| decode summaries | `results/r1/flammenkamp/decode_verify_summary.json` | **yes** | yes | own work | commit |
| representative public certificates | `results/r1/flammenkamp/flam_n*.json` (sample) | **yes**, as samples | yes, from upstream | **third-party** | keep a small sample, record the upstream URL + SHA-256, and state the licence basis |
| **the full vendored third-party corpus** | `lit_data/known_solutions_1997.txt` (1.65 MB) | **no** | yes, by URL | **third-party; terms not stated** | **replace with URL + SHA-256 + fetch script** |
| `lit_data/decode.c`, `readme.html` | small | useful | yes, by URL | third-party | URL + hash |
| `lit_data/dl/all_known_solutions` (23.8 MB, if added) | | no | yes | third-party | **must be URL + hash only**; do not vendor |
| huge generated DIMACS (e.g. 695 MB; PR #4's instances) | | no | yes, ~140 s from a generator | n/a | do not commit; record generator + SHA-256 |
| `__pycache__/*.pyc` | `experiments/baseline_r1/__pycache__/` | **no** | yes | n/a | **remove**, add to `.gitignore` |

Concrete recommendation: adopt a **manifest** pattern — one
`results/<round>/artifacts.json` per round listing, for every input, its URL,
SHA-256, byte count, fetch date and licence note; and for every output, its
generator command plus SHA-256. Keep only the small self-generated certificates and
summaries in-tree. That preserves full reproducibility while removing the
redistribution question and most of the 100k+ diff.

Note: this reviewer's branch follows that rule — the 23.8 MB database and the 695 MB
DIMACS are **not** committed; only URLs, hashes and generators are.

## Answers to the assigned review questions

- **Which artifacts are necessary research evidence?** Programs, round records,
  hashes/environment, self-generated certificates, decode summaries, and a *sample* of
  third-party certificates.
- **Which are regenerable?** Every third-party corpus (by URL), every large DIMACS
  (by generator), all `__pycache__`.
- **Which raise licensing/redistribution questions?** The vendored Flammenkamp data
  files. The upstream pages state no licence in the fetched material; "freely
  downloadable" is not a redistribution grant. This is a real, unresolved question in
  PR #2, and it should be answered explicitly rather than left implicit.
- **Should the repo compact?** **Yes.** Move to URL + SHA-256 + fetch script for
  third-party data and for large generated instances; keep small own-work artifacts.
  This is also the only way the diff stays reviewable.
- **Are hashes + fetch instructions better than vendoring?** **Yes for large or
  third-party data**, provided the hash is of the *upstream* bytes and the fetch is
  reproducible — which this round demonstrated is achievable (all three upstream files
  re-downloaded byte-identically, and the 431,008-configuration database too).
  **No for small own-work evidence** (self certificates, summaries), where vendoring
  is cheaper than re-deriving.

## Merge recommendations

| PR | recommendation |
|---|---|
| FrontierMath #2 | **NEEDS_CHANGES** — retract/repair the BLOCKED limitation (F1); resolve third-party redistribution (P-1); drop `__pycache__` |
| FrontierMath #4 | **BLOCKED** — carries the false "config access BLOCKED" premise; correct it and incorporate the now-available `n=71..76` verification |
| FrontierMath #3 | not in the assigned set; F1/P-1 apply |

No PR is recommended `READY_FOR_OWNER_REVIEW` in its current state. None of these
objections is about the quality of the computations; all three are about accuracy of
the stated record and about reproducibility packaging.
