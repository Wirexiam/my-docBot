import os
from pathlib import Path

# Основные настройки

# BOT_TOKEN = "8478874758:AAHI0WeIR6gN3Ydf6VINDpM-Fg8rdocUNLg"
BOT_TOKEN = "7935432562:AAEuTyOolR92z3KTRmOZyhLVNfUrxM2WkkU"
API_TOKEN = "K86846604488957"

BASE_TEMP_DIR = "docbot"
SESSION_LIFETIME_HOURS = 3
CLEANUP_INTERVAL_MINUTES = 30

# Создаем базовую директорию
Path(BASE_TEMP_DIR).mkdir(exist_ok=True)
