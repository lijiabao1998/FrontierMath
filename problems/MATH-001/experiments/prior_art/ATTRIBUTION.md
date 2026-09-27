# Attribution

The two logs in this directory are quoted from a third-party repository, redistributed
here under the terms of its licence.

## `RESEARCH.md`, `ATTACK.md`

- Source: https://github.com/wustep/maths
- Paths upstream: `problems/three-in-line/RESEARCH.md`, `problems/three-in-line/ATTACK.md`
- Retrieved: 2026-09-28 from `https://raw.githubusercontent.com/wustep/maths/refs/heads/main/problems/three-in-line/`
- Licence: **MIT** (`gh api repos/wustep/maths/license` → `spdx_id: MIT`)
- Reason kept: direct prior art for the n=75 attack. It is what establishes that a
  canonical-rct4 DIMACS for n=75 already exists (996,434 variables / 2,398,895
  clauses), that its restricted-UNSAT runs produced **no proof trace** and were
  recorded as residue, and that Heule's n=71 record was already replayed and verified
  by a third party before this round.

### MIT Licence

```
MIT License

Copyright (c) 2026 Stephen Wu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

Vendor path (for reference, hashes not recorded this round):
`https://raw.githubusercontent.com/wustep/maths/refs/heads/main/problems/three-in-line/{RESEARCH,ATTACK}.md`

Note: the Flammenkamp material used by this branch is handled the *opposite* way,
because no licence was found for it — see `../lit_data/THIRD_PARTY_SOURCES.md`.
