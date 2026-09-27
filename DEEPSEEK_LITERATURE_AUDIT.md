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
