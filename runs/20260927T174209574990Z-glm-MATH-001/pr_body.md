## 範圍與主線
Problem / round ID：MATH-001 / 20260927T174209574990Z-glm-MATH-001
Base SHA / governance pin：cd1e4eadc177920b95332ebe08c2498e52c3ce56 / FrontierLab-Governance 07d2b13051b83215182e411e1612f92f1912d8fb

## 本輪新鮮檢索
8 條實際 query（general/discipline/solution/criticism 齊備），紀錄與來源見 runs/.../LITERATURE_MAP.md；primary：arXiv:2602.07751（v1）、Flammenkamp 紀錄頁（更新 2026-09-11）、arXiv:2605.09215（v2）、Prellberg GitHub（MIT）。無 erratum/retraction。
**文獻更新（PARTIAL_PROGRESS）**：finite frontier 由題卡之 n≤60（最小未定 61）推進至 n≤74 除 75 外全解＋紀錄 n=76（Heule SAT 2026-08-10）；最小未定 n=75。一般問題仍 open；題卡 known_result 已更新（非規格變更），statement/evaluator/completion_criterion 未動。

## 驗收（動手前凍結）
見 round.json acceptance：整數 verifier v1＋獨立 v2、確定性 DFS 自製 n=2..10 之 2n 憑證、Flammenkamp 資料集獨立解碼重驗、共線注入負例（保持 2n 計數）、邊界 n=1。預算 0 美元／≤120 分／≤100 trials。

## 實際執行與證據
- 自製憑證 n=2..10 全部 v1+v2 PASS（n=1 UNSAT=D(1)=1 邊界）。
- Flammenkamp data_1997（36,912 構造，n=2..52）：獨立 Python 解碼（decode.c 語意）→ v2 全量驗證 0 失敗＋v1 抽樣 999 個 0 失敗 → REPRODUCTION_SUCCESS。
- Adversarial：636 案例（共線注入/重複/越界/缺點數/fuzz seed42）全部正確拒絕、兩實作 636/636 一致 → EVALUATORS_SOUND。
- Skeptic 迴圈抓到並修正 2 個自家 bug（解碼映射 ord−87→ord−61；v2 違規回報 NameError），buggy 對照摘要保留。
- 環境／版本／hash：problems/MATH-001/results/r1/{environment.txt,hashes.txt}。Python 3.13.5，僅標準庫。
- 憑證可重驗：`python experiments/baseline_r1/verifier.py <cert>`（及 verifier_indep.py），exit 0 = PASS。

## 獨立覆核
單 agent 輪（glm）：v1/v2 為互不共享程式碼之雙實作，交叉檢查全部正負例；無獨立 session 重現（單 agent 不得宣稱獨立重現——本 PR 不作此宣稱）。請 Verifier/Skeptic 以自身實作抽查憑證。

## 沒做成的事與限制
未取得 Heule n=71–76 原始解／SAT 認證檔；未審 arXiv:2602.07751 全文；未重現 HJSW (3/2−ε)n 下界；DFS 未加對稱破壞故未推 n≥11；本輪 FINISHED ≠ 問題完成，MATH-001 仍 OPEN。未跑寫 NOT_RUN：無。

## 合併
等待 owner 明確批准；不自行合併、未修改 evaluator 來讓結果通過（evaluator 變更僅為修 bug，見 skeptic 紀錄）。
