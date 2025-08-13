import json
import uuid
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

from config import BASE_TEMP_DIR, SESSION_LIFETIME_HOURS

logger = logging.getLogger(__name__)


class SecureDataManager:
    """Управление временными данными с автоочисткой"""

    def __init__(self, base_dir: str = BASE_TEMP_DIR):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

    def create_user_session(self, user_id: int) -> str:
        """Создает новую сессию для пользователя"""
        session_id = str(uuid.uuid4())
        session_dir = self.base_dir / str(user_id) / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        # Создаем метаданные сессии
        metadata = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "expires_at": (
                datetime.now() + timedelta(hours=SESSION_LIFETIME_HOURS)
            ).isoformat(),
        }

        with open(session_dir / "metadata.json", "w") as f:
            json.dump(metadata, f)

        logger.info(f"Created session for user {user_id}")
        return session_id

    def get_session_dir(self, user_id: int, session_id: str) -> Path:
        """Получает путь к директории сессии"""
        return self.base_dir / str(user_id) / session_id

    def save_user_data(
        self, user_id: int, session_id: str, data: Dict[str, Any]
    ) -> None:
        """Сохраняет данные пользователя (БЕЗ логирования персональных данных)"""
        session_dir = self.get_session_dir(user_id, session_id)

        old_data = self.load_user_data(
            user_id, session_id
        )  # Проверка существования сессии
        for key in data:
            old_data[key] = data[key]
        # Обезличенное сохранение данных
        safe_data = {
            "timestamp": datetime.now().isoformat(),
            "fields_count": len(data),
            "data": old_data,  # Данные сохраняются, но не логируются
        }

        with open(session_dir / "data.json", "w", encoding="utf-8") as f:

            json.dump(safe_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(data)} data fields for user {user_id}")

    def load_user_data(self, user_id: int, session_id: str) -> Optional[Dict[str, Any]]:
        """Загружает данные пользователя"""
        session_dir = self.get_session_dir(user_id, session_id)
        data_file = session_dir / "data.json"

        if not data_file.exists():
            return {}

        try:
            with open(data_file, "r", encoding="utf-8") as f:
                safe_data = json.load(f)
                return safe_data.get("data", {})
        except Exception as e:
            logger.error(f"Error loading data for user {user_id}: {e}")
            return None

    def save_file(
        self, user_id: int, session_id: str, file_data: bytes, filename: str
    ) -> str:
        """Сохраняет файл с обезличенным именем"""
        session_dir = self.get_session_dir(user_id, session_id)

        # Обезличиваем имя файла
        file_extension = Path(filename).suffix
        safe_filename = f"passport{file_extension}"  # Всегда одинаковое имя

        file_path = session_dir / safe_filename

        with open(file_path, "wb") as f:
            f.write(file_data)

        logger.info(f"Saved file for user {user_id}")
        return str(file_path)

    def cleanup_expired_sessions(self) -> None:
        """Удаляет истекшие сессии"""
        if not self.base_dir.exists():
            return

        now = datetime.now()
        cleanup_count = 0

        for user_dir in self.base_dir.iterdir():
            if not user_dir.is_dir():
                continue

            for session_dir in user_dir.iterdir():
                if not session_dir.is_dir():
                    continue

                metadata_file = session_dir / "metadata.json"
                if not metadata_file.exists():
                    # Удаляем сессии без метаданных
                    shutil.rmtree(session_dir)
                    cleanup_count += 1
                    continue

                try:
                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)

                    expires_at = datetime.fromisoformat(metadata["expires_at"])
                    if now > expires_at:
                        shutil.rmtree(session_dir)
                        cleanup_count += 1

                except Exception as e:
                    logger.error(f"Error processing session {session_dir}: {e}")
                    # Удаляем поврежденные сессии
                    shutil.rmtree(session_dir)
                    cleanup_count += 1

        if cleanup_count > 0:
            logger.info(f"Cleaned up {cleanup_count} expired sessions")

    def delete_session(self, user_id: int, session_id: str) -> None:
        """Удаляет конкретную сессию"""
        session_dir = self.get_session_dir(user_id, session_id)
        if session_dir.exists():
            shutil.rmtree(session_dir)
            logger.info(f"Deleted session for user {user_id}")
