# Superseded and retracted claims register

Every claim this line of work has withdrawn, with the reason and where the correction lives.
Kept in one place so no reader has to reconstruct the history from commit messages.

If a number or statement appears in this register, it is **not** current. No active document in
this branch publishes any of them except as an explicit retraction.

| # | withdrawn claim | status | reason | correction / evidence |
|---|---|---|---|---|
| R1 | "the environment cannot retrieve the frontier configurations (`n=61..76`); access is BLOCKED" | **REFUTED** | Two public retrieval paths exist and were both used: the coded corpus `…/no3in/download/all_known_solutions` (431,008 configurations, `n=2..76`, 2026-08-31) and the live lookup endpoint. Recorded in the r1 and r2 round reports of FrontierMath PRs #2/#4. | `CANONICAL_FACTS.md` C3; `evidence/all_known_solutions_verification.json` |
| R2 | "independent S₂ slope 1.4911 vs GLM's 1.54, 3% apart, **consistent with realisation noise**" | **RETRACTED** | The estimator has *zero* realisation noise — the per-seed spread is ~1e-15, as GLM's own `sf_std` shows — so noise cannot explain a 0.0489 gap. The comparison was between two different quantities: all 234 integers in `[16,249]` versus GLM's 13 geometric lags. The gap is a lag-set (sampling) difference. | Physics canonical: exact reproduction to ~1e-14 |
| R3 | "implementation error excluded" argued from a **0.05 tolerance** | **RETRACTED** | An unexplained cutoff is not an error budget; and no noise exists to absorb the difference. | replaced by exact reproduction against GLM's full-precision values |
| R4 | "the window's upper lags are **already saturated**; a second saturation mechanism truncates it" | **RETRACTED** | Saturation needs `k_lo·r >> 1`; the window reaches only 1.146. The exact local exponent is 1.1630 at `r=217` and 1.0723 at `r=249`, nowhere near 0. | replaced by: the window crosses the *onset* of finite-band turnover |
| R5 | "β=3 reaches exponent 1.9 for `r ≳ 3300`" | **RETRACTED — the inequality was reversed** | `2 − 1/L > 1.9` requires `L > 10`, i.e. `k_lo·r < 1.14e-4`, i.e. **`r < 0.0248`** — the regime is at *small* `r`, below one sample, not beyond the domain. | Physics canonical, corrected direction |
| R6 | recommended window **`[4,20]`**, and its replacement **`[15,21]`** | **RETRACTED** | `[4,20]` violates its own gate (`k_hi·4 = 5.52 < 20`). `[15,21]` satisfies the gate but gives β=5/3 → 0.7285, a *larger* deviation from 2/3 than GLM's window, because the local exponent sits above 2/3 at small `r` and below it at large `r`. Across windows β=5/3 spans 0.27…0.73. | no window is recommended; a resolved-band condition alone does not make a slope equal the asymptotic exponent |
| R7 | `C₀ = 0.461390`, "stable to **5e-7**" | **RETRACTED** | Overclaimed by two orders of magnitude and never swept over the advertised range. | → R8 |
| R8 | `C₀ = 0.4613932125…` presented at 16 digits as a "40-digit computation" | **RETRACTED** | Came from `mpmath.quad(f, [1, inf])`, which mishandles the oscillatory integral, giving `F_tail = 0.481883428` where two independent routes give `0.481882378` — an error of 1.05e-6 in `F_tail`, hence in `C₀`. It also used an undeclared dependency. | `C₀ = 0.4613921675492818`, standard library only, with the routes recorded |
| R9 | `0.461336` (script value) | **RETRACTED** | Partially converged quadrature, inconsistent with the report beside it. | as R8 |
| R10 | an audit that accepts a maximal line if **at least one** negative-triple clause for it is present | **RETRACTED** | Unsound for lines longer than 3 cells: the other triples may still be selectable, so an underconstrained formula passes. A reviewer demonstrated it by keeping 1 of the n=5 diagonal's 10 triples. | completeness now requires all `C(k,3)` triples on explicitly encoded lines |
| R11 | a semantic audit that asks whether the **whole** formula is satisfiable as its vacuity guard | **RETRACTED** | Unusable for the outcome under investigation: a genuinely UNSAT target would always be marked vacuous, so the protocol could never certify it, and it required solving the full instance synchronously. | the guard is local per line |
| R12 | "every decode-invariant-preserving mutation must become illegal" | **REFUTED as worded** (criterion defect, not a verifier defect) | 2 of 34,051 legality-changing mutations produce another *legal* `2n` configuration (single 2-character swaps; 42 and 46 distinct in-range points). A mutation mapping one legal solution to another is not a verifier failure. | restated criterion: **zero unexplained survivors**, which holds |
| R13 | a DRAT round-trip that exited 0 while **blocked** and 1 when a proof was checked | **RETRACTED** | Exit semantics were inverted, so a CI gate would read an uncertifiable pipeline as successful. | exit 0 **iff** a proof was checked |
| R14 | "the reference GLM script has SHA-256 `5244be1d…`" | **RETRACTED** | Checkout-dependent: that is the CRLF working-tree hash; the committed blob and the file on `glm/PHYS-001-baseline-r1` hash to `b1070ea4…` after LF normalisation. The digest was also computed but never compared. | LF-normalised hash pinned and enforced (mismatch refuses execution) |
| R15 | artifact hashes taken from the CRLF working tree | **RETRACTED** | None of them identified the committed artifact on a Linux checkout, and the manifest tried to hash itself. | hashes are now over **git blob** bytes |
| R16 | a round record created **after** the work, presenting a pre-registration it could not have had | **DELETED, not retconned** | Fabricating a frozen acceptance after the fact misrepresents the round. | deleted; the prior artifacts are labelled PRE-ADMISSION EXPLORATORY WORK, and a new round was admitted with its preflight run fresh and its acceptance frozen before execution |
| R17 | "this is not a round / no `start`/`admit` was run" | **SUPERSEDED** | It was true when written and became false once the round was admitted. | the report now states the admitted round and is marked NOT RUN IN THIS PR |
| R18 | the report claiming the round was **executed** and all criteria passed while the evidence was split out to another branch | **WITHDRAWN** | The claim was unsupported in that tree once the evidence moved. | marked NOT RUN IN THIS PR; reinstated only when the evidence lands with it |
| R19 | "the local audit rejects an over-constrained formula" via a weight-2 witness or a clause count | **SUPERSEDED (my own attempted fixes)** | The weight-2 witness produced **false negatives** on intact instances (other lines sharing a variable legitimately block it) and the clause count was too weak. | exact clause-**multiset** equality against an encoder-produced manifest; without a manifest the audit fails closed |
| R20 | certifying an independent checker by matching the substring `VERIFIED` | **RETRACTED** | It also matches `s NOT VERIFIED`, so a **rejected** proof could have been promoted to certification. | requires the checker's zero exit code AND a positive verdict AND no explicit negative marker |
| R21 | "the two quadrature routes agree to ~1e-12" as a claim in the JSON | **SUPERSEDED** | The claim was written but the routes were never executed by the committed script. | both routes are implemented and executed; the validation now carries an acceptance bound and **fails** if exceeded (executed spread 1.1e-12 vs a 1e-11 bound) |

## Notes on this register

- Items R2–R9 and R14–R21 arose in the DeepSeek verification line; R1 and R10–R13 arose from
  review findings on FrontierMath PR #5 and FrontierPhysics PR #3.
- Several items are **defects introduced while fixing an earlier item** (R19, R20, and the
  second appearance of the CRLF hashing issue in R15). They are listed rather than quietly
  corrected, because a fix that creates a new defect is exactly the kind of thing a register of
  this sort exists to make visible.
- Where a withdrawal concerns a *claim about the world* (R1, R10, R11, R12) the correction is a
  change in what is asserted; where it concerns *this tooling* (R13, R19, R20, R21) the
  correction is a change in behaviour plus a regression test.
