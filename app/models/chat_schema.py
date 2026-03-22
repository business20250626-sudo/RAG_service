#用來定義api gateway會傳來的資訊


from pydantic import BaseModel

class ChatRequest(BaseModel):
    player_query: str   # 例如：你的進階職業是什麼？
    session_id: str     # 用來追蹤對話
    context_data: dict = {} #額外資訊