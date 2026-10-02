# HANDOFF｜MATH-001 grok r1

- repo：`C:\Users\Leon1\OneDrive\Desktop\前沿RP\_grok\FrontierMath`
- branch：`grok/MATH-001-baseline-r1`
- base SHA：`cd1e4eadc177920b95332ebe08c2498e52c3ce56`（origin/main 在開工時）
- problem：MATH-001，狀態 OPEN
- round：`20260927T184702323864Z-grok-MATH-001`，state FINISHED，verdict PARTIAL_PROGRESS
- governance pin：`07d2b13051b83215182e411e1612f92f1912d8fb`。不要把 `GOVERNANCE.lock.json` 改成治理 repo 現在的 HEAD。
- 治理工具要從這個 pin 跑：`前沿RP\_grok\gov-07d2b13\tools\frontier.py`
- 原 FrontierMath 工作目錄停在 `glm/MATH-001-baseline-r1`，不要在那裡提交。

## 讀過的原始來源

- https://wwwhomes.uni-bielefeld.de/achim/no3in/readme.html （年表、編碼、Corrections）
- https://wwwhomes.uni-bielefeld.de/achim/no3in/table.html （全文；2026-09-11）
- https://wwwhomes.uni-bielefeld.de/achim/no3in/encoding 與 `download/no3in_functions.h`（2026-07-12_14:40）
- https://arxiv.org/abs/2602.07751 v1 only；HTML Theorem 1 與結論。PDF 未逐行審。
- https://arxiv.org/abs/2607.05255 abstract。k>=3，排除 k=2。
- https://arxiv.org/abs/2605.09215 abstract。棋盤變體。
- https://arxiv.org/abs/2609.25133 abstract 與引言前段。立方體／計數。
- https://arxiv.org/abs/2603.00215 abstract 層級。Guy–Kelly 常數。
- `download/configurations/n76_rot4.few` 與 n=61..74 的 `.few` 已下載並重驗。

## 查詢

見 `LITERATURE_MAP.md` 的表。引擎是 web search、export.arxiv.org API、以及對上述 URL 的 HTTPS GET。

## 命令

```text
py -3 ..\gov-07d2b13\tools\frontier.py validate .
py -3 ..\gov-07d2b13\tools\frontier.py start . MATH-001 --agent grok
py -3 ..\gov-07d2b13\tools\frontier.py admit . runs\20260927T184702323864Z-grok-MATH-001\round.json
py -3 problems\MATH-001\experiments\grok_r1\run_round.py
py -3 problems\MATH-001\experiments\grok_r1\recheck_public.py
```

後兩條在修正 `@` 之前／之後各有一次。`run_round.py` 的 1997 全檔與 n=2..10 搜索不必為了 n=75 再跑。

## 改過的檔

- `problems/MATH-001/problem.json`：known_result、first_task、screening、sources。statement／completion_criterion／evaluator 沒改。
- `problems/MATH-001/experiments/grok_r1/*.py`
- `problems/MATH-001/results/grok_r1/**`
- `STATUS.md`、`README.md` 交付邊界、`runs/README.md`
- 本輪 `round.json`、`LITERATURE_MAP.md`、`ROUND_REPORT.md`、`HANDOFF.md`

## 檢查器狀態

兩套在已報告的正例上 PASS，在故意負例上 FAIL。1997：36912/36912。`.few`：65/65。

`all_known_solutions` 的全量是 `full_scan.py`，git `7561485`，凍結 `2026-10-02T14:28:30Z`。431008/431008，兩套檢查器，exit 0。n=54 是 7714，0 失敗。沒有 n=75。第一遍 `run_round.py` 的 412675 筆 `time_limit` 不是這次全量。

`@` 失敗仍在 `summary.json`。產生它的 `decode_flam.py` 是 `fdfc81c934b9b3f059324b47986453f0f44fb61e72852776ac804a88d154d65d`，記在 `run1_binding.json`。不要用後來的程式 hash 回填。

## 不要再做

- 不要把 `@` 當格式旗標。它是索引 66。
- 不要把 `'a'` 編成 10。索引是 36。
- 不要用 1995 年 `decode.c`（MAX_N 62）解 n>62。
- 不要把某個 n 的 2n 憑證寫成一般定理。
- 不要把「沒搜到」寫成 D(n)<2n。SAT 的 UNSAT 要有可檢查證書。
- 不要改 glm 分支，不要合 main，不要 force push。
- 不要把同一 session 的第二份程式簽署成獨立覆核。
- 不要把資料檔 `known_solutions` / `all_known_solutions` 放進 git。SHA256 在 `results/grok_r1/hashes.txt`。

## 下一條命令

新開一輪，不要續用這個 round id：

```text
py -3 ..\gov-07d2b13\tools\frontier.py start . MATH-001 --agent grok
```

然後只做 n=75 的編碼校準。先用 `results/grok_r1/self/self_n02.json` 到 `self_n10.json` 確認編碼會 SAT，再碰 75。
