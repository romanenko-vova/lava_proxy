"""
Конфигурационные параметры приложения.
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройки для SaleBot

SALEBOT_API_TIMEOUT = int(os.getenv("SALEBOT_API_TIMEOUT", "10"))
SALEBOT_API_KEY = os.getenv("SALEBOT_API_KEY")
if not SALEBOT_API_KEY:
    raise ValueError("SALEBOT_API_KEY is not set")

CHATTER_CALLBACK_URL = (
    f"https://chatter.salebot.pro/api/{SALEBOT_API_KEY}/callback"
)

# Настройки базы данных
DB_PATH = "utm_metrics.db"
