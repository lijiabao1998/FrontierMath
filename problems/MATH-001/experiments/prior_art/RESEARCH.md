# Research log — No-three-in-line at n=71

## 2026-08-16

- [Prellberg, arXiv:2602.07751](https://arxiv.org/abs/2602.07751) — D(n)=2n for n≤60.
- Heule 2026 / Flammenkamp database — 2n for n=65,67,69,70,72,76; Prellberg n=74. n=71 is the first hole.
- q1/q2: rct4 SAT UNKNOWN. CNF not recovered.

## 2026-08-23

- Fetched and read [Prellberg, arXiv:2602.07751v1](https://arxiv.org/abs/2602.07751)
  and its [HTML full text](https://arxiv.org/html/2602.07751v1) before reusing
  any model count. The paper proves $D(n)=2n$ through 60, defines the odd
  symmetry as four-orbits off the diagonal and half-turn pairs on it, reports
  812 variables and 118,241 constraints at $n=57$, and documents a
  384-independent-run CP-SAT protocol. Its implementation link is
  [ThomasPrellberg/no-three-in-line---CP-SAT](https://github.com/ThomasPrellberg/no-three-in-line---CP-SAT).
- Fetched the current [Flammenkamp no-three-in-line database notes](https://wwwhomes.uni-bielefeld.de/achim/no3in/readme.html),
  dated 19 August 2026. They record Heule's rct4 solutions at 65, 67, and 69,
  his rot4 solutions at 70 and 72, and, critically, his first rct4 solution
  for $n=71$ on 17 August and first rct4 solution for $n=73$ on 19 August.
  Thus the 16 August statement that 71 was the first hole had become stale;
  the first current hole is 75.
- The database documents its extended alphabet in
  [`encoding`](https://wwwhomes.uni-bielefeld.de/achim/no3in/encoding) and its
  historical decoder in [`decode.c`](https://wwwhomes.uni-bielefeld.de/achim/no3in/decode.c).
  A POST lookup with `symm=c`, `size=71`, `index=1` returned the raw code pinned
  in `compute/q3/n71-rct4.code` from the database cut of 19 August 2026.
- Exact replay: 142 distinct in-grid points; every row and column has two;
  467,180 determinants and 10,011 independently normalized pair-lines checked;
  no collinear triple. This verifies $D(71)=142$ but does not improve the
  published record.
- Refreshed the live [Flammenkamp database notes](https://wwwhomes.uni-bielefeld.de/achim/no3in/readme.html)
  before starting $n=75$. The page remains dated 19 August 2026 and records
  Heule's rct4 solutions at 71 and 73, but no solution at 75. Both an
  unrestricted POST and an rct4 POST to the documented
  [lookup endpoint](https://wwwhomes.uni-bielefeld.de/cgi-bin/cgiwrap/achim/script_lookup?para=FIXED)
  with `size=75`, `index=0` returned “no configurations are known” and the
  same database cut date. Thus 75 remains the first current hole as of this
  check; the database response is a search-status source, not an impossibility
  result.
