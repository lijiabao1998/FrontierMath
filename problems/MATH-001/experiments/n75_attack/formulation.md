# n=75 attack bench — formulations and derivations (DeepSeek r1)

Scope guard, stated first: **nothing in this directory resolves MATH-001 or n=75.**
The deliverable is a bench that (a) states exactly what a 2n-certificate is,
(b) gives two independent formulations with textual derivations, (c) records which
approaches are excluded *by counting* rather than by solver belief, (d) calibrates
the encoders against this round's exhaustive ground truth, and (e) marks n=75 as
`COMPUTE_REQUIRED`.

Prior art this bench does **not** duplicate (read and recorded in
`../prior_art/`, fetched 2026-09-28):
- Prellberg, *Constraint Satisfaction Programming for the No-three-in-line Problem*,
  arXiv:2602.07751 — CP-SAT with odd-order symmetry reduction, `D(n)=2n` for `n ≤ 60`.
- The `wustep/maths` attack log (`problems/three-in-line/{RESEARCH,ATTACK}.md`). Its
  canonical-rct4 DIMACS for n=75 has 996,434 variables and 2,398,895 clauses
  (SHA-256 `1709cdf478920fd9ed0160bc5f00e049b10f0f6b28a1955560cd4aaa88205317`).
  Reported: a *restricted* slice (retain ≥28 of 37 seed orbits) returned UNSAT in
  499 s with **no proof trace**; the full phased Glucose run returned UNKNOWN after
  1,350 s; two full CaDiCaL runs were killed externally. Recorded there as residue.
- Kudriashov, arXiv:2609.25133 (2026-09-20) — certified computations, but for the
  **cube** variant and the Guy–Kelly count, not the plane at n=75.

---

## 1. What a certificate must satisfy (restated precisely)

- Grid `G(n) = {1..n}²` (the card's 1-indexing).
- `S ⊆ G(n)` is legal iff no three *distinct* points of `S` are collinear.
- A certificate for `D(n) = 2n` is a legal `S` with `|S| = 2n` (cardinality of the
  point *set*, not of any serialisation — see `../independent_verifier_r1/DERIVATION.md`).
- The row-pigeonhole bound `D(n) ≤ 2n` holds because each row is contained in a
  line and a line may hold at most 2 points of a legal set. Hence a verified
  certificate gives `D(n) = 2n` **for that n only**.

Derived consequence used everywhere below (and used by `encoder.py`):

**Lemma 1 (exactly two per row and per column).** If `|S| = 2n` and `S` is legal
then `S` has exactly 2 points in every row and exactly 2 in every column.

*Proof.* Rows: each row is contained in the line `y = j`, so `|S ∩ {y=j}| ≤ 2`;
summing over the `n` rows gives `2n = |S| ≤ 2n`, so every row has exactly 2.
Columns: the line `x = i` gives `|S ∩ {x=i}| ≤ 2`, and the same sum gives equality. ∎

**Corollary (2-permutation form).** Identifying `S` with its `n×n` 0/1 incidence
matrix `M`, Lemma 1 says every row and column sum of `M` is 2. Hence `M` is the
incidence matrix of a 2-regular bipartite graph on the `n` rows and `n` columns,
so by König's edge-colouring theorem `M = P + Q` for two permutation matrices
`P, Q` with disjoint supports. Equivalently: **a 2n-certificate is a pair of
disjoint permutations of `[n]` whose union has no three collinear points.**

This is the formulation the exhaustive searches in
`../independent_verifier_r1/brute_force.py` and `run_small_n_calibration.py`
enumerate: choose an unordered column-pair per row, with the inherited guarantee
that columns are used exactly twice.

---

## 2. Formulation A — cell-based Boolean model

Variables `x[r][c]` for `(r,c) ∈ G(n)`: true iff the cell is selected.

```
(A1)  for each row j:  sum_{i=1..n} x[i][j]  = 2
(A2)  for each maximal line L with |L| >= 3:  sum_{(r,c) in L} x[r][c]  <= 2
```

Derivation of the constraint families:
- `(A1)` is forced by Lemma 1; conversely `(A1)` alone gives `|S| = 2n`, so no
  separate cardinality constraint on `|S|` is needed.
- A collinear triple lies on some line containing ≥3 grid points, and every such
  line is contained in a *maximal* one (adding points preserves collinearity). So
  `(A2)` over maximal lines is exactly "no three in line". Lines are indexed by
  primitive directions `(a,b)` with `gcd(|a|,|b|) = 1`, up to sign, and offsets
  `c` in `a·x + b·y = c`; `maximal_lines()` implements this.
- Columns are lines, so `(A2)` enforces "≤2 per column" too; that is *derived*,
  not assumed — an encoder that forgot columns would be caught by the audit in §6.

**Encoding cost.** `(A2)` for a line of length `k` is "at most 2 of k". This bench
uses explicit `(k+1)`-subset clauses when `C(k,3) ≤ 4096` (which for `k=3` gives
the single clause `¬a ∨ ¬b ∨ ¬c`), and a sequential-counter network from
`pysat.card` otherwise. `pysat.card` is pure Python and part of the already
installed `python-sat`; **no dependency was installed by this round**.
(For reference, `pysat.pb`'s pseudo-Boolean encoder is *not* usable here because
its `pypblib` backend is absent; the orbit formulation below is designed to avoid
needing it.)

## 3. Formulation B — orbit-based Boolean model

Fix a subgroup `G ≤ D4` acting on `G(n)`, and let `𝒪` be its orbits.
Variables `y_o` for `o ∈ 𝒪`: true iff **every** cell of the orbit is selected
(an orbit is either fully in or fully out of a `G`-invariant set).

```
(B1)  y_o <-> x[r][c]  for all (r,c) ∈ o      (when combined with A; standalone
                                                B treats y_o as the primitive)
(B2)  for every maximal line L:  sum_{o} |o ∩ L| · y_o  <= 2
(B3)  sum_{o} |o| · y_o  =  2n
```

`(B3)` is a weighted cardinality equality. To avoid needing a weighted encoder,
each `y_o` is **replicated `|o|` times**, the copies tied to the original by two
implication clauses, and one ordinary cardinality equality is posted over the
replicated literals. Orbit sizes here are at most 4, so the replica count is at
most `4·|𝒪| = O(n²)`.

`(B2)` is derived exactly as `(A2)`; the weight `|o ∩ L|` is the number of cells
the line meets inside the orbit, and it is at most 2 for the groups used.

> **Scope warning, load-bearing.** An orbit instance is a *restricted search*, not
> the original problem. `SAT` yields a genuine certificate and is sound evidence
> (`D(n)=2n` for that n). `UNSAT` means only "no `G`-invariant certificate", which
> says **nothing** about `D(n)`. Every UNSAT from Formulation B is therefore
> reported as `UNSAT_BY_ORBIT_PARITY` or `UNSAT_RESTRICTED`, never as a result
> about `D(n)`.

## 4. Counting exclusions for n = 75 (no solver involved)

For odd `n`, the 90° rotation `T(r,c) = (n+1-c, r)` has orbit sizes 1 (the centre
cell) and 4. Proof: `T²(r,c) = (n+1-r, n+1-c)`, whose only fixed point is the
centre, so every non-centre `T`-orbit has size dividing 4 but greater than 2;
size 2 would force `T²`-fixed, i.e. the centre. Hence sizes are 1 and 4 only.

Measured by `orbit_feasibility` (a bounded knapsack over orbit sizes with their
multiplicities — an earlier version of this function wrongly used an *unbounded*
coin problem and was caught by the calibration, see §7):

| group | orbit sizes (multiset) | target 150 | verdict |
|---|---|---|---|
| `iden` | 5625 × 1 | any | feasible |
| `rot2` | 1 × 1, 2812 × 2 | even | **feasible** |
| `rot4` | 1 × 1, 1406 × 4 | 150 ≡ 2 (mod 4) | **excluded by counting** |
| `dia1`,`dia2`,`ort1`,`ort2` | 75 × 1, 2775 × 2 | even | feasible |
| `full` (D4) | 1 × 1, 74 × 4, 666 × 8 | 150 ∉ {8a+4b+c} | **excluded by counting** |

For `full`: sizes are `8a + 4b + c` with `c ∈ {0,1}`; `150 = 8a+4b` requires
`2a+b = 37.5` (not integral) and `149 = 8a+4b` requires `2a+b = 37.25` (not
integral). So no D4-invariant 150-set exists, without any geometry.

**Consequence for n=75:** every 90°-rotation-invariant approach is dead on
arrival, as is any fully symmetric attack. The only rotation-type symmetry still
available is the 180° one (`rot2`), where the centre is forced empty (150 is
even) and exactly 75 of the 2812 two-orbits must be chosen. This is a real
reduction — 5625 cells → 2812 orbit variables — but it is a *restricted search*:
**`rot2` UNSAT at n=75 would not prove `D(75) < 150`,** because a certificate need
not have any symmetry at all.

## 5. Sound symmetry breaking (Formulation A)

The exclusions above are restrictions. A different device, `lex_break`, is *sound*
for the existence question:

**Theorem.** Every `D4`-orbit of subsets of `G(n)` contains at least one `S` with
`S ≤_lex Sᵀ` (comparing the row-major bit vectors of the incidence matrix and its
transpose). Hence adding `S ≤_lex Sᵀ` removes no `D4`-orbit and is a sound
restriction for "does a legal 2n-set exist?".

*Proof.* Let `S` be any subset with incidence matrix `M`, and let `Mᵀ` be its
transpose. Transposition is the reflection in the main diagonal, an element of
`D4`, so `M` and `Mᵀ` lie in the same `D4`-orbit. If `M ≤_lex Mᵀ` we are done with
`S`. Otherwise `M >_lex Mᵀ`, i.e. `Mᵀ <_lex M`; taking the image of `S` under
transposition gives a subset with matrix `Mᵀ` (transposition is an involution), and
`Mᵀ ≤_lex (Mᵀ)ᵀ = M`, so `Mᵀ` satisfies the constraint. In both cases the orbit
contains a satisfying element. ∎

Two honest caveats, both recorded in `limitations.md`:
1. The theorem gives *at least one* representative per orbit, not a canonical form.
   The constraint may leave several members of the same orbit, so it is weaker than
   full lex-leader symmetry breaking. It is validated as sound, not as tight.
2. Transposition-based breaking interacts with the `dia1`/`dia2` groups: an
   instance that *imposes* `dia1` symmetry is already transposition-invariant, and
   combining `lex_break` with such a group is at best redundant. It is only applied
   to the untreated cell formulation.

## 6. Certification hygiene: does the CNF express the problem?

An UNSAT is worth nothing if the formula is wrong. `audit_cnf_covers_lines()`
implements link (1) of certification explicitly (this is the link Kudriashov's
abstract singles out): for every maximal line with ≥3 grid points, it checks that
the DIMACS contains at least one clause `¬a ∨ ¬b ∨ ¬c` on a collinear triple of
that line. A silently dropped line family is the most likely encoder bug, and the
audit catches it directly — demonstrated by a negative control that deletes one
line's clauses (`benchmark.json → negative_controls`, `audit_has_teeth: true`).

## 7. Calibration against exhaustive ground truth (`small_n_tests/calibration.json`)

`run_small_n_calibration.py` decides, for `n = 2..7`, the *exact* number of legal
2n-sets (exhaustive over all 2-per-row configurations, which by Lemma 1 is
exhaustive for certificates) and the number invariant under each named group, then
requires the SAT encoders to agree:

- Formulation A: `SAT` for every `n = 2..7`, matching `D(n)=2n`.
- Formulation B: 48 instances; `status == SAT` **iff** the exhaustive invariant
  count is `> 0` in every case. Every SAT model was decoded back to a point set,
  re-verified for no-three-in-line by the round's own checker, and tested to
  actually possess the imposed symmetry.
- UNSAT controls: `at most 1 per row` with `2n` points forced is UNSAT
  (provable: rows are lines, `|S| ≤ n < 2n`); `rot4` at odd `n` is excluded by
  orbit parity.

**Bug this found:** the first draft of `orbit_feasibility` modelled the orbit-size
question as an *unbounded* coin problem, which wrongly declared `rot4` feasible at
`n = 3,5,7` by using the size-1 centre orbit twice. The SAT instances disagreed
(the solver returned UNSAT at `n=3,5,7`), and the disagreement localised the bug to
the pre-check. Fixed to a bounded knapsack. This is exactly the failure mode the
role is meant to catch: a *counting* shortcut that is not a valid counting proof.

## 8. Measured size of the objects (n=75, `benchmark.json`)

| quantity | value |
|---|---|
| maximal lines with ≥3 points | 1,336,828 |
| total line/cell incidences | 5,081,844 |
| longest line | 75 |
| lines encodable by explicit triple clauses | 1,336,088 |
| lines needing a cardinality network | 740 |
| estimated clauses, Formulation A | ~15.5 × 10⁶ |
| **built `rot2` instance (Formulation B)** | **1,648,125 vars, 36,418,316 clauses, 695 MB** |
| SHA-256 of that DIMACS | `2b47bce655ec925d…` (full value in `benchmark.json`) |
| build time | 140 s |

Comparison to prior art: the `wustep/maths` canonical-rct4 instance is
996,434 vars / 2,398,895 clauses. This bench's `rot2` instance is ~15× larger in
clauses, which is the expected cost of using a weaker (larger) symmetry group. The
instance is **not** committed to the repository (695 MB); it is reproducible from
`encoder.py` in about 140 s, and only its hash is recorded.

## 9. What is *not* claimed

- No `D(75) = 150`. The instance was built, not solved.
- No `D(75) < 150`. Nothing here produces, or could produce, that.
- No UNSAT is a theorem: this round produced **no DRAT/LRAT proof**, and no
  solver in this round was asked to emit one. Solver UNSAT without a checked trace
  is residue.
- No new literature result. The n=75 status is the published status, which this
  round independently re-verified from the database (§`../independent_verifier_r1/`).
