# FrontierMath agent 入口

先讀 README、STATUS、GOVERNANCE.lock.json，再讀固定治理版的 AGENTS、RESEARCH_PROTOCOL、EVIDENCE_POLICY、SAFETY：
https://github.com/lijiabao1998/FrontierLab-Governance/tree/07d2b13051b83215182e411e1612f92f1912d8fb

本次初始化之後，所有 agent 用 `<agent>/MATH-xxx-<topic>` 分支，不直接寫 main；單一工作目錄一位寫入者。遠端 main 是已審核紀錄，合併需 owner 明確批准，作者不得自合。

每輪先 fetch 記 base SHA、查 open PR／領題，讀既有失敗；執行 start，真正聯網做本輪四路查證，再 admit。缺網路、來源未讀、只有未核實解答則停。不沿用昨日檢索。已確認外部解答立即標 COMPLETED_EXTERNAL 並提 PR，不再占探索預算。

Scout / Explorer / Verifier / Skeptic / Integrator 分工；同一模型多次同意不算獨立驗證。先重現、小例、正反例及故意破壞測試，再做新構造；驗證器與成功門檻不能和結果同 PR 偷改。

數學加嚴：有限窮舉不推出無限命題；浮點構造需精確化或可靠區間證書；SAT 的 UNSAT claim 要可檢查證書；Lean 要審量詞、假設、定義、公理與實際匯入 target，禁止 sorryAx／未批准自訂 axiom。新 theorem 必須加入 claims.json，不以僅 source grep 代替 kernel／axiom 檢查。

研究檔案固定 problems/<ID>/{experiments,proofs,results}/；每輪 runs/<id>/round.json，未跑寫 NOT_RUN，失敗不刪。預設30分鐘、0美元、100次；超出預算先停。正式 theorem 的完成與本輪 FINISHED 分開。
