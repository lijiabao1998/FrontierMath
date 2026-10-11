# Independent protocol review before computation

Reviewer: separate read-only `independent_review` session, 2026-10-11 UTC. No research computation or reference main was run by the reviewer.

The reviewer checked the pinned governance, both protocols and source snapshots. All 4 Math and 6 Physics snapshots matched their recorded SHA256 and byte counts. Static source observations included r1 deduplication before closure testing and V1 flags absent from `ok`; these were hypotheses awaiting the dynamic audit at this stage.

First-pass requests were incorporated before freezing: exact named family/universe control inputs, empty/missing/error rejection, exact signal formulas, sine coefficient sign and mutation-sensitive fixtures. All imported top-level/main behavior was replaced with whitelisted reviewed AST function definitions.

Second-pass requests were incorporated before freezing: independent fixed aggregate check names; exact m=1,2,3,4 coverage and 65,812 candidate count; per-m required-check coverage. The V1 projection now copies the original `main` Return.value AST, alongside the original verdict assignment. It explicitly assumes other stages pass and does not rerun the full original main.

The reviewer found the direct-set uniqueness/empty-union/integer checks, all-candidate closure comparison, signed DFT/Parseval checks, mixed/sine sensitivity and poisoned-amplitude reference fixtures within this bounded scope. This is independent static protocol/code review, not an independent experimental rerun. Post-run review is recorded separately.
