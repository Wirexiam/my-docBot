# keyboards/passport_preview.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def old_preview_kb() -> InlineKeyboardMarkup:
    """
    Клавиатура предпросмотра для СТАРОГО паспорта.
    callback_data должны совпадать с хэндлерами:
    old_ok / old_edit / old_retry / goto_new_by_photo / goto_new_manual
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Всё верно", callback_data="old_ok")],
            [
                InlineKeyboardButton(
                    text="✏️ Изменить одно из полей", callback_data="old_edit"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🖼 Загрузить другое фото", callback_data="old_retry"
                )
            ],
            [
                InlineKeyboardButton(
                    text="➡️ Перейти к новому паспорту (по фото)",
                    callback_data="goto_new_by_photo",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⌨️ Новый паспорт — ввести вручную",
                    callback_data="goto_new_manual",
                )
            ],
        ]
    )


def new_preview_kb() -> InlineKeyboardMarkup:
    """
    Клавиатура предпросмотра для НОВОГО паспорта.
    callback_data должны совпадать с хэндлерами:
    new_ok / new_edit / new_retry
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Всё верно", callback_data="new_ok")],
            [
                InlineKeyboardButton(
                    text="✏️ Изменить одно из полей", callback_data="new_edit"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🖼 Загрузить другое фото", callback_data="new_retry"
                )
            ],
        ]
    )


__all__ = ["old_preview_kb", "new_preview_kb"]
