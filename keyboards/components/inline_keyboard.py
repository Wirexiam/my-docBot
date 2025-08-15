from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from localization import _


def get_callback_btns(btns: dict[str, str], lang, sizes: tuple[int] = (1,), url=None):
    keyboard = InlineKeyboardBuilder()

    for key, data in btns.items():
        keyboard.add(InlineKeyboardButton(text=_.get_text(key, lang), callback_data=data))

    if url:
        for text, data in url.items():
            keyboard.add(InlineKeyboardButton(text=text, url=data))
    

    return keyboard.adjust(*sizes).as_markup()