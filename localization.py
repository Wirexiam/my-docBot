import json
from pathlib import Path
from typing import Dict, Any, Optional


class Localization:
    """Система локализации"""

    def __init__(self):
        self.locales_dir = Path(__file__).parent / "locales"
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.default_lang = "ru"
        self.load_translations()

    def load_translations(self):
        """Загружает все переводы"""
        if not self.locales_dir.exists():
            return

        for locale_file in self.locales_dir.glob("*.json"):
            lang_code = locale_file.stem
            try:
                with open(locale_file, "r", encoding="utf-8") as f:
                    self.translations[lang_code] = json.load(f)
            except Exception as e:
                print(f"Error loading locale {lang_code}: {e}")

    def get_text(self, key: str, lang: str = None) -> str:
        """Получает переведенный текст по ключу"""
        if lang is None:
            lang = self.default_lang

        if lang not in self.translations:
            lang = self.default_lang

        # Поддержка вложенных ключей: "consent.title"
        keys = key.split(".")
        text = self.translations.get(lang, {})

        for k in keys:
            if isinstance(text, dict) and k in text:
                text = text[k]
            else:
                # Fallback на русский если ключ не найден
                text = self.translations.get(self.default_lang, {})
                for k in keys:
                    if isinstance(text, dict) and k in text:
                        text = text[k]
                    else:
                        return f"[Missing: {key}]"
                break

        return str(text) if text else f"[Missing: {key}]"

    def get_available_languages(self) -> Dict[str, str]:
        """Получает список доступных языков"""
        return (
            self.translations.get(self.default_lang, {})
            .get("language", {})
            .get("languages", {})
        )


# Глобальный экземпляр локализации
_ = Localization()
