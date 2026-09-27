# FrontierMath
前沿數學

## 主線：精確構造 → 反例／證書 → 形式證明
第一個工作目標是 **MATH-001 的小實例與已公開構造驗證器**，不是直接宣告通解。先做一個可重做的 loop，再增加並行。所有題卡的 OPEN 都是初始有界檢索狀態；新輪次必須重查最新文獻。

本庫由 lijiabao1998 獨立建立，**與 Epoch AI 的同名 FrontierMath benchmark 無隸屬關係**。

## 第一批 10 題
A：優先建立有限驗證器；B：需要較多形式化／文獻；C：先分解與重現。這不是可解性概率。

| ID | 問題 | 級別 | 第一輪 |
|---|---|---|---|
| [MATH-001](problems/MATH-001/problem.json) | No-three-in-line 一般 n 的 2n 構造 | A | 整數 determinant 驗證器、小 n 基線 |
| [MATH-002](problems/MATH-002/problem.json) | Ramsey R(5,5) 精確值 | B | 小 Ramsey 正負例、圖證書格式 |
| [MATH-003](problems/MATH-003/problem.json) | Hadwiger–Nelson 平面色數 | B | 精確單位距離圖與著色證書 |
| [MATH-004](problems/MATH-004/problem.json) | Cap set 漸近增長率 | A | F3 向量加法與無三項結構驗證 |
| [MATH-005](problems/MATH-005/problem.json) | 五維 kissing number 精確值 | B | 40 點基線的精確／區間驗證 |
| [MATH-006](problems/MATH-006/problem.json) | Frankl union-closed conjecture | A | 小全集族窮舉與閉包檢查 |
| [MATH-007](problems/MATH-007/problem.json) | 一般 Lonely Runner conjecture | B | 有理分段事件掃描，不只浮點採樣 |
| [MATH-008](problems/MATH-008/problem.json) | Earth–Moon／biplanar 最大色數 | B | 兩平面分解與著色雙證書 |
| [MATH-009](problems/MATH-009/problem.json) | 一般 Hadamard conjecture | C | ±1 矩陣正交性、排除已解階數 |
| [MATH-010](problems/MATH-010/problem.json) | C7 Shannon capacity 精確值 | A | 強積獨立集證書、更新下界基線 |

每張 JSON 都有精確 statement、已知結果、剩餘缺口、第一步、evaluator、不能推出什麼、完成條件、來源與本次檢索字串。題目定義是本庫的研究 scope；來源中的部分結果不被誇大為整題解答。

## 每輪先做
依 [AGENTS.md](AGENTS.md) fetch/讀卡/看 runs，建立自己的分支。治理固定在 [07d2b130](https://github.com/lijiabao1998/FrontierLab-Governance/tree/07d2b13051b83215182e411e1612f92f1912d8fb)。

```bash
# 在旁邊 clone 治理庫並 checkout GOVERNANCE.lock.json 的 commit
python3 ../FrontierLab-Governance/tools/frontier.py validate .
python3 ../FrontierLab-Governance/tools/frontier.py start . MATH-001 --agent gpt
# 實際聯網查：general / discipline / solution / criticism，讀原始來源，填 round.json
python3 ../FrontierLab-Governance/tools/frontier.py admit . runs/<round-id>/round.json
```

已找到且獨立確認同範圍解答：立即記 `COMPLETED_EXTERNAL`，署名歸給原作者，停止重做；未核實預印本記 `CLAIMED_RESOLVED`。有限 n、下界改善、restricted variant 不會關閉一般問題。

## Lean 線上工作台
已放 Lean 核心最小工程與 CI，固定 `leanprover/lean4:v4.34.1`；`lake build --wfail` 及 `#print axioms` audit 檢查列出的 claim。`FrontierMath.bootstrap_add_zero` 是**工具鏈 smoke theorem，不是前沿成果**。

```bash
lake build --wfail
python3 tools/audit_lean.py
```

本版未引入 mathlib。需要時另開依賴 PR，選與 Lean 匹配的精確 mathlib commit，提交 `lake-manifest.json`，重驗再使用；不要追浮動 master。`claims.json` 列需要審計的每個正式 theorem。CI 通過只保證列出的命題在允許公理下被檢查，不保證自然語言題目翻譯正確，也不保證新穎。研究 proof 應放 `problems/<ID>/proofs/` 並經正式 Lean module 匯入；不能以未被 build 的檔案冒充證明。

## 目前交付邊界
40 題整體中的本庫 10 題已完成初始選題；尚未開始原創數學探索、下載大型構造、實作各題 evaluator 或重現最佳界。來源摘要／問題頁篩查不等於完整證明審讀。流程 CI、Lean CI 的實際結果以 Actions 為準，不在這裡預寫成功。
