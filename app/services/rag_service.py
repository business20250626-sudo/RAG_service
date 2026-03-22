import json
import hashlib
import traceback
from dotenv import load_dotenv
from app.engine.model import Model
from app.core.config import Settings
from app.core.logger import get_logger
from app.engine.template import Template
from app.engine.retriever import Retriever
from langchain_core.output_parsers import StrOutputParser
from app.engine.search_opt import BaseRetriever, MultiQueryRAG

load_dotenv(encoding='utf-8')

class ChatService:
    def __init__(self):
        self.llm = Model.google_gemini()
        self.template = Template
        self.retriever = Retriever(Settings)
        self.redis = None
        self.logger = get_logger()

    def _get_cache_key(self, query):
        # 將問題轉化為唯一的 Hash 值
        query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
        return f"cache:{query_hash}"


    async def intelligent_query(self, question: str, redis_client):
        try:
            cache_key = self._get_cache_key(question)
            print("DEBUG: 準備讀取 Redis...")
            cached_answer = await redis_client.get(cache_key)
            if cached_answer:
                self.logger.info('cache hit', extra={'cached_answer': {cached_answer}})
                return cached_answer
            """智能选择和组合技术"""
            async with redis_client.lock(f"lock:{cache_key}", timeout=30):
                print(f"DEBUG: [{question}] 拿到鎖了！")
                cached_answer = await redis_client.get(cache_key)
                if cached_answer:
                    print(f"DEBUG: [{question}] 鎖內發現快取，準備閃人")
                    return json.loads(cached_answer)
                print(f"DEBUG: [{question}] 真的沒快取，開始問 AI...")
                complexity = await self.analyze_complexity(question)
                self.logger.info('LLM judge question complexity', extra={'complexity': {complexity}})
                if complexity == "simple":
                    answer = await BaseRetriever(self.llm, self.template, question, self.retriever).get_answer()
                # 如果加上RRF排序,讓排序前面的文檔分數較高,計算最終排序就叫做RAG-Fusion
                if complexity == "ambiguous":
                    answer = await MultiQueryRAG(self.llm, self.template, question, self.retriever).get_answer()
                json_answer = json.dumps(answer, ensure_ascii=False)
                await redis_client.setex(
                    cache_key,
                    getattr(Settings, "CACHE_TTL", 3600),
                    json_answer
                )
                self.logger.info('RAG Success', extra={'response': {json_answer}})
                return answer
        except Exception as e:
            self.logger.error(f'Query Failed: {str(e)}', extra={'traceback': traceback.format_exc()})
            return "抱歉，系統暫時無法回答您的問題。"



    async def analyze_complexity(self, question: str) -> str:
        """分析查询复杂度"""
        # 使用LLM判断
        analysis_prompt = Template.analyze_complexity_template()
        chain = analysis_prompt | self.llm | StrOutputParser()
        complexity = await chain.ainvoke({"question": question})

        return complexity


if __name__ == '__main__':
    chat = ChatService()
    chat.intelligent_query('有哪些職業?')