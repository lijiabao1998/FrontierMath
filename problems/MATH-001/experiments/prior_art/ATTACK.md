# Attack log — No-three-in-line at n=71

## 2026-08-16

- Environment created. Overnight quest. written: SAT-search 142 points on the $71\times 71$ grid, prefer
  rct4. No attack yet.

## 2026-08-16 — q1

- rct4 SAT on n=71: UNKNOWN (memory: commit 374e75b). CNF `n71-rct4.cnf` was generated but not recovered (too large; not in Add-File patches).
- Scripts recovered: `rct4_model.py`, `search_sat.py`, `search_cpsat.py`, `verify_n71.py`, `audit_dimacs.py`.

## 2026-08-16 — q2

- Continued SAT on the saved CNF; 20min UNKNOWN. Script: `long_sat_saved.py`.

## 2026-08-23 — q3: certificate shapes, ranked by cheapest first check

1. **Flammenkamp database certificate (outside this folder).** The finished
   object is the database-native rct4 code for Heule's 17 August 2026
   $n=71$ entry, a pinned decoder, the decoded 142-line coordinate file, and
   an exact replay log. It settles the case because a checked 142-set meets
   the row upper bound $D(71)\le142$. Cheapest check: fetch the single coded
   entry, decode its two column positions in each of 71 rows, and run the
   existing determinant checker. A database announcement alone is only a
   lead.
2. **Verifier gate for every claimed 142-set.** The finished object is a
   `run_all.sh` that feeds the same plain coordinate file to the committed
   Python triple-determinant checker and to a second checker in another
   language using primitive line normalization, then compares their point,
   row, and column counts. Agreement settles the computational part of any
   claimed construction; disagreement kills the claim. Cheapest check: run
   every already committed verifier before writing $D(71)=142$ anywhere.
3. **Honest `rot4` SAT — killed immediately.** The hypothetical finished
   object would be a 142-point quarter-turn-invariant coordinate file and the
   same verifier replay. It would settle $n=71$, but on an odd board every
   noncentral orbit has size four and the centre has size one, so its size is
   $0$ or $1$ modulo $4$, never $142\equiv2\pmod4$. The one-page orbit-count
   check kills this shape without a solver.
4. **Flammenkamp `rct4` SAT (the symmetry used at 65, 67, and 69).** The
   finished object is an audited DIMACS or direct CP-SAT model with the
   anti-diagonal empty, one selected half-turn pair on the main diagonal,
   35 selected four-orbits, and a decoded 142-set. It settles the case after
   the verifier gate. Cheapest check: regenerate the model, replay it first
   at $n=69$ against a published witness, and audit its orbit weights and
   DIMACS header before spending solver time at 71.
5. **Lift and perturb 69, 70, or 72.** The finished object is a 142-line
   coordinate file obtained by deleting or inserting boundary rows and
   columns in a published checked configuration, followed by a bounded local
   repair trace and the verifier replay. Any final checked file settles 71;
   the provenance does not. Cheapest check: replay the source witness, apply
   each monotone row/column map once, and count collinear triples and conflicted
   points. Kill a lift if its first image has no small repair support.
6. **`rot2` SAT, a named weaker symmetry.** The finished object is a
   half-turn-invariant 142-set, its exact encoding under 2-cycles, and the
   verifier replay. It would settle 71 while retaining more candidates than
   rct4. Cheapest check: construct the orbit/cardinality equations and solve
   small odd controls through $n=25$; proceed only if the encoding reproduces
   checked witnesses and its $n=71$ clause count fits memory.
7. **No imposed board symmetry: paired-row local search followed by SAT.**
   The finished certificate is again the plain 142-point file, with exactly
   two points in every row and column; a row-pair permutation supplies a
   compact search state, and SAT completes only the unresolved cells. It
   settles 71 only after the verifier gate. Cheapest check: seed from the
   best lifted 69/70/72 image and measure the exact number of violated maximal
   lines after one minute; abandon it if it does not beat the unperturbed
   lift.

## 2026-08-23 — q3 result

- Shape 1 ended the campaign. Flammenkamp's dated notes report that Marijn
  Heule found an rct4 solution for $n=71$ on 17 August 2026. A POST lookup of
  symmetry `c`, size 71, index 1 against the database cut of 19 August returned
  one 143-character code: one symmetry character and two columns in each of
  71 rows.
- `compute/q3/decode_database.py` decoded the pinned raw entry to
  `compute/n71-142.txt`. Re-encoding was not trusted as a geometry check.
- The previously committed `verify_n71.py` checked all 467,180 point triples
  by exact integer determinant. The independent Rust checker normalized the
  line through each of the 10,011 point pairs and found no duplicate line.
  Both checked 142 distinct points in the grid and exactly two in every row
  and column. Witness SHA-256:
  `690b7d94092a728dd0e6a2b3907ed0736e05d88c8c5a120e9735d8f9dca7b176`.
- Therefore $D(71)=142$. This is a replay of Heule's published database
  record, not a dent by this campaign. The same dated record now includes
  $n=73$, so the first current hole is $n=75$. Shapes 4–7 were not run after
  the certificate passed the verifier gate; honest `rot4` remains killed by
  the orbit-cardinality check.

## 2026-08-23 — q4: n=75 certificate shapes, ranked

The finished object in every surviving shape is a plain 150-point file on
$\{0,\ldots,74\}^2$ that passes two exact, algorithmically independent
verifiers. Working backwards from that object gives this order of attack:

1. **Current database certificate — checked and killed as a source.** A raw
   Flammenkamp code plus the existing decoder would be the cheapest route to
   a certificate. Both an unrestricted lookup and an rct4 lookup for size 75
   returned “no configurations are known” at the database cut of 19 August
   2026. This establishes only that this source has no witness, not that none
   exists.
2. **Canonical rct4 SAT.** The certificate has the anti-diagonal empty, one
   selected diagonal half-turn pair, and 37 selected four-orbits. The existing
   geometry generator, exact row and column equations, and weighted line
   constraints already express this shape. First replay the model and
   verifier at 71, then audit the generated $n=75$ instance and run several
   named Kissat seeds. SAT followed by the verifier gate settles $D(75)=150$;
   UNKNOWN or rct4 UNSAT does not.
3. **rct4 SAT phased from the checked n=73 configuration.** Embed the 146
   source points into a 75-grid in symmetry-preserving ways, translate the
   surviving orbit choices into initial SAT phases, and let the complete rct4
   instance repair them. The cheapest check counts violated maximal lines and
   retained source orbits for each embedding; only the best phases deserve
   solver time.
4. **Named rot2 SAT.** A 150-set can be exactly 75 half-turn pairs, so rot2
   has no orbit-cardinality obstruction and is weaker than rct4. The finished
   object is a half-turn-invariant point file decoded from an audited orbit
   model. The cheap gate is a control replay on a checked odd witness and a
   clause/memory count at 75.
5. **Boundary lift and bounded repair from n=73.** Place the checked 146-set
   into the 75-grid, add two new row pairs and two new column pairs, and expose
   only conflicted source points plus boundary candidates to SAT. A small
   repair support would yield a 150-set without imposing more symmetry than
   the source; a large initial conflict core kills this version of the shape.
6. **Two-per-row/column permutation SAT without board symmetry.** Represent
   the certificate as two permutations of the 75 columns, seed them from the
   checked 74- and 76-grid records, and use lazy line cuts or local search
   before a final exact SAT completion. This is the broadest credible shape,
   but it is ranked late because its model is much larger and a timeout leaves
   a less informative residue.
7. **Honest rot4 — killed by orbit cardinality.** On an odd grid a
   quarter-turn-invariant set has size $0$ or $1$ modulo 4 depending on the
   centre, never $150\equiv2\pmod4$. No solver run is warranted.

## 2026-08-23 — q4 partial result: smallest n=73 repairs exhausted

- Heule's database-native rct4 code at $n=73$ decoded to 146 points and passed
  all 508,080 exact determinant checks. Of the 37 symmetry-preserving ways to
  insert two empty coordinates, translation into rows and columns 1 through
  73 is uniquely cheapest: it retains 37 complete rct4 orbits and has no
  collinear triple.
- A direct addition is impossible because two points must be added to each
  empty boundary row and column, forcing the four corners, two of which lie on
  the fixed-empty anti-diagonal.
- `compute/q4/search_small_repair.py` then exhausted every row-and-column
  feasible repair that changes one or two selected seed orbits. It rejected
  all 144 one-orbit and all 23,536 two-orbit candidates by exact normalized
  lines. This is a finite residue around one seed, not a bound on rct4 and not
  evidence that $D(75)<150$.
- The corrected SAT encoder was replayed at $n=71$ by forcing all 36 orbits of
  the checked database witness. CaDiCaL returned SAT and decoded the identical
  coordinate file with SHA-256
  `690b7d94092a728dd0e6a2b3907ed0736e05d88c8c5a120e9735d8f9dca7b176`.
  This catches the inherited centre-row multiplicity bug that had previously
  prevented the wrapper from building an odd-order instance.
- At $n=75$, CaDiCaL 1.9.5 reported UNSAT in 206.69 seconds when the complete
  formula was restricted to retain at least 29 of the 37 seed orbits; the
  augmented formula had 996,666 variables and 2,399,380 clauses. This
  subsumes separate reported-UNSAT runs at minimums 30 through 34 and rules
  out repairs changing at most eight seed orbits only if the unproved solver
  result is trusted. No proof trace was produced, so the committed JSON is
  residue, not a certified exclusion and not a lower bound.

## 2026-08-23 — q4 result: precise rct4 wall

- The audited canonical-rct4 DIMACS has 996,434 variables, 2,398,895 clauses,
  5,577,130 literals, and SHA-256
  `1709cdf478920fd9ed0160bc5f00e049b10f0f6b28a1955560cd4aaa88205317`.
- The broadest near-seed slice required at least 28 of the 37 translated
  $n=73$ orbits. CaDiCaL 1.9.5 reported UNSAT after 499.31 seconds, 703,844
  conflicts, and 2,067,436,821 propagations. This subsumes the recorded
  minimums 29 through 34, but no proof trace was produced; it is solver
  residue, not a certified exclusion.
- The full phased Glucose 4.2 run returned `UNKNOWN` after 1,350.15 seconds,
  1,011,446 conflicts, and 11,425,221,379 propagations. The two full CaDiCaL
  seeds did not return from PySAT's requested 1,500-second interrupt. They
  were stopped externally at 13:41:04 PDT after measured process elapsed
  times of 1,653 and 1,621 seconds; both exited 143 without a model or final
  solver statistics. `compute/q4/hard-wall.json` records those observations.
- No 150-point certificate was found. This campaign therefore leaves residue:
  it does not prove rct4 impossible, and it gives no inequality for $D(75)$.
