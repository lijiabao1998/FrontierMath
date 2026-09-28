# DEEPSEEK_LITERATURE_AUDIT — MATH-001 (2026-09-28)

Fresh, independent literature pass for MATH-001. **GLM's `LITERATURE_MAP.md` was not
used as a starting point for the searches**, though its claims are compared at the end.
Engine: web search + direct fetch of primary sources. Search window: 2026-09-28.

## Classification

| # | item | class | evidence |
|---|---|---|---|
| 1 | `D(n) ≤ 2n` (row pigeonhole) | **confirmed** | derived here (`DERIVATION.md` §2) and corroborated by exhaustive powerset enumeration at `n = 2,3,4` which does not use the argument |
| 2 | All `n ≤ 70` have `D(n) = 2n` | **confirmed** | readme: "now no-three-in-line solutions are known for all grid sizes ≤ 70" (2026-06-21, Heule `n=67,69`) |
| 3 | `n = 71,72,73,74,76` also solved; `n=75` the only gap in `[2,76]` | **confirmed, by three independent artifacts** | (a) readme announcements; (b) `table.html` (2026-09-11): the `n=75` row is **blank** while every other `n ≤ 76` has an entry; (c) `download/all_known_solutions` (2026-08-31): 431,008 configurations, **zero at `n=75`**, present at every other `n ∈ [2,76]`. Plus the CGI lookup: "sorry for n=75 no configurations are known" |
| 4 | record `n = 76` (Heule, rot4, 2026-08-10) | **confirmed and independently verified** | decoded from two independent paths; 152 points, all rows/columns used, no three collinear, invariant under the full 90° rotation |
| 5 | "smallest open `n` is 75" | **probable** (sound inference, not a stated fact) | Flammenkamp never writes "n=75"; it follows from the enumeration. Also confirmed as the state of *this database*, which is a search-status source, not an impossibility result |
| 6 | `Heule` SAT solutions at 65,67,69,70,71,72,73,76 | **confirmed** (readme + database), **certificate publicly retrievable** | both retrieval paths succeeded for all of 71,72,73,74,76 |
| 7 | Kudriashov, *Certified computations on no-three-in-line problems…*, arXiv:2609.25133, **2026-09-20** | **confirmed to exist; read at abstract level** | fetched `arxiv.org/abs/2609.25133`. It is about the **cube** variant `a(1..6) = 1,8,16,28,40,64` (DRAT-certified via kissat + drat-trim), `b(n)` no-four-coplanar, the **Guy–Kelly first-moment count** (corrected constant `π/√3`, threshold crossing `n=493`), and the **direction spectrum of 2n-point solutions**. It makes **no claim about the plane at n=75** and does not resolve the general conjecture |
| 8 | Prellberg arXiv:2602.07751 — `D(n)=2n` for `n ≤ 60` via CP-SAT, symmetry-reduced; `812` variables / `118,241` constraints at `n=57`; a `384`-independent-run protocol | **confirmed at abstract level** (independent reading: `wustep/maths` RESEARCH.md 2026-08-23 logged a full-text read). Journal: J. Combin. Theory Ser. A |
| 9 | `wustep/maths` n=75 attack log | **confirmed, and it is real prior art** | `problems/three-in-line/{RESEARCH,ATTACK}.md` fetched. Contains a canonical-rct4 DIMACS for `n=75` (996,434 vars / 2,398,895 clauses, SHA-256 `1709cdf478920fd9ed0160bc5f00e049b10f0f6b28a1955560cd4aaa88205317`), a **restricted** UNSAT (≥28 of 37 seed orbits, 499 s, **no proof trace**, recorded as residue), a full Glucose run `UNKNOWN` after 1,350 s, and two externally-killed CaDiCaL runs. Also a verified replay of Heule's `n=71` (142 points, 467,180 determinants, 10,011 normalized pair-lines) |
| 10 | HJSW 1975 gives `(3/2−ε)n` infinitely often; still the best proved general lower bound | **probable** (secondary sources only; not re-read) | no 2024–2026 improvement located in this pass |
| 11 | Grebennikov–Kwan arXiv:2510.17743 (2025): no-`(k+1)`-in-line for large constant `k`, explicitly not `k=2` | **claimed-only in this pass** (search-summary only, not fetched) | flagged rather than relied on |
| 12 | "Polynomial Structure of No-Three-In-Line Sets" (Zenodo, 2026), Lean 4 formalization, CRT obstruction at `6×6` | **claimed-only in this pass** | search-summary only; not fetched, not relied on. Relevant as a possible Lean prior art for `n75_attack`-adjacent formalization work |
| 13 | "spectral methods give `≤ (2−ε)n`" upper bound | **not independently verified / retracted-class** | still no primary source found; GLM r1 reached the same conclusion. Must not be cited |
| 14 | The general conjecture `∀n≥2, D(n)=2n` | **unresolved** | no paper claims it; the cubic case and the plane `n=75` are separate questions |

## Scope comparisons that must not be blurred

1. **Finite `n` ≠ general conjecture.** A verified certificate gives `D(n) = 2n` for
   that one `n`. Any presentation that reads "certificates for `n ≤ 76`" as progress
   on *the* problem in the sense of resolution is a scope transfer.
2. **Record ≠ coverage.** "record `n = 76`" (largest `n` with a known solution) and
   "all `n ≤ 76` except 75" are two different statements with different evidence.
   Both happen to be true; they are not the same claim.
3. **Cube ≠ plane.** arXiv:2609.25133's DRAT-certified exact values are for
   `{0..n-1}³` (A399138) and A280537. They say nothing about `D(n)`.
4. **Search status ≠ impossibility.** "no configurations are known for n=75" is a
   statement about a database, not a theorem that none exist.
5. **`rct4` is a search space, not a symmetry group.** Flammenkamp's own page says
   the class "is not a symmetry class of the grid". This round measured, as a
   property of the objects, that the `c`-labelled records are invariant under exactly
   the 180° rotation. An UNSAT within `rct4` does not refute `D(75) = 150`.

## Where GLM's r1 `LITERATURE_MAP.md` is deficient

GLM's map is **substantively accurate** on everything it asserts about the planar
problem, including all of items 2, 3, 6, 13, and its `PARTIAL_PROGRESS` verdict. Its
gap is coverage, not correctness:

| gap | consequence |
|---|---|
| **does not contain arXiv:2609.25133** (2026-09-20), a certified-computation paper that is directly adjacent (it even measures the *direction spectrum of the 2n-point solutions*, part IV) | missed primary source; no wrong claim results, but the map is incomplete for a 2026-09-27 round |
| **does not contain the `wustep/maths` n=75 attack log** | this is the most directly relevant prior art for the r1 "next step 2: 對 n=75 發起 SAT/CSP 攻略前置". GLM proposed work that a public log shows has already been attempted and walled, with a 996k-variable instance — and the r2 PR then built a bench without citing it |
| **does not contain `table.html` or `download/all_known_solutions`** | the two strongest artifacts for its own frontier claim, and the two that would have let r2 verify `n=71..76` instead of recording them as BLOCKED |
| does not mention Grebennikov–Kwan or the Zenodo Lean-4 item | acceptable (secondary/adjacent), but they should be listed as `claimed-only` rather than absent |

**No GLM literature claim was found to be false.** One GLM *limitation* claim
("frontier config access blocked") is false — see `independent_verifier_r1/REPORT.md` F1.
Per instruction, no card was edited on the basis of this audit; the evidence is
recorded here in this branch for review.

---

## Late additions (fresh confirming search, 2026-09-27T20:0xZ, after the audit above)

A second search pass was run to check specifically for 2026-09-27/09-28 updates and for
errata. It found **two items the first pass and GLM's map both missed**. The first is a
genuine erratum-class paper.

| # | item | class | evidence |
|---|---|---|---|
| 15 | **Voutier, *On the Guy–Kelly Conjecture for the No-Three-In-Line Problem*, arXiv:2603.00215** (v1 2026-02-27, v2 2026-03-09) | **confirmed to exist; read at abstract level** | abstract fetched. It supplies the details of the error **Gabor Ellmann found in 2004** in the Guy–Kelly heuristic and the resulting correction to their *conjectured upper bound*. The abstract itself gives no constants; secondary summaries report the corrected constant as `π/√3` (matching part III of arXiv:2609.25133 and Prellberg). It makes **no claim about `D(n)` for any specific `n`, and does not mention `n=75`** — so it does not change the problem's status. This is the erratum-class item the round's `retractions_checked` flag exists to catch, and until now it was missing from both this audit and GLM's map |
| 16 | **`aujurd22/no3inline-rigidity` — `analysis/even_n_existence_tools/ROT4_MULTIGRAPH_MODEL_CORRECTION_2026-07-19.md`** (MIT licence) | **confirmed; read in full** | fetched via the GitHub API. A **model correction that RETRACTS previously claimed infeasibility certificates** (see below) |

### On item 16 — what it corrects, and why it does not affect this round's n=75 claim

The correction's subject is explicitly `m = 37, n = 74`, i.e. **even** `n`. Its content:
the old `build_general_model` imposed `x_uv + x_vu ≤ 1` on each unordered endpoint pair,
and **that constraint is wrong** — in the contracted 2-regular object `(u,v)` and `(v,u)`
are *distinct C4 orbits*, and they may coexist as two parallel edges forming a digon. The
study had earlier recorded that digons do occur in the small-`m` census. An independent
geometric audit over all `C(37,2) = 666` pairs (disjoint 8-point orbits, four rows/four
columns, two points per row and column, no three collinear inside the union) passed with
0 failures.

**Withdrawn by that correction** (all in the even-`n` rot4 line, none of them cited by this
round): the `k=11` full neighbour-layer closure, the `k=12` corridor for `3 ≤ A ≤ 6`, the
`A=6` low-`B` `q=3`/`q=4` closure, and the `q=4` direction-pair certificate. Results that do
not use the faulty constraint remain valid (normalisation-distance lemma, deletion-window
identity, `q=1` double-resource and general-direction Gaussian resource formula, the blocker
oracle, the blocker-only flip bound, the 666-pair audit, and certificates re-derived under
the corrected model).

**Why this does not touch this round's `rot4`-excluded-for-n=75 result.** This round's
exclusion is a pure **orbit-cardinality** statement about a group action, with no multigraph
or CP-SAT model anywhere in it: for odd `n` the 90° rotation `T` has only orbits of size 1
(the centre) and 4, so a `T`-invariant set has size ≡ 0 or 1 (mod 4), while `150 ≡ 2
(mod 4)`. That argument cannot be repaired or broken by an edge-orientation constraint in
someone else's SAT encoding. The two statements live in different regimes (odd vs even `n`)
and different formalisms (orbit counting vs contracted-graph modelling).

**What it does mean for the bench:** the general lesson is transferable and is already
reflected in `n75_attack/COMPUTE_PHASE_PROTOCOL.md` G3 — an encoding can silently over- or
under-constrain the object it is meant to represent, so an UNSAT from any model must be
accompanied by an audit that the formula expresses the problem (G2) before it is believed.
Here the failure mode was the opposite direction: an over-constraint that made a space look
smaller than it is and produced infeasibility certificates that did not hold.
