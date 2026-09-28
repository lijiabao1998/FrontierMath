# ROUND REPORT｜MATH-001 r2｜20260927T191802542471Z-glm-MATH-001

- branch：`glm/MATH-001-n75-bench-r2`；pin `07d2b130`；verdict：**NO_RESOLUTION_FOUND**（再核查）
- 領題狀態：PR #3（grok r1，範圍=finite checkers+public reproduction）與本 PR 範圍不同（n=75 bench），無撞題；r1（glm，PR #2）已先行。

## 成果：n=75 attack bench（BENCH_SOUND，4/4 預登記 checks）
1. **~~資料嘗試→BLOCKED~~【已撤回，見 Remediation v3】**：初版記述「n=71-76 原始解不可取得」是**錯誤的**。獨立驗證者 dsk（PR #5）指出兩條公開檢索路徑；本庫以自有 fetch＋自寫解碼器複驗：`download/all_known_solutions`（23,834,242 bytes、**431,008 構造**）中 **n=71/72/73/74/76 各 1 筆、n=75 為 [2,76] 中唯一 0 筆**。正確記述：**n=71,72,73,74,76 公開構造可得；n=75 仍為最小未解有限案例**。檢索路徑署名為 dsk 之獨立驗證者證據（independent verifier evidence）；驗證檔 `results/r2/deepseek_path1_verification.json`。
2. **CNF encoding 產生器**（`experiments/n75_bench/ntil_cnf.py`）：cells 變數、列/行 exactly-2、全斜率 primitive lines at-most-2；triples 與 Sinz-sequential 兩種 at-most-2 編碼；DIMACS-ready。
3. **小 n 行為驗證**：n=2..5 SAT 且模型全部通過 r1 整數 verifier；n=1 UNSAT；鴿籠負控（row1 cap=1）n=3,4 UNSAT；雙編碼在 n=3,4 判定一致。
4. **n=75 規模估計（線正典化後，Codex P2 修正）**：排除水平/垂直線（已由行列 cardinality 覆蓋）並以 dy>0 正典化方向後：1,336,678 條 ≥3-cell 線；triples 模式線子句 **23.34M**＋行列 ~10.1M ≈ **33.5M clauses / 5,625 變數**；seq 模式輔助變數 **8,804,510**（2m−1/線）。可行但需串流 DIMACS 產出＋專輪求解。
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

## Remediation v3（2026-09-28，Codex 二審回應）
- **P1 UNSAT certificates**：n=1 與 pigeonhole（n=3,4）之 UNSAT 改由**窮舉枚舉證明**（2⁹=512、2¹⁶=65,536 全 assignment 檢查，satisfying=0，方法完整可獨立重做）；solver UNSAT 一律標註 `SOLVER_UNSAT_UNCERTIFIED`，不再作為 BENCH_SOUND 的嚴格證據。C2/C3 checks 改以窮舉證明為準。
- **P2 線正典化**：primitive_lines 排除水平/垂直線（行列 cardinality 已覆蓋）且方向正典化 dy>0——修掉 (1,0)/(−1,0) 雙重發射（n=75 曾多出 ~10.1M 冗餘子句）。回歸測試 C5 + tests_regression T6。
- **P2 hashes**：`verify_manifest.py` 新增；manifest 於所有檔案定稿後最後生成並驗證。
- **P2 報告數字**：~10.2M/38.5M/48.6M 全部同步為 8,804,510 / 23.34M / ~33.5M。
- **外部更正（署名）**：「n=71-76 BLOCKED」記述撤回——dsk PR #5 為獨立驗證者證據來源；本庫以自有下載+解碼器複驗（431,008 全量、n=75 唯一缺席）。
- 重跑：BENCH_SOUND 5/5（C1 SAT+verifier、C2/C3 窮舉 UNSAT、C4 雙編碼一致、C5 線正典化）。
