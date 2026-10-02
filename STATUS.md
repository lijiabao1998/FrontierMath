# 狀態｜2026-09-27

主線：MATH-001 grok r1 已跑完有限檢查器與公開構造重驗。一般問題仍 OPEN。下一輪最小動作是 n=75，不是再做一套 n<=10 的檢查器。

- 題卡：10。MATH-001 仍 OPEN。known_result 已依本輪檢索更新到 Flammenkamp 2026-09-11 的表：n<=74 除 75 外有 2n 構造，紀錄 n=76。這是外部結果。
- 本分支輪次：1。`runs/20260927T184702323864Z-grok-MATH-001`，判定 PARTIAL_PROGRESS，輪次 FINISHED。
- 本輪檢查器：整數行列式與直線分桶，同一 session 寫成，不是跨 agent 獨立簽署。n=2..10 自製 2n 憑證兩者都通過。故意共線、重複、越界、點數不足兩者都拒絕，240 個 seed=42 的 fuzz 沒有分歧。
- 公開重現：`data_1997/known_solutions` 36912 筆，兩套檢查器都通過。`download/configurations/n{61..74,76}_*.few` 共 65 筆，兩套都通過。
- `all_known_solutions`（SHA256 `c27f8f53…b7effde`，23834242 bytes）由 `full_scan.py` 在 git `7561485` 上掃完：431008 筆，兩套檢查器，0 失敗，exit 0。n=54 是 7714 筆，含先前 timeout 落下的尾段。per_n 沒有 n=75，有 n=76 的 1 筆。清單在 `results/grok_r1/public/all_known_full_checkpoint.json`。
- 第一遍 `run_round.py` 只掃到 412675 筆就 `time_limit`，而且當時的 exit 條件沒把這個停住算成失敗。那次不是全量成功。`recheck_public.py` 的舊版只數學驗證 n≥55。
- `@` 失敗留在 `summary.json` 與 `public_failure.json`，對應當時的 `decode_flam.py` `fdfc81c9…d154d65d`。這個 hash 寫在 `run1_binding.json`，沒有用後來的程式 hash 回填。
- 前沿結果：0。沒有新的一般定理或反例。
- 未跑：Lean 新定理、Hall–Jackson–Sudbery–Wild 構造、Heule SAT 證書、n=75 搜索。
- 並行：glm 的 PR #2 仍 OPEN，本分支沒有改它，也沒有把它的輸出當證據。
- 治理 pin 仍是 `07d2b13051b83215182e411e1612f92f1912d8fb`，沒有改成治理 repo 的最新 HEAD。
- 其餘 9 題排隊。沒有常駐 agent 或付費算力。
