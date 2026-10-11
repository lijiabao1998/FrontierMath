# MATH-006 有界獨立驗證報告

本輪有限驗證通過，但原 r1 驗證器契約失敗；總判定 **AUDIT_FAIL_EVALUATOR_DEFECTS**，退出碼 **1**。這不是 Frankl 猜想的反例。未修改原驗證器、題卡或任何既有結果。

來源是 [PR10](https://github.com/lijiabao1998/FrontierMath/pull/10)，head `1d75828f779b9863f966a76fbf115fac3708e09c`；本輪 fetch 後 main 是 `12962b3f7612ecdfc22280c0403f9ef6dcca3f56`。治理鎖定 `07d2b13051b83215182e411e1612f92f1912d8fb`。父代理已有同範圍領題，本輪承接該登記，沒有新的 GitHub 寫入。兩庫與治理快照沒有 .agents/skills 或下層 AGENTS.md。

計畫在執行前凍結，先完成新的四路搜尋與來源閱讀，再由鎖定工具成功 admit。本輪協議 SHA256 為 `376b3ac869af007dd3281eee863d3c15b7d53551142fee70fe15b9f2df5167e3`。先行本地協議提交 `659df6d`，實驗之後沒有更改協議、數值容差或程式。完整控制表、文獻限制與來源快照在 experiments/independent_20261011/。

基線是既有 r1/r2 小 m 計數。族包含空集合、族為空、族的聯集為空是三種不同情況。[OEIS A102896](https://oeis.org/A102896) 的 Moore-family 定義經補集對應到「含空集合的 union-closed 族」，所以它與 r1 全部非空族的計數不同。

| m | 全部候選 | 非空 union-closed 族 | 聯集非空族 | 含空集合族 | 含空集合且非平凡 |
|---|---:|---:|---:|---:|---:|
| 1 | 4 | 3 | 2 | 2 | 1 |
| 2 | 16 | 13 | 12 | 7 | 6 |
| 3 | 256 | 121 | 120 | 61 | 60 |
| 4 | 65,536 | 4,959 | 4,958 | 2,480 | 2,479 |

這些是本轮實際產出的數值，共檢查 65,812 個候選。新寫的 oracle 使用直接 frozenset 聯集與 tuple 成員檢查，拒絕重複集合後才評估准入，使用 `2*最高頻數 >= 族大小` 的整數條件。所有聯集非空的合法閉合族均通過；各 m 的最小比例恰為 1/2。m4 含空集合的 2,479 個非平凡族也全部通過。r1 closure 對全部候選均與直接實作一致，r2 BFS 輸出的完整族集合與直接實作精確相同，沒有 corpus mismatch。保存的直接閉合族 corpus 有 5,096 行，逐 m 計數如表。

本輪動態確認兩類軟體缺陷：

- r1 的公共 closure/frequency predicate 路徑接受 `[{1},{1}]` 與 `[{1},{1},{2},{1,2}]`。原 closure 先轉 set，沒有唯一性拒絕；這些輸入違反題卡的集合唯一性要求，不能作猜想反例。
- V1 控制投影令 is_union_closed 恆 false 或恆 true，分別使正控或破壞控失敗，原 verdict 仍為 `EVALUATOR_ROUND_COMPLETE`、原 return 表達式仍得 0。投影直接擷取原初始化、V1、最終 verdict 與 return AST，假定其餘階段通過；**完整原 main 沒有重跑**，不能把投影說成端到端基線重現。

空族的 closure 是 vacuous true，完整准入仍排除空聯集；{∅} 的半數 predicate false，兩者都未被當成合法 Frankl 實例。22 個具名檢查中 18 個通過、4 個原契約檢查失敗。reference_validation_pass、finite_replication_pass、named_case_budget_pass 為 true；original_evaluator_contract_pass 為 false。自寫總判定對失敗、缺失或空檢查清單拒絕成功。

實際啟動是 2026-10-11T18:23:03.912599Z，結束 18:23:04.762227Z。單 CPU affinity mask=1，子程序總 wall 0.685 秒；oracle wall 0.565 秒、CPU 0.563 秒。新支出 $0。計算沒有與物理計算重疊。首次沙箱 Git clone 的 DNS 失敗及成功的受審核重試都保存。Python stderr 有「Failed to find real location ...python.exe」警告，未阻止完整結果產出；原因沒有進一步判定。

復跑在庫根目錄執行，使用新 tag，不覆蓋 attempt-01：

```powershell
python -X utf8 problems/MATH-006/experiments/independent_20261011/run_bounded.py --round runs/20261011T180847963562Z-gpt-MATH-006/round.json --tag replay-01 --replay
```

預期退出碼是 1，因為原驗證器缺陷仍存在；不要把它改成成功來使流程變綠。run_bounded.py 驗證所有凍結輸入 hash、限制單 CPU 並保存 binary stdout/stderr、launch.json、execution.json。原始結果是 attempt-01/data/result.json；全部閉合族是 direct_union_closed_corpus.jsonl。

獨立審查由另一個唯讀 session 檢查協議、函式、來源 hash、原始 stdout/result 與 corpus。此 session 沒有第二次枚舉；這是獨立程式與證據審查，並非第二次獨立實驗。同一模型的再次同意不被當成實驗重現。最終審查在 INDEPENDENT_REVIEW.md。

Git 的文字轉換使初始協議提交有 1 個 source snapshot 的 blob bytes 與實際執行 bytes 不同。失配保存在 BYTE_PRESERVATION.json。之後僅在本輪 experiment/results 目錄加 `* -text` 並重新 stage 精確 bytes；沒有重跑、修改原研究程式或更改結果。最終提交須通過 Git-blob 與凍結 SHA256 核對。

未跑 m5、r1 V4 的 m6 隨機探索、原 main、Lean 或一般定理證明，也沒有修復 evaluator。MATH-006 保持 OPEN。本輪的新發現限於兩類既有靜態疑點的動態確認；小 m 計數與半數下界是有限重現，沒有數學新穎性宣稱。由父代理決定後續分開提出 evaluator 修復；本輪只做本地提交、不推送、不合併、不部署。
