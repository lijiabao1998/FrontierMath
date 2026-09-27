# Provenance: primary sources used by this round (DeepSeek r1)

All third-party inputs were **re-downloaded from source** by this round (not copied
from a sibling branch) and hash-compared against the copies already committed by GLM
r1. All three matched byte-for-byte, which is itself the provenance result.

| file | URL | bytes | SHA-256 |
|---|---|---|---|
| `known_solutions_1997.txt` | https://wwwhomes.uni-bielefeld.de/achim/no3in/data_1997/known_solutions | 1,654,852 | `5e127d7be1c060a4d9021356b14848661fac8b76efee45c79acba5b7b7cd80f4` |
| `decode.c` | https://wwwhomes.uni-bielefeld.de/achim/no3in/decode.c | 2,324 | `4ef26ee8adda3543e19ce5ab75383b33f80365e3a013bbcac64fa9dbff5022db` |
| `readme.html` | https://wwwhomes.uni-bielefeld.de/achim/no3in/readme.html | 34,559 | `efc0b3c2ad60e00a6ba11e197e7e1e929d833a9222f59ef20d6eb75b9e259156` |
| `all_known_solutions` (**not vendored**) | https://wwwhomes.uni-bielefeld.de/achim/no3in/download/all_known_solutions | 23,834,242 | see `small_n_tests/all_known_solutions_verification.json` (`lines_read` 431,008) |
| `table.html` | https://wwwhomes.uni-bielefeld.de/achim/no3in/table.html | 9,396 | the authoritative count table |
| `encoding` | https://wwwhomes.uni-bielefeld.de/achim/no3in/encoding | 734 | extended alphabet, indices 0..89 |
| live lookup endpoint | https://wwwhomes.uni-bielefeld.de/cgi-bin/cgiwrap/achim/script_lookup?para=FIXED (POST `symm`,`size`,`index`) | — | database cut date 2026-08-31 |

Upstream pages state no licence in the fetched material. The 1.65 MB and 23.8 MB
corpora are therefore **not** committed by this branch; fetch them from the URLs above
and verify the hashes. `known_solutions_1997.txt`, `decode.c` and `readme.html` are
already present in GLM's r1 commit and are not re-added here.

Reproduce the frontier retrieval:

```bash
# path A: coded entries from the database file
python cross_check_database.py --n 76 --symm o --index 1
# path B (same script): the ASCII grid rendered by the live endpoint; the script
# reports paths_agree=True only when both paths decode to the identical point set.
```
