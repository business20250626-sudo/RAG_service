from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class RateLimitException(Exception):
    """專門給限流用的標籤"""
    pass

class AIServiceTimeoutException(Exception):
    """專門給模型逾時用的標籤"""
    pass

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(RateLimitException)
    async def rate_limit_handler(request: Request, exc: RateLimitException):
        return JSONResponse(status_code=429, content={"message": "太快了！"})

    @app.exception_handler(AIServiceTimeoutException)
    async def ai_service_handler(request: Request, exc: AIServiceTimeoutException):
        return JSONResponse(status_code=500, content={"message": "AI 邏輯出錯"})

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=500, content={"message": "伺服器冒煙了"})