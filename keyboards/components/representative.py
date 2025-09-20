from aiogram.utils.keyboard import InlineKeyboardBuilder
from localization import _


def kbs_who_guardian(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("representative_who.btn_mom", lang), callback_data="mom"
    )
    builder.button(
        text=_.get_text("representative_who.btn_dad", lang), callback_data="dad"
    )
    builder.button(
        text=_.get_text("representative_who.btn_guardian", lang),
        callback_data="guardian",
    )
    builder.adjust(1)
    return builder.as_markup()
