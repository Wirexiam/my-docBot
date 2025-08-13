from aiogram.utils.keyboard import InlineKeyboardBuilder
from localization import _


def kbs_patent_work_activity_start(lang: str = "ru"):
    builder = InlineKeyboardBuilder()

    builder.button(
        text=_.get_text("work_activity_start.buttons.start_button", lang),
        callback_data="start_work_act"
    )

    builder.button(
        text=_.get_text("work_activity_start.buttons.cancel_button", lang),
        callback_data="main_menu"
    )

    builder.adjust(1)
    return builder.as_markup()