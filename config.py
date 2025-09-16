import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Бот
BOT_TOKEN = os.environ.get("token")
API_TOKEN = os.environ.get("api_token")

# Яндекс Vision OCR
YC_FOLDER_ID = os.environ.get("YC_FOLDER_ID")
YC_OCR_RPS = int(os.environ.get("YC_OCR_RPS", "1"))

# Временные файлы
BASE_TEMP_DIR = "docbot"
SESSION_LIFETIME_HOURS = int(os.environ.get("SESSION_LIFETIME_HOURS", "3"))
CLEANUP_INTERVAL_MINUTES = int(os.environ.get("CLEANUP_INTERVAL_MINUTES", "30"))
TMP_TTL_SECONDS = int(os.environ.get("TMP_TTL_SECONDS", str(SESSION_LIFETIME_HOURS * 3600)))
TMP_CLEAN_INTERVAL = int(os.environ.get("TMP_CLEAN_INTERVAL", str(CLEANUP_INTERVAL_MINUTES * 60)))

Path(BASE_TEMP_DIR).mkdir(exist_ok=True)
