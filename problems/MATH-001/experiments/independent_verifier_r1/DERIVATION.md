# MATH-001 Certificate Spec — Independent Derivation (DeepSeek, r1)

Author: DeepSeek (verifier role). Written **before** reading any GLM verifier code.
Purpose: state, from the frozen problem card alone, what counts as a valid
`D(n) = 2n` certificate and what a checker must therefore establish.

Source of the statement (read first, verbatim from `problems/MATH-001/problem.json`):

> 令 D(n) 為 {1,...,n}² 中任三相異點不共線的最大子集大小。研究對所有 n>=2 是否
> D(n)=2n，或給出嚴格反例／一般界。

---

## 1. Definitions fixed from the statement

- **Grid**: `G(n) = {1,...,n} x {1,...,n}` ⊂ Z². Note `1..n`, not `0..n-1`.
  The grid is *stated* 1-indexed, so a certificate submitted to this card must be
  1-indexed. (Collinearity is translation invariant, so a 0-indexed set that is
  shifted by +1 is an equivalent valid configuration; but a checker enforcing the
  card must reject raw 0-indexed input and accept only the shifted form — or
  normalise and say so. See §5 "convention traps".)
- **Collinear triple**: three *distinct* points `p,q,r` are collinear iff
  `det[[x1,y1,1],[x2,y2,1],[x3,y3,1]] = 0`, i.e.
  `(x2-x1)(y3-y1) - (x3-x1)(y2-y1) = 0`. All quantities integer; no division.
- **Legal set**: `S ⊆ G(n)` such that no three distinct points of `S` are collinear.
- **Certificate for `D(n) = 2n`**: a legal set `S` with `|S| = 2n`.

## 2. The 2n upper bound — derived, not assumed

Claim: for every `n ≥ 1`, `D(n) ≤ 2n`.

Proof. For `j ∈ {1..n}` let `R_j = {(x,j) : x ∈ {1..n}}` be the j-th *row*. Each
`R_j` is contained in the affine line `y = j`, hence any three points of `R_j` are
collinear. Therefore a legal `S` satisfies `|S ∩ R_j| ≤ 2` for every `j`. The `R_j`
partition `G(n)`, so `|S| = Σ_j |S ∩ R_j| ≤ 2n`. ∎

Consequences a checker must respect:
- The bound uses **rows**. It equally holds for columns by symmetry, but the
  argument as written is row-based; either is fine, both give `2n`.
- The bound is **independent of any construction**. So a verified certificate with
  `|S| = 2n` yields `2n ≤ D(n) ≤ 2n`, i.e. `D(n) = 2n` **for that n**, exactly.
- The bound gives `D(n) ≤ 2n` but says nothing about whether the bound is attained.
  A certificate is exactly the missing half.

⚠ **Scope limit that must never be blurred**: `D(n) = 2n` proved for a *finite set
of n* is a finite statement. It does **not** imply `D(m) = 2n` for other m, and it
does **not** imply the general conjecture `∀n≥2, D(n) = 2n`. Any document that
presents "certificates for n = 2..10" as progress on "*the* no-three-in-line
problem" in the sense of resolving it is committing a scope transfer.

## 3. An exact, division-free characterisation of legality (my primary checker)

The textbook test enumerates all `C(|S|,3)` triples and evaluates a determinant.
I use a **different** equivalent characterisation, chosen deliberately so that this
checker shares no algorithmic structure with a determinant-enumeration checker.

**Canonical line of a pair.** For distinct points `p=(x1,y1)`, `q=(x2,y2)` set
```
A = y2 - y1,  B = x1 - x2,  C = x2*y1 - x1*y2        (integers)
```
Then `A*x + B*y + C = 0` is the unique line through `p` and `q` (verify:
`A*x1+B*y1+C = (y2-y1)x1 + (x1-x2)y1 + x2y1 - x1y2 = x1y2 - x1y1 + x1y1 - x2y1 + x2y1 - x1y2 = 0`;
similarly for `q`). Let `g = gcd(|A|,|B|,|C|)` (with `gcd(0,0)=0`), divide by `g`,
then multiply the triple by `-1` if the first nonzero entry is negative. Call the
result `L(p,q)`; it is a canonical form: `L(p,q) = L(r,s)` **iff** the two pairs span
the same affine line.

**Theorem (legality ⟺ pair-line injectivity).** `S` is legal ⟺ the map
`{unordered pairs of distinct S} → lines`, `{p,q} ↦ L(p,q)`, is injective.

Proof.
(⟸) Suppose `S` illegal: there are distinct collinear `p,q,r ∈ S`. Then `{p,q}` and
`{p,r}` are distinct pairs spanning the same line, so `L(p,q) = L(p,r)`. Not injective.
(⟹) Suppose not injective: distinct pairs `{p,q} ≠ {r,s}` with `L(p,q) = L(r,s) = ℓ`.
The union `{p,q} ∪ {r,s}` has either 3 or 4 elements (3 when the pairs share one
point), and all of its elements lie on `ℓ`. Any 3 distinct elements of that union are
three distinct collinear points of `S`. So `S` is illegal. ∎

Why this matters for verification: it converts an `O(m³)` all-triples scan into an
`O(m²)` exact-integer hash with an *equivalence proof*, and — more importantly —
it is a **structurally different implementation**, so a shared bug with a
determinant-triple checker is unlikely. `m = |S| = 2n`, so `C(m,3) ≈ 1.3e6` at
`n = 75` versus `C(m,2) = 11175` pairs.

## 4. Second, arithmetically different checker (rationals)

To guard against a bug in the gcd/sign normalisation of §3, a second implementation
groups pairs by **exact rational slope and intercept** using `fractions.Fraction`
(arbitrary-precision rationals, a different arithmetic path):

- if `x1 ≠ x2`: `m = Fraction(y2-y1, x2-x1)`, `b = Fraction(y1*x2 - y2*x1, x2-x1)`; key `(m, b)`.
- if `x1 = x2`: key `('V', x1)`.

Same injectivity criterion. Keys are hashable and exact.

A third, deliberately naive **determinant triple scan** is included and used only as
a cross-check on small instances, so that the two fast checkers are themselves
validated against the definition.

## 5. Convention traps a checker must survive (explicitly enumerated)

| # | Trap | Correct handling |
|---|---|---|
| T1 | `{1..n}` vs `{0..n-1}` indexing | Statement says 1..n. Reject out-of-range; report which index base the input appears to use. |
| T2 | Row vs column as the outer loop of a pair-per-line encoding | Rows are `y`; a pair `(c1,c2)` is `(c1, row)` and `(c2, row)`. Transposing the grid maps legal sets to legal sets, so a pure transpose is *not* a validity error — but it changes which points are named, so certificates must declare orientation. |
| T3 | Lowercase char mapping (`'a' → 36`, not 10) | Flammenkamp's `TOPOS` macro: digits `'0'-'9' → 0-9`; `'A'-'Z' → 10-35`; `'a'-'z' → 36-61`. Mapping `'a'` to 10 collides with `'A'`, silently OK for `n ≤ 36` and catastrophic above. |
| T4 | Symmetry-class prefix char | Each data line begins with one of `.:/-xo+*c`; it is a label, not coordinates. |
| T5 | Duplicate points inflating the count | `|S|` must be the cardinality of the *point set*, not the number of listed rows. |
| T6 | Counting a 4-collinear as two triples | Pair-line injectivity handles it uniformly; triple scans must not "dedupe" violations and then pass. |
| T7 | `2n` count must be checked against `n`, not against the input length | A file of 10 points can be a `2n` certificate for `n=5` and a lie for `n=6`. |
| T8 | Empty / `n=1` edge | `D(1) = 1` (whole grid `{(1,1)}`), so `2n = 2 > 1`: **`D(1) = 2n` is FALSE**. Any claim of a `2n` certificate at `n=1` is necessarily invalid. |
| T9 | Float coordinates or floats in arithmetic | All arithmetic must be integer/rational. `1e16`-scale floats lose exactness; reject non-`int` and non-`Fraction` coordinates. |

## 6. What a checker must NOT claim

- A checker that accepts a certificate proves `D(n) = 2n` **for that single n**.
- A checker that rejects nothing does not prove `D(n) < 2n`; absence of a
  certificate is a search result, not a proof. Only an **UNSAT certificate**
  (independently verifiable, e.g. DRAT/LRAT) would prove `D(75) < 150`.
- Solver `s UNSAT` without a checkable proof is `COMPUTE_REQUIRED`-grade evidence.
- Solver `s UNKNOWN` / timeout is **not** UNSAT.

## 7. Independent reproductions claimed by this round

1. Exact `D(n)` for small `n` by exhaustive enumeration (no reliance on §2's bound
   for `n ≤ 4`; the bound is used for `n ≥ 5` only to bound the search, and the
   exhaustive enumeration is over *all* point subsets up to that bound).
2. Re-verification of the r1 self-certificates `n = 2..10`.
3. Independent decode + verification of Flammenkamp's `known_solutions` corpus,
   with the decode mapping validated *by the mathematics* (a wrong mapping
   destroys legality), not by trusting a reading of `decode.c`.
4. Adversarial negative and positive controls, including fuzz.
