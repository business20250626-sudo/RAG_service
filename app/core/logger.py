import logging
import logging.config
from app.core.config import Settings
import os

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False, # 💡 建議加上，確保 FastAPI 內建 log 不會被蓋掉
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            "json_ensure_ascii": False
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json"
        },
        # 💡 新增：自動存檔的 Handler
        "file": {
            "class": "logging.handlers.RotatingFileHandler", # 用 Rotating 版本，避免單一檔案過大
            "filename": "logs/app_json.log",
            "mode": "a",
            "encoding": "utf-8",
            "maxBytes": 10485760,  # 10MB 就換一個檔案
            "backupCount": 5,      # 保留最近 5 份 log
            "formatter": "json"

        }
    },
    "loggers": {
        "ai_service": {
            "handlers": ["console", "file"], # 💡 同時輸出到螢幕和檔案
            "level": "INFO",
            "propagate": False
        }
    }
}
# 2. 封裝初始化邏輯
def init_logger():
    log_dir = Settings.LOG_FILE
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    logging.config.dictConfig(LOGGING_CONFIG)
    print("--- [DEBUG] Logger 初始化完成！ ---")

# 3. 封裝獲取實例的邏輯
def get_logger(name="ai_service"):
    return logging.getLogger(name)