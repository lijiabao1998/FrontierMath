# LITERATURE MAP｜MATH-001｜20260927T184702323864Z-grok-MATH-001

檢索開始於本輪 `started_at` 之後（2026-09-27T18:47:02Z）。這是有界檢索，不是全網已讀完的證明。快取 HTML／C 在 `runs/.../lit/`，不進 git。

## 題卡 scope

`D(n)` = `{1,...,n}^2` 中無三點共線的最大子集。問的是：是否對所有 `n>=2` 都有 `D(n)=2n`，或給出同範圍的嚴格反例／一般界。有限 n 的構造只提升有限下界。

`origin/main` 題卡 `known_result` 只寫到 Prellberg 2026 的 `n<=60`。

## 查詢

| category | engine | query | outcome |
|---|---|---|---|
| general | web search | `no-three-in-line problem D(n)=2n open status 2026` | 問題仍被標成 unsolved。有限構造已超過題卡的 n≤60。 |
| discipline | web search | `site:arxiv.org no-three-in-line Prellberg 2026` | 命中 2602.07751（古典，n≤60）與 2605.09215（棋盤變體）。 |
| discipline | export.arxiv.org API | `all:"no-three-in-line"` sort submittedDate desc, max 25 | 近期同名論文沒有一篇宣稱一般 `D(n)=2n` 已證或已有反例。 |
| solution | web search | `"no-three-in-line" Heule SAT n=75 OR n=76 OR solved OR counterexample 2026` | Heule／Prellberg 的有限紀錄出現在 Flammenkamp 頁與 MathWorld。沒有一般反例。 |
| solution | HTTPS GET | `https://wwwhomes.uni-bielefeld.de/achim/no3in/readme.html` 與 `table.html` | 原始年表與計數表。 |
| criticism | web search | `"no-three-in-line" erratum OR retraction OR corrigendum OR "failed to reproduce" Prellberg OR Heule OR Flammenkamp` | 沒有找到針對 2n 存在性證明的撤稿。命中的是 Guy–Kelly 啟發式常數的舊錯誤。 |
| criticism | HTTPS GET | Flammenkamp readme「Corrections to published Data」 | 1992 年計數表的更正，不是存在性撤稿。 |
| discipline | HTTPS GET | `download/`、`download/README`、`encoding`、`download/configurations/` | 公開編碼與 n=76 等小檔。 |

## 讀了什麼

### 原始來源

- Flammenkamp readme，`https://wwwhomes.uni-bielefeld.de/achim/no3in/readme.html`。讀了問題陳述、主猜想連結、1996 之後的編碼說明、2026 年表（至 2026-08-19 的 n=73）、以及 Corrections 節。不是 1992 以前每條參考文獻都打開。
- Flammenkamp table，`https://wwwhomes.uni-bielefeld.de/achim/no3in/table.html`。全文讀完。頁尾寫 last updated **11 September 2026**。圖例：數字＝該對稱類已完整計數；`.`＝恰有一個已知構造；`..`＝有一些已知構造；空白＝沒有記入。
- 編碼頁 `encoding` 與 `download/no3in_functions.h`（版本字串 `2026-07-12_14:40`）、`no3in_functions.c` 的 `char_to_val`、`decode`、`check_validity`。這是資料格式，不是定理。
- `download/README`（目錄時間 2026-08-31）與 `configurations/` 索引。
- `download/configurations/n76_rot4.few` 整行讀完。檔案時間 2026-08-10，154 bytes。
- Prellberg, arXiv:2602.07751。abs 頁只有 **v1**（2026-02-08）。HTML 讀到 Theorem 1（`2<=n<=60` 則 `D(n)=2n`）和結論（作者寫當時最小未定從 47 升到 61；n=61、62 在 10^7 秒內沒找到）。沒有逐行審 16 頁 PDF。補充資料指向 `https://github.com/ThomasPrellberg/no-three-in-line---CP-SAT`。Kudriashov 2609.25133 寫此文 “J. Combin. Theory Ser. A, to appear”；本輪沒有看到勘誤版。
- arXiv:2607.05255v1，No-(k+1)-in-line for `k>=3`。讀 abstract。它寫明 k=2 就是尚未解決的 no-three-in-line，而他們證明的是 k≥3、n 夠大時最大值恰為 `kn`。
- arXiv:2605.09215v2 abstract。棋盤單色變體。摘要寫古典問題是否總能達到 `2n` 仍 open。
- arXiv:2609.25133v1 abstract 與引言前段。立方體 no-three-in-line、共面四點、Guy–Kelly 計數審計。不是平面一般 `D(n)=2n`。引言裡「資料庫到 n=57」與 2026-09-11 的表不一致，以表為準。文中說撤回過的宣稱留在正文裡。
- arXiv:2603.00215 abstract 層級。Guy–Kelly 1968 啟發式推導有錯，修正後常數約 `π/√3 ≈ 1.814`。這是猜想常數的更正，不是 `D(n)=2n` 的證明或反例。

### 二手來源（不當成 frontier 的主證據）

- Wikipedia `No-three-in-line problem`（抓取當下）。頁首仍標 unsolved。正文數學寫的是 `n≤70` 時 `2n` 已知達到。這比 2026-09-11 的原始表舊。
- MathWorld `No-Three-in-a-LineProblem`。紀錄表列到 Heule n=76、Prellberg n=74、Heule n=71 與 n=73。句子裡「除了某個 n」的那個數字在文字抽取裡掉了，本輪不從這頁宣稱那個缺號。
- Epoch AI 的 no-three-in-line 頁（搜尋摘要）。他們要的是勝過 `(3/2)n` 的無限族；並寫 `n≤70` 已緊。那是另一個形式化，而且有限範圍舊於原始表。
- OEIS A000769 internal 頁（搜尋摘要，2026-07-19 編輯）仍寫至少 n≤60 有解。舊。

## 有限 frontier（以 2026-09-11 的表為準）

- `n=75` 那一列只有列號，沒有數字也沒有 `.`／`..`。
- `n=76` 有一個已知構造（`o` 欄，四分之一旋轉；檔名 `n76_rot4.few` 與此相符）。
- `n=61` 到 `n=74` 以及 `n=76` 至少有 `.`。所以表上記入的最小空白階是 **75**，最大已記入構造是 **76**。
- 年表署名：n=71、73、76 是 Marijn Heule（SAT）；n=74 是 Thomas Prellberg（2026-07-20，rot4）；n≤70 的補齊見 readme 2026-06 條目。這些不是本庫的發現。
- `configurations/` 索引裡有 `n70_rot4`、`n71_rct4`、`n72_rot4`、`n73_rct4`、`n74_rot4`、`n76_rot4` 的 `.few`。沒有 n=75 檔。
- `download/all_known_solutions` 23834242 bytes，時間 2026-08-31。`data_1997/known_solutions` 1654852 bytes。1997 檔不是 2026 的 frontier。

## 一般問題

沒有找到與題卡同 scope 的證明或反例。

- 上界 `2n` 仍只是鴿籠（每行至多兩點）。達到 `2n` 就證明該 n 的 `D(n)=2n`，不能外推到所有 n。
- 最好的一般下界仍是 Hall–Jackson–Sudbery–Wild 1975 的 `(3/2-ε)n`。本輪沒有重現這個構造。
- Guy–Kelly 啟發式（修正後約 `1.814n`）是猜想，不是定理。Flammenkamp 對 full／ort2 對稱類的 near-miss 計數只是那些對稱類的經驗，而且他寫猜想 III 已在 1996 年被否定。
- `k≥3` 的解決明確不覆蓋 `k=2`。

判定：**PARTIAL_PROGRESS**。更新有限已知結果；父問題保持 OPEN。不是 `CLAIMED_RESOLVED`，也不是 `RESOLVED_EXTERNAL`。

## 編碼，避免再踩的坑

- 現行字母（90 字元）是 `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz#$%&@?!()[]<>{}=*+|-/~^_:;,.`。`'a'` 的索引是 36，不是 10。
- 1995 年以前的 `decode.c` 只處理到 `'z'`（`MAX_N 62`），對擴充字母的 else 分支會得到 -1。不能用它解 n>62。
- 座標是 0-based：每個 row `y = h//2` 兩個 column。題卡用 `{1,...,n}`，驗證前要平移並寫明。
- 對稱字元以 2026-07-12 標頭 `SYMM ".:/-ox+*c?"` 為準。`o` = rot4。舊 `decode.c` 的字串順序不同，但 `o` 仍然標成 rot4。對稱標籤不作為對錯依據。
- 官方 `check_validity` 用 unsigned 乘法比較。座標 < 90 時與有號行列式同值；本輪仍用 Python 有號整數，不把那份 C 當本輪驗證器。

## 驗證之後（同一輪，不另做檢索宣稱）

表在實驗結束前再抓一次，SHA256 `6fd563d23b1bc5064bd9ae4bf8a3933c5f153b7c3b32a622c4652b2a19d04ff4`，與 preflight 快取相同。

公開檔重驗見 `problems/MATH-001/results/grok_r1/`。n=75 不在 `all_known_solutions`（431008 筆，最大 n=76）裡，也不在 `configurations/*.few` 裡。這只證明這份 2026-08-31 的檔案沒有 n=75，不是證明 D(75)<152。

## 本輪不採用的東西

- 未合併的 `glm/MATH-001-baseline-r1`（PR #2）不讀、不改、不把它的 stdout 當本輪證據。
- 模型記憶中的舊 frontier 不作數；以上均來自本輪打開的頁面。
