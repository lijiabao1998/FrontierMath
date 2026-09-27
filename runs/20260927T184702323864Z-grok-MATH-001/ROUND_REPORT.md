# ROUND REPORT｜MATH-001｜20260927T184702323864Z-grok-MATH-001

- repo／branch：FrontierMath `grok/MATH-001-baseline-r1`（base `cd1e4eadc177920b95332ebe08c2498e52c3ce56`）
- governance pin：`07d2b13051b83215182e411e1612f92f1912d8fb`（worktree `_grok/gov-07d2b13`，沒有改鎖到治理 repo 的 `1ead143`）
- verdict：**PARTIAL_PROGRESS**。輪次 FINISHED。問題仍 OPEN。
- 預算：0 美元；wall 凍結 120 分；試驗 29 批（搜索 9、tamper 1、下載與檔案 18、表再抓 1）。另有一次解碼器修正後的重跑，沒有另開 round。

## 文獻

四路檢索在 `start` 之後重做，紀錄在 `LITERATURE_MAP.md`。沒有同 scope 的一般證明或反例。

- 有限 frontier 以 Flammenkamp `table.html`（2026-09-11）為準：n=75 那一列是空的，n=76 有一個構造，n<=74 除 75 外至少有一個。署名在 Heule 與 Prellberg，不是本輪的發現。
- arXiv:2602.07751 只有 v1，Theorem 1 停在 n<=60。arXiv:2607.05255 明示只解決 k>=3。棋盤變體與立方體計數都不關父問題。
- 沒有找到 2n 存在性的撤稿。Flammenkamp 自己的 Corrections 只改 1992 年計數（n=30 rot4：62→92，n=32：99→101，n=20 的 rot2 欄：693→675）。Guy–Kelly 常數修正（arXiv:2603.00215）是啟發式，不是定理。
- Wikipedia 仍寫 n<=70，OEIS A000769 註記仍寫 n<=60。以原始表為準。
- 實驗結束前再抓表，SHA256 與 preflight 相同。

## 檢查器

兩份程式不互相 import。

- `verifier_det.py`：有號整數行列式。
- `verifier_lines.py`：約分後的方向加 `dx*y-dy*x`。同一 session 寫的，**不是**另一位 reviewer 的獨立簽署。
- 不一致就停。本輪沒有不一致。

自製搜索是確定性的，沒有 seed。n=2..10 都找到一張 2n 憑證，兩套都通過。n=9：306125 個 DFS 呼叫，7.62 秒。時間或節點上限內找不到，只會記 `time_limit`／`node_limit`，不會記成反例。n=1 的單點沒有三點共線，但不是 2n 憑證。

負例：n=2 的四點正方形通過；對角線、斜率 2、負斜率、重複、0、越界、浮點都拒絕。從自製憑證注入格點上的第三點，8 次都拒絕。seed=42 的 240 個單點亂改，兩套 reason 都相同。

## 公開構造

資料不進 git。SHA256：

- `data_1997/known_solutions` `5e127d7be1c060a4d9021356b14848661fac8b76efee45c79acba5b7b7cd80f4`（1654852 bytes）
- `download/all_known_solutions` `c27f8f53286be5b047a46bf1e469985e44efd4e6955783e8d0fb5ad66b7effde`（23834242 bytes，目錄時間 2026-08-31）

1997 檔 36912 筆，兩套檢查器都通過，66 秒。

`configurations/` 裡 n>=61 的 `.few`：n=61 到 74，以及 76，沒有 75。修正解碼器之後 65 筆全部兩套通過，包含 Heule 的 `n76_rot4.few` 與 Prellberg 的 `n74_rot4.few`。點列在 `results/grok_r1/public/n76_rot4_points.json` 與 `n74_rot4_points.json`。

`all_known_solutions` 431008 筆都解得出來。直線檢查器：第一遍 412675 筆（涵蓋 n<=53 以及 n=54 的前段）0 失敗；補上全部 7714 筆 n=54，0 失敗；n>=55 的 12007 筆 0 失敗。沒有 n=75。n>=61 的筆數與 `.few` 逐 n 相同，而 `.few` 已用行列式全查。n=11..53 的行列式只查了 n<=10 的全部、每 25 筆一張，以及 1997 檔的全部。

## 解碼器抓到的錯

第一遍把 `@` 當成 1995 年 `decode.c` 的格式旗標。2026-07-12 的 `char_to_val` 裡 `@` 是索引 66。於是 n=70、71、73、74、76 等被記成 decode failure，而不是數學失敗。`summary.json` 留著這次結果。去掉這個判斷後 `recheck_public.py` 全過。

不要再犯：`'a'` 的索引是 36，不是 10。1995 年 `decode.c` 的 `MAX_N 62` 不能解擴充字母。

## 沒做成

- 沒有一般證明或反例。有限憑證每個 n 只證明那個 n 的 `D(n)=2n`。
- 沒有 Heule 的 DRAT/LRAT。公開的是 Flammenkamp 編碼，不是 SAT 證書。
- 沒有逐行審 2602.07751 的 16 頁，也沒有重現 Hall–Jackson–Sudbery–Wild 的 `(3/2-ε)n`。
- 沒有新 Lean 定理。`lake build` 本輪 NOT_RUN。
- 沒有讀、沒有改 `glm/MATH-001-baseline-r1`。PR #2 仍開著。
- 官方 `check_validity` 用 unsigned。座標 < 90 時與有號式同值；本輪沒有編譯那份 C，不以它為檢查器。

## 下一輪最小動作

為 n=75 寫 SAT/CSP，先用 n<=10 的已知憑證校準編碼，再跑。若 UNSAT，必須留下可檢查證書。沒有證書就只記「這次搜索沒找到」。

## 重跑

```text
py -3 problems/MATH-001/experiments/grok_r1/run_round.py
py -3 problems/MATH-001/experiments/grok_r1/recheck_public.py
```

大型檔在 `experiments/grok_r1/data_cache/`，被 gitignore。刪掉後這兩條命令會重新下載。
