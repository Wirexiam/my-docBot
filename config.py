import os
from pathlib import Path

# Основные настройки

BOT_TOKEN = "8150356502:AAGgmO4yqcn0v5iMc07sWtXIaIl400DdxXA"
API_TOKEN = "K86846604488957"

BASE_TEMP_DIR = "docbot"
SESSION_LIFETIME_HOURS = 3
CLEANUP_INTERVAL_MINUTES = 30

# Создаем базовую директорию
Path(BASE_TEMP_DIR).mkdir(exist_ok=True)
