import redis.asyncio as aioredis
import os

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