1. 安全防禦流程
採用 「預先過濾 (Pre-filtering)」 機制。在 User Query 進入 RAG 檢索前，會先通過 Lakera Guard v2 的語義掃描：
    a.指令安全性檢測：攔截 Prompt Injection。
    b.合規性審查：過濾暴力與非法犯罪內容。
    c.隱私保護 (PII)：偵測並標記身分證字號與聯繫方式。
2. Metadata Schema 設計
為了提升檢索精準度，本專案實作了 「主體關聯 (Subject-Linked) 索引」。
在 Metadata 中引入 subject_id 欄位。透過 LLM 意圖解析 提取主體標籤，結合 ChromaDB 的 where filter 實作物理隔離檢索。
3. LLM as judge讓AI判斷目前的問題適合使用哪種優化查詢方式
    a.一般查詢
    b.Multi Query
4. 檢索設計
為了提升檢所資訊,避免出現文檔提供資訊量不足導致回復錯誤
    a.一般檢索
    b.父檔檢索
5. rerank 設計
    透過將文檔的順序性及出現次數重新排序,在多文檔中找出最重要的
    a.RRF
6. Redis快取,加快重複問題的回復速度且節省成本