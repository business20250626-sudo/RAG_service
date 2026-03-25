from langchain_core.documents import Document
from typing import List


class Rerank:
    @staticmethod
    def rrf_rerank(all_query_results: List[List[Document]], id_extractor: callable, k: int = 60) -> List[str]:
        """
        id_extractor: 一個函數，告訴 RRF 怎麼從 Document 拿 ID
        回傳：排序後的 ID 列表
        """
        scores = {}
        for docs in all_query_results:
            for rank, doc in enumerate(docs):
                # 💡 透過傳進來的函數拿 ID，不管它是內容還是 Metadata
                uid = id_extractor(doc)
                if not uid: continue

                score = 1.0 / (k + rank + 1)
                scores[uid] = scores.get(uid, 0) + score

        # 回傳排序後的 ID 順序
        return [uid for uid, s in sorted(scores.items(), key=lambda x: x[1], reverse=True)]