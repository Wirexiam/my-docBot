import os
from pathlib import Path
from dotenv import load_dotenv

# Основные настройки
load_dotenv()
BOT_TOKEN = os.environ.get("token")
API_TOKEN = os.environ.get("api_token")

BASE_TEMP_DIR = "docbot"
SESSION_LIFETIME_HOURS = 3
CLEANUP_INTERVAL_MINUTES = 30

# Создаем базовую директорию
Path(BASE_TEMP_DIR).mkdir(exist_ok=True)
