from langchain_core.output_parsers import StrOutputParser
from app.core.logger import get_logger
from app.core.config import Settings
from app.core.guardrails import LakeraGuard
from dotenv import load_dotenv
from functools import lru_cache
from typing import List
from .rerank import Rerank
import asyncio
import re
load_dotenv(encoding='utf-8')

class QueryMethod:
    def __init__(self, llm, template, question, retriever_engine):
        self.logger = get_logger()
        self.llm = llm
        self.retriever_engine = retriever_engine
        self.retriever = None
        self.template = template
        self.question = question
        self.query_generator = None
        self.metadata_filters= None


    async def execute(self):
        guard = LakeraGuard()
        guard_result = guard.is_safe(self.question)
        if guard_result:
            return "偵測到問題帶有攻擊性,請換個問題"

        complexity = await self.analyze_complexity(self.question)
        self.metadata_filters = self.get_metadata_info(self.question)
        retriever_method = {
            "simple": self.retriever_engine.get_base_retriever,
            "ambiguous": self.retriever_engine.get_parent_retriever
        }.get(complexity)
        self.retriever = retriever_method(query=self.question, k=3,filters=self.metadata_filters)
        method = {
            "simple": self.base_query,
            "ambiguous": self.multi_query
        }.get(complexity)
        return await method()

    async def base_query(self):
        final_docs = await self.retrieve_documents_with_score(self.question, self.metadata_filters)
        if not final_docs:
            self.logger.warning(f"所有檢索結果均低於門檻")
            return '很抱歉，在目前的資料庫中找不到與您問題相關的具體記載，建議您換個方式提問或提供更多資訊'
        flattened_docs = [doc for sublist in final_docs for doc in sublist]
        context = "\n\n---\n\n".join([doc.page_content for doc in flattened_docs])
        answer = await self.get_answer(context)
        return answer

    async def multi_query(self):
        self.query_generator = (
                self.template.mutiple_query_template()
                | self.llm
                | StrOutputParser()
                | (lambda x: x.split("\n")[:3])  # 最多3个变体
        )
        queries = self._cached_query_generation()
        if not queries:
            queries = self.generate_queries()
        all_docs = await self.retrieve_documents_with_score(queries, self.metadata_filters)
        if not all_docs:
            self.logger.warning(f"所有檢索結果均低於門檻")
            return '很抱歉，在目前的資料庫中找不到與您問題相關的具體記載，建議您換個方式提問或提供更多資訊'
        context = "\n\n---\n\n".join([doc.page_content for doc in all_docs])
        answer = await self.get_answer(context)
        return answer

    @lru_cache(maxsize=100)
    def _cached_query_generation(self):

        # 這裡會動態去找子類的 self.query_generator
        return tuple(self.query_generator.invoke({"question": self.question}))

    def generate_queries(self) -> List[str]:
        """生成查询变体"""
        queries = self.query_generator.invoke({"question": self.question})
        # 确保原始查询也包含在内
        return [self.question] + [q for q in queries if q.strip()]

    async def retrieve_documents_with_score(self, query, filters, k=3, score_threshold: int = 0.1):
        search_params = {"k": k, "filter": filters}
        if not filters:
            search_params.pop("filter")
        if hasattr(self.retriever, "docstore"):
            # 執行手動拆解邏輯 (父子檔版)
            tasks = [
                self.retriever.vectorstore.asimilarity_search_with_relevance_scores(
                    query=q, **search_params
                ) for q in query
            ]
            child_all_docs = await asyncio.gather(*tasks)
            # 轉換成父文件，但保留子文件的分數
            child_results = [[doc for doc, score in sublist if score >= score_threshold]
                              for sublist in child_all_docs]

            sorted_pids = Rerank.rrf_rerank(
                all_query_results=child_results,
                id_extractor=lambda d: d.metadata.get(self.retriever.id_key),
                k=60
            )
            if not sorted_pids:
                return []
            parent_docs = self.retriever.docstore.mget(sorted_pids)
            id_to_parent_doc = {pid: doc for pid, doc in zip(sorted_pids, parent_docs) if doc}
            final_docs = [id_to_parent_doc[pid] for pid in sorted_pids if pid in id_to_parent_doc]
            return final_docs
        else:
            # 執行基礎向量搜尋 (基礎版)
            results = self.retriever.vectorstore.similarity_search_with_relevance_scores(query, **search_params)
            docs = [doc for doc, score in results if score >= score_threshold]
            return docs



    async def get_answer(self, context) -> str:
        answer_chain = self.template.base_template() | self.llm | StrOutputParser()
        answer = await answer_chain.ainvoke({
            "context": context,
            "question": self.question
        })

        return answer

    async def analyze_complexity(self, question: str) -> str:
        """分析查询复杂度"""
        # 使用LLM判断
        analysis_prompt = self.template.analyze_complexity_template()
        chain = analysis_prompt | self.llm | StrOutputParser()
        complexity = await chain.ainvoke({"question": question})

        return complexity

    def get_metadata_info(self, question: str):
        active_filter = {}
        career_pattern = re.compile(Settings.CAREER_STR)
        equipment_pattern = re.compile(Settings.EQUIPMENT_STR)
        career_match = career_pattern.search(question)
        equipment_match = equipment_pattern.search(question)
        if career_match:
            active_filter['entity_name'] = career_match.group()
        if equipment_match:
            active_filter['entity_name'] = equipment_match.group()

        return active_filter

