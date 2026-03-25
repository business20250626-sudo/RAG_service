import os
from pathlib import Path


class Settings:
    # 取得專案根目錄 (app/core/config.py 的上三層)
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    DATA_DIR = "data"
    LOG_DIR = "logs"
    # 向量資料庫存放位置
    CHROMA_PERSIST_DIR = os.path.join(BASE_DIR, DATA_DIR, "chroma")
    LOCALFILESTORE_DIR = os.path.join(BASE_DIR, DATA_DIR, "parent_store")
    MANIFEST_DIR = os.path.join(BASE_DIR, DATA_DIR, "manifest_path")
    LOG_FILE = os.path.join(BASE_DIR, LOG_DIR, "app_json.log")

    # 集合名稱
    CHROMA_COLLECTION_NAME = "game_assets"
    CHROMA_PARENT_COLLECTION_NAME = 'parent'

    BASE_RAG_CONFIG = {
        "child_chunk_size": 50,
        "child_chunk_overlap": 20,
        "parent_chunk_size": 100,
        "parent_chunk_overlap": 50,
        "embedding_model": "text-embedding-3-small"
    }
    CACHE_TTL = int(os.getenv("CACHE_EXPIRE", 3600))
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("PORT", 8000))  # 許多雲端平台會用 "PORT" 這個 Key
    DEBUG: bool = False

    CAREER_STR = "源刃戰士|星術法師|影行者|靈契使"
    EQUIPMENT_STR = "大坑裂地刃|震界戰鎧|血怒戰環|星隕法杖|星界法袍|虛空之環|幻影雙刃|夜幕披風|影襲徽記|古樹契杖|自然庇護衣|靈魂共鳴符"



settings = Settings()