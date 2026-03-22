from app.core import logger
logger.init_logger()
from fastapi import FastAPI
from app.api import npc
from contextlib import asynccontextmanager
from app.core.redis import RedisManager
import uvicorn
from app.core.exceptions import register_exception_handlers
from app.core.config import Settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    RedisManager.init_pool()
    yield
    if RedisManager._pool:
        await RedisManager._pool.disconnect()

app = FastAPI(title="AI Service", lifespan=lifespan)
register_exception_handlers(app)

# 掛載路由
app.include_router(npc.router, prefix="/v1/npc", tags=["Game-NPC"])

if __name__ == "__main__":
    uvicorn.run(app, host=Settings.APP_HOST, port=Settings.APP_PORT)