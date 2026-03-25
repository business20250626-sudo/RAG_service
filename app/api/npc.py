from fastapi import APIRouter, Depends
from app.services.rag_service import ChatService
from app.models.chat_schema import ChatRequest
from app.core.redis import RedisManager
import logging

logger = logging.getLogger("ai_service")
router = APIRouter()
service = ChatService()

async def get_redis_conn():
    redis = await RedisManager.get_redis()
    try:
        yield redis
    finally:
        await redis.aclose()


@router.post("/chat")
async def chat_with_npc(request: ChatRequest, redis = Depends(get_redis_conn)):
    response = await service.intelligent_query(request.player_query, request.session_id, redis)
    return {"reply": response}


