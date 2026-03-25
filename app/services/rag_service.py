import asyncio
import json
import hashlib
import traceback
from dotenv import load_dotenv
from app.engine.model import Model
from app.core.config import Settings
from app.core.logger import get_logger
from app.engine.template import Template
from app.engine.retriever import Retriever
from app.engine.query_method import QueryMethod

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


    async def intelligent_query(self, question: str, session_id, redis_client):
        try:
            cache_key = self._get_cache_key(question)
            cached_answer = await redis_client.get_cache(cache_key)
            if cached_answer:
                self.logger.info('cache hit', extra={'cached_answer': {cached_answer}})
                return cached_answer

            async with redis_client.lock(f"lock:{cache_key}", timeout=30):
                cached_answer = await redis_client.get_cache(cache_key)
                if cached_answer:
                    return json.loads(cached_answer)
                query_method = QueryMethod(self.llm, self.template, question, self.retriever)
                answer = await query_method.execute()

                await redis_client.set_cache(
                    cache_key,
                    getattr(Settings, "CACHE_TTL", 3600),
                    json.dumps(answer, ensure_ascii=False)
                )
                self.logger.info('RAG Success', extra={'response': {answer}})
                return answer
        except Exception as e:
            self.logger.error(f'Query Failed: {str(e)}', extra={'traceback': traceback.format_exc()})
            return "抱歉，系統暫時無法回答您的問題。"

# class MockRedisConn:
#     """模擬 aioredis 的底層連線"""
#
#     def __init__(self):
#         self.storage = {}  # 模擬資料庫儲存
#
#     # 模擬 Redis 字串操作 (Cache)
#     async def get_cache(self, key):
#         return self.storage.get(key)
#
#     async def set_cache(self, key, ttl, value):
#         self.storage[key] = value
#
#     # 模擬 Redis 列表操作 (History)
#     async def rpush(self, key, value):
#         if key not in self.storage: self.storage[key] = []
#         self.storage[key].append(value)
#
#     async def lrange(self, key, start, end):
#         return self.storage.get(key, [])
#
#     async def ltrim(self, key, start, end): pass
#
#     async def expire(self, key, ttl): pass
#
#     # 模擬 Pipeline (讓你 add_history 裡的 async with pipe 不會噴錯)
#     def pipeline(self, transaction=True):
#         return self
#
#     async def execute(self): pass
#
#     async def __aenter__(self): return self
#
#     async def __aexit__(self, *args): pass
#
#     # 模擬 Lock
#     def lock(self, name, timeout=None):
#         return self
#
#
#
# if __name__ == '__main__':
#     chat =  ChatService()
#     mock_redis = MockRedisConn()
#     result = asyncio.run(chat.intelligent_query('源刃戰士有那些裝備?', '1', mock_redis))