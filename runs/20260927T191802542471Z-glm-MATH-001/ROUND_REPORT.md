# ROUND REPORT｜MATH-001 r2｜20260927T191802542471Z-glm-MATH-001

- branch：`glm/MATH-001-n75-bench-r2`；pin `07d2b130`；verdict：**NO_RESOLUTION_FOUND**（再核查）
- 領題狀態：PR #3（grok r1，範圍=finite checkers+public reproduction）與本 PR 範圍不同（n=75 bench），無撞題；r1（glm，PR #2）已先行。

## 成果：n=75 attack bench（BENCH_SOUND，4/4 預登記 checks）
1. **資料嘗試→BLOCKED**：Flammenkamp 頁 anchors 無靜態 href；`table.txt`/`cases.txt`（已下載）為解數量枚舉表非構造；Heule GitHub 無 NTIL DIMACS。**不以網頁聲稱代替 reproduction**；n=71-76 獨立重驗延至取得原始解。
2. **CNF encoding 產生器**（`experiments/n75_bench/ntil_cnf.py`）：cells 變數、列/行 exactly-2、全斜率 primitive lines at-most-2；triples 與 Sinz-sequential 兩種 at-most-2 編碼；DIMACS-ready。
3. **小 n 行為驗證**：n=2..5 SAT 且模型全部通過 r1 整數 verifier；n=1 UNSAT；鴿籠負控（row1 cap=1）n=3,4 UNSAT；雙編碼在 n=3,4 判定一致。
4. **n=75 規模估計**：1,336,903 條 ≥3-cell 線；triples 模式線子句 38.5M＋行列 ~10M ≈ **48.6M clauses / 5,625 變數**；seq 模式輔助變數 ~8.84M（2m−1/線；初版 10.2M 估計經 Codex 審查修正）。可行但需串流 DIMACS 產出＋專輪求解。
5. solver：pysat/CaDiCaL **in-repo 安裝**（experiments/n75_bench/.deps，不污染系統）。

## Skeptic 迴圈抓到的自家 bug
- Sinz 計數器初版含致命錯誤：最終 unit `¬prev_ge2` 等於禁止 ≥2=true（整題必 UNSAT）＋兩條多餘 exactness 子句——重寫為正確五子句族（forward-only）。
- 結果列印 KeyError（pigeonhole 無 clauses 鍵）。
- 教訓：cardinality 編碼必須先過「已知 SAT 個案＋鴿籠 UNSAT」雙向控制才可信——本輪流程即此。

## 下一輪最小下一步
1. 串流產生 n=75 DIMACS（seq 模式，~20M 子句）＋ CaDiCaL 求解（預算另立；SAT 即證 D(75)=2n 新有限前沿）。
2. 對稱破壞（row/col lex-leader 或 rot4 類固定）以縮搜索空間——先在小 n 驗證 soundness。
3. 若 Heule/Flammenkamp 取得原始解→以 r1 verifier 獨立重驗。

## Remediation（2026-09-28，Codex review 回應）
- P1 lazy import：pysat 改為 solve() 內延遲載入，--estimate 不再依賴平台 wheel；回歸測試 T1（meta_path 阻擋 pysat 下 --estimate 仍可跑）。
- P1 鴿籠負控制：row1_cap=1 由 per-cell unit（等價空列、TRIVIAL UNSAT）改為 pairwise at-most-1；UNSAT 現在真正由 cardinality 推導。回歸測試 T2（exactly-one SAT/兩真 UNSAT）。
- P2 `--mode seq` KeyError：改為恆跑雙模式；回歸測試 T3（CLI seq 完整跑完無 KeyError）。
- P2 aux 變數估計：2m−1/線，總數 10,174,938 → **8,838,035**；回歸測試 T4。報告數字已同步收窄。
- 重跑結果：BENCH_SOUND（4/4 checks）在修正後編碼上維持；results JSON 重新生成、hashes 重算。
- `tests_regression.py`：T1–T4 全 PASS。
