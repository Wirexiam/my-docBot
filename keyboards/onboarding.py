from aiogram.utils.keyboard import InlineKeyboardBuilder
from localization import _


def get_consent_keyboard(lang: str = "ru"):
    """Клавиатура согласия на обработку данных"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("consent.agree_button", lang), callback_data="consent_agree"
    )
    builder.button(
        text=_.get_text("consent.refuse_button", lang), callback_data="consent_refuse"
    )
    builder.adjust(1)
    return builder.as_markup()


def get_refusal_keyboard(lang: str = "ru"):
    """Клавиатура при отказе"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("refusal.back_button", lang), callback_data="back_to_consent"
    )
    return builder.as_markup()


def get_language_keyboard():
    """Клавиатура выбора языка"""
    builder = InlineKeyboardBuilder()
    languages = _.get_available_languages()

    for lang_code, lang_name in languages.items():
        builder.button(text=lang_name, callback_data=f"lang_{lang_code}")

    builder.adjust(1)
    return builder.as_markup()
