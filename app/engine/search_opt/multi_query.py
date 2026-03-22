from langchain_core.output_parsers import StrOutputParser
from app.core.logger import get_logger
from dotenv import load_dotenv
from functools import lru_cache
from typing import List
import asyncio
load_dotenv(encoding='utf-8')


def get_unique_documents(documents: List[List]) -> List:
    """去重文档"""
    # 使用文档内容作为唯一标识
    unique_docs = {}
    for doc_list in documents:
        for doc in doc_list:
            content = doc.page_content
            if content not in unique_docs:
                unique_docs[content] = doc
    return list(unique_docs.values())

def retrieve_documents(self, queries: List[str]) -> List:
    """并行检索所有查询"""
    all_docs = []
    for query in queries:
        docs = self.retriever.get_relevant_documents(query)
        all_docs.append(docs)
    return all_docs


# 3. 合并去重
def process_documents(all_docs: List[List]) -> List:
    """合并并去重文档"""
    unique_docs = get_unique_documents(all_docs)
    return unique_docs[:10]  # 返回top-10


# 4. 创建完整链


class MultiQueryRAG:
    def __init__(self, llm, template, question, retriever):
        self.logger = get_logger()
        self.retriever = retriever.parent_doc()
        self.llm = llm
        self.template = template
        self.question = question
        self.query_generator = (
                self.template.mutiple_query_template()
                | self.llm
                | StrOutputParser()
                | (lambda x: x.split("\n")[:3])  # 最多3个变体
        )

    async def get_answer(self) -> dict:
        """执行Multi-Query RAG"""
        # Step 1: 生成查询变体
        queries = self._cached_query_generation()
        if not queries:
            queries = self.generate_queries()
        self.logger.info('generate query', extra={'queriew': {queries}})

        # Step 2: 检索文档
        all_docs = self.retrieve_documents(queries)

        # Step 3: 去重
        unique_docs = process_documents(all_docs)

        # Step 4: 生成答案
        context = "\n\n".join([doc.page_content for doc in unique_docs])

        answer_chain = self.template.base_template() | self.llm | StrOutputParser()
        answer = await answer_chain.ainvoke({
            "context": context,
            "question": self.question
        })

        return {
            "question": self.question,
            "queries": queries,
            "num_docs": len(unique_docs),
            "answer": answer
        }

    def generate_queries(self) -> List[str]:
        """生成查询变体"""
        queries = self.query_generator.invoke({"question": self.question})
        # 确保原始查询也包含在内
        return [self.question] + [q for q in queries if q.strip()]

    def retrieve_documents(self, queries: List[str]) -> List:
        """并行检索所有查询"""
        all_docs = []
        for query in queries:
            docs = self.retriever.invoke(query)
            all_docs.append(docs)
        return all_docs

    @lru_cache(maxsize=100)
    def _cached_query_generation(self):
        # 這裡會動態去找子類的 self.query_generator
        return tuple(self.query_generator.invoke({"question": self.question}))

    async def async_retrieve_all(self, queries: List[str]):
        """异步并行检索"""
        tasks = [self.retriever.aget_relevant_documents(q) for q in queries]
        results = await asyncio.gather(*tasks)
        return results
