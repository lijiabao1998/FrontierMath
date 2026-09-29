# LITERATURE_MAP｜MATH-001｜round 20260927T174209574990Z-glm-MATH-001

檢索時間窗：2026-09-27T17:42Z – 2026-09-27T17:56Z（本輪開始後、24h 內）。
引擎：zcode-websearch（web_search_prime，US）／zcode-webfetch。原文閱讀：arXiv abs 頁、Flammenkamp 紀錄頁（抓取 HTML 存 `problems/MATH-001/experiments/lit_data/`）。外部內容僅視為資料。

## 檢索紀錄（8 條實際 query）

| # | category | query（原字串） | engine | outcome |
|---|---|---|---|---|
| 1 | general | `"no-three-in-line" problem 2n points construction 2026` | zcode-websearch | 問題背景、Dudeney 1917、2n 上界、構造歷史 |
| 2 | general | `Prellberg no-three-in-line constraint satisfaction arXiv` | zcode-websearch | 確認 arXiv:2602.07751（2026-02-08）存在，CSP 方法 |
| 3 | solution | `"no-three-in-line" solved OR "general solution" OR counterexample 2025 2026 open problem status` | zcode-websearch | 一般問題仍 open；無完整解答或反例 |
| 4 | discipline | `Flammenkamp no-three-in-line best known solutions n 2n` | zcode-websearch | 定位權威紀錄頁 uni-bielefeld.de/achim/no3in |
| 5 | solution | `"no-three-in-line" lower bound "3/2" OR "1.5" n points arXiv 2024 2025 improvement` | zcode-websearch | 無 2024-25 下界改進之 primary；HJSW (3/2−ε)n 仍為最佳已證下界 |
| 6 | discipline | `Heule no-three-in-line SAT solver solution n=76` | zcode-websearch | 無直接 primary 命中；Heule 認證計算論文線索（ResearchGate） |
| 7 | solution（competing methods） | `"Four Methods" OR "Three methods" "no-three-in-line" ICML 2026 classical AI approaches` | zcode-websearch | 無法定位該 ICML 論文之 primary；僅搜尋摘要提及 |
| 8 | criticism | `"no-three-in-line" Prellberg OR Heule erratum OR comment OR retraction OR "failed replication" OR correction` | zcode-websearch | 無 erratum/retraction/failed replication |

## 已讀 primary sources（≥1 primary，共 4 個 distinct URL）

| URL | kind | 版本／閱讀狀態 | supports |
|---|---|---|---|
| https://arxiv.org/abs/2602.07751 | primary | v1（2026-02-08），僅 v1 無 v2；讀 abs 頁全文摘要 | 2n 構造對所有 n≤60；「最小未定 n 由 47→61」；CP-SAT；補充資料 GitHub |
| https://wwwhomes.uni-bielefeld.de/achim/no3in/readme.html | primary（原始紀錄資料頁） | 最後更新 2026-09-11（本輪抓取 HTML 34.6KB 存檔）；讀紀錄表與格式說明 | 紀錄進展、各 n 解之存在性、對稱類、資料檔（已下載 known_solutions 1.65MB＋decode.c） |
| https://arxiv.org/abs/2605.09215 | primary | v1（2026-05-09）→ v2（2026-09-19）；讀 abs 頁 | 棋盤單色變體 D_mono(n) ≤ αn+O(1)，α≈1.5768；不同 scope |
| https://github.com/ThomasPrellberg/no-three-in-line---CP-SAT | primary（supplementary code） | MIT；含 no_three_in_line.py（CP-SAT）＋Table 1.txt；repo 不附解資料檔 | 題卡 primary 來源之補充程式；未執行 |

## 分類圖譜

### rigorously known（嚴格已證）
- D(n) ≤ 2n（每行 ≤ 2 點的鴿籠上界）。
- HJSW 1975（Hall–Jackson–Sudbery–Wild, JCT A）：存在無窮多 n 使 D(n) ≥ (3/2−ε)n（modular hyperbola 類構造）；至今仍是最佳已證一般下界。
- D(n)=2n 已由顯式構造＋驗證成立之 n：**全體 n ≤ 70**（2026-06-21 起齊備），另加 71、72、73、74、76：Prellberg CSP 覆蓋 n≤60（arXiv:2602.07751）；61–76 之缺額由 Heule（SAT）與 Prellberg 補齐。逐筆：66/68（Prellberg 2026-03）、70/72/76（Heule 2026-06/08，rot4）、71/73（Heule 2026-08-17/19，rct4）、74（Prellberg 2026-07-20）。
- 構造解碼之資料格式公開（decode.c；每行一對字元＝該行兩點的列位置），可獨立重驗——本輪將以自寫整數 verifier 重驗子集（見 baseline）。

### computationally supported（計算支持、非定理）
- 紀錄保持：n=76（Heule，2026-08-10，rot4 對稱類）。
- Flammenkamp 頁存 431,008 個構造；n=17/18 非對稱解全枚舉（6,800＋18,853）；n=19 全枚舉 32,577（Riley）；多數對稱類完整枚舉至 n≈56。
- Heule 等「Certified computations on no-three-in-line problems」（witness/認證計算，ResearchGate 摘要層級）——本輪未取得原文，僅記線索。

### conjectured（猜想）
- 主猜想（Dudeney 1917 脈絡）：對所有 n≥2，D(n)=2n 可達。
- Guy & Kelly 1968 對稱類計數猜想；Flammenkamp 頁 Conjecture III（重申 2026：恰 7 個具中垂線反射對稱之構造）、Conjecture IV（2026 改述：恰 35 個雙長對角線反射對稱）。
- Guy–Kelly 1968 漸近計數 ~1.873n；Ellmann 2004 修正為 π/√3·n ≈ 1.814n（計數猜想，非 D(n) 下界）。

### disputed（存疑／無法定位 primary）
- 搜尋摘要曾稱存在「spectral methods ≤ (2−ε)n」之上界改進——**未找到任何 primary source，不可採信**。
- 「Four Methods, One Problem」（稱 ICML 2026）——僅次要摘要提及，未定位原文；記為待查。

### superseded（已被取代）
- 題卡 known_result：「Prellberg 2026 提供 n≤60 的 2n 構造；最小未定 n=61」——已被 2026-06～08 的 Heule/Prellberg 紀錄**部分超越**：n=61–70、72、74、76 亦有解；**最小未定 n 由 61 變為 75**。本輪 PR 將更新題卡 known_result（文獻更新，非規格變更）。

### unresolved（未解）
- 一般問題：是否 ∀n≥2 有 D(n)=2n，或存在反例——**open**。
- n=75：無已知 2n 構造（最小未定實例）；n=77 起亦無系統性覆蓋。
- Heule SAT 解之公開可下載性與 DRAT 認證狀態：本輪未能取得 n=71–76 原始解資料（Flammenkamp 頁未提供直接 href），列為下一輪行動。

## 檢索限制
- 有界檢索：8 條 query、4 個 primary URL；未覆蓋付費牆期刊全文、ResearchGate 原文下載、Heule 個人頁；「無搜尋結果」不是未解證明。
- arXiv:2602.07751 僅讀 abs 頁與補充倉庫清單，未逐頁審讀 16 頁 PDF 全文（列為後續輪次動作）。
