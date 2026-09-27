# ROUND REPORT｜MATH-001｜20260927T174209574990Z-glm-MATH-001

- repo／branch：FrontierMath `glm/MATH-001-baseline-r1`（base `cd1e4eadc177920b95332ebe08c2498e52c3ce56`）
- governance pin：FrontierLab-Governance `07d2b13051b83215182e411e1612f92f1912d8fb`（依 GOVERNANCE.lock.json checkout）
- verdict：**PARTIAL_PROGRESS**（一般問題仍 open；finite frontier 文獻更新）
- 預算：0 美元；wall（宣告 ≤120 分）；trials 上限 100（實際執行的計算性實驗：搜索 10 次 n、解碼驗證 1 批、tamper/fuzz 1 批）

## 本輪做了什麼

1. **開工程序**：fetch（origin/main 無前進）→ 治理 pin checkout → `validate` PASS（10 題卡）→ 查 open PR/issue（0）→ branch → `start`（DRAFT）→ 本輪新鮮四路檢索（8 query）→ 凍結驗收 → `admit`（首次嘗試被 gate 正確擋下：漏填七個 preflight 旗標；補齊後 ADMITTED）。
2. **文獻檢索（詳見 LITERATURE_MAP.md）**：
   - 確認題卡 primary（Prellberg arXiv:2602.07751，v1，2026-02-08）：2n 構造覆盖所有 n≤60，最小未定 61。
   - **發現題卡已知結果已過時**：Flammenkamp 紀錄頁（更新 2026-09-11）記載 Heule 以 SAT 於 2026-06/08 補齊 61–70 並創 n=72/76 紀錄；n=71/73（2026-08-17/19）、n=74（Prellberg 2026-07-20）亦有解。**現況：n≤74 除 75 外皆有 2n 解；紀錄 n=76；最小未定 n=75。**
   - criticism 路：無 erratum/retraction/failed replication；版本核查通過。
   - 相鄰 scope：Prellberg 棋盤變體（arXiv:2605.09215 v2 2026-09-19）——不同問題，不改變本題狀態。
3. **Evaluator 建立（兩個獨立實作）**：
   - `experiments/baseline_r1/verifier.py`（v1）：全三點組整數行列式，顯然正確版。
   - `experiments/baseline_r1/verifier_indep.py`（v2）：獨立演算法（row-pair 直線掃描 O(n³) 整數運算＋Fraction 斜率複核＋行列計數結構審計），與 v1 零共享程式碼。
4. **自製小 n 憑證**：`search_small_n.py` 確定性 DFS（無 RNG）產生 n=2..10 之 2n 構造（n=1 UNSAT，符合 D(1)=1 邊界）。因 2n 是行鴿籠上界，每張通過驗證的 2n 憑證即證 D(n)=2n 該 n。v1/v2 雙 PASS。
5. **公開構造重現**：下載 Flammenkamp `data_1997/known_solutions`（1.65MB）＋`decode.c`；依其語意獨立重寫 Python 解碼器；**36,912 個公開構造（n=2..52）全數以 v2 演算法驗證通過＋999 個 v1 抽檢全過** → `REPRODUCTION_SUCCESS`。
6. **Adversarial（Skeptic）**：`tamper_test.py` 636 案例（共線注入保持 2n 計數、重複點、越界、點數不足、n=1 假憑證、600 個 seed=42 隨機 fuzz）→ 兩實作全部正確拒絕且 636/636 一致 → `EVALUATORS_SOUND`。

## Skeptic 迴圈實際抓到的 bug（本輪最有價值的負結果）

1. **解碼器映射 bug**：首輪批量重現 `REPRODUCTION_DISCREPANCY`（1,469/36,690 失敗，全部集中 n≥37，錯誤型態為欄位計數爆炸）。根因：我把 decode.c 的 `c-'a'+36` 誤寫成 `ord(c)-87`（'a' 應為 36 而非 10）；n≤36 不用小寫字母故全過。修正後全綠。 buggy 版摘要保留於 `results/r1/flammenkamp/decode_verify_summary_BUGGY_MAPPING_a-87.json` 作為對照。
2. **v2 違規回報路徑 NameError**：v2 的錯誤訊息 f-string 引用已刪除變數 `s1`，只在「有共線要回報」時觸發——先前全 PASS 從未走到。fuzz 第一個案例即炸出。修正後整套重跑。
   - 教訓：只測 PASS 路徑的 evaluator 是不可信的；EVIDENCE_POLICY 要求的「故意破壞測試」不是形式。

## 憑證（certificates）與可重現性

- 自製：`results/r1/self/self_n02..n10.json`（含 search_stats、WLOG 說明）
- 公開重現：`results/r1/flammenkamp/`（解碼摘要＋代表性憑證 n=2..52 與各對稱類）
- 否定組：`results/r1/negative/`（636 篡改/fuzz 案例檔＋tamper_summary.json）
- hash：`results/r1/hashes.txt`（SHA256，含資料檔與程式）；環境：`results/r1/environment.txt`
- 每張憑證可用 CLI 重驗：`python experiments/baseline_r1/verifier.py <cert>` 與 `verifier_indep.py`（需 exit 0）

## 沒做成的事／限制

- 未取得 Heule n=61–76 原始解資料與 SAT 認證檔（Flammenkamp 頁無直接 href；ResearchGate 原文未取）——本輪對新 frontier 的重驗僅及文獻層級＋n≤52 資料集。
- 未審讀 arXiv:2602.07751 十六頁全文（僅 abs 頁）；「Four Methods, One Problem」論文未能定位 primary。
- 未嘗試 n=11/12 之 DFS（n=9 已 13.7s/306k 節點，指數增長；需對稱性破壞剪枝再戰）。
- 未重現 HJSW (3/2−ε)n 下界構造；未動 Lean/claims.json（本輪無形式化成果）。
- 隨機搜尋找不到反例、找不到 2n 構造，皆不證明一般命題（validation_limits）。

## 對下一輪的最小下一步（next-smallest-action）

1. 取得並獨立重驗 Heule n=71–76 解（聯繫 Flammenkamp 頁資料目錄/Heule 個人頁；若有 DRAT 證書一併核）。
2. 對 n=75 發起 SAT/CSP 攻略前置：編碼 2n 點之 CNF（pair-per-row 對稱破壞），先小 n 校準 solver 行為；UNSAT 證書若出現即為重大結果（D(75)<2n 反例方向）。
3. 審讀 arXiv:2602.07751 全文＋其 GitHub Table 1.txt，比對其 CP-SAT 編碼技巧。
4. DFS 加對稱破壞（固定首行/對角規範化）後推 n=11/12。

## 狀態不混用聲明

本輪完成的是：evaluator 建立＋小 n 憑證＋公開資料集重現＋文獻更新。**問題 MATH-001 仍為 OPEN**；本輪 FINISHED ≠ 問題 COMPLETED；無任何一般性宣稱。
