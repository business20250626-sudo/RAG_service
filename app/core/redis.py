import redis.asyncio as aioredis
from typing import List, Optional
import os
import json

class RedisManager:
    _pool = None

    @classmethod
    def init_pool(cls):
        # 💡 只有這裡知道 URL 和連線上限
        cls._pool = aioredis.ConnectionPool.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", 20)),
            decode_responses=True,
            health_check_interval=30,
            retry_on_timeout=True
        )

    @classmethod
    async def get_redis(cls):
        # 💡 確保連線池已初始化
        if cls._pool is None:
            cls.init_pool()
        return aioredis.Redis(connection_pool=cls._pool)

    def __init__(self, redis_conn):
        """服務員：拿到鑰匙 (FastAPI 借給你的連線)"""
        self.r = redis_conn

    async def set_cache(self, key: str, value: any):
        await self.r.setex(f"cache:{key}", 3600, json.dumps(value))

    async def get_cache(self, key: str):
        data = await self.r.get(f"cache:{key}")
        return json.loads(data) if data else None

    async def add_history(self, session_id: str, role: str, content: str):
        key = f"history:{session_id}"
        msg = json.dumps({"role": role, "content": content}, ensure_ascii=False)
        # 使用傳入的連線進行操作
        await self.r.rpush(key, msg)
        await self.r.ltrim(key, -10, -1)
        await self.r.expire(key, 3600)

    async def get_history(self, session_id: str):
        key = f"history:{session_id}"
        raw = await self.r.lrange(key, 0, -1)
        return [json.loads(m) for m in raw]