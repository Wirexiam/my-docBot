from aiogram.utils.keyboard import InlineKeyboardBuilder
from localization import _


def start_changing_data_keyboard(
    return_from_change: str, lang: str = "ru", buttons: list = []
):
    """Клавиатура для начала изменения данных"""
    builder = InlineKeyboardBuilder()
    for button in buttons:
        btn_text = _.get_text(button["btn_text"], lang)
        builder.button(
            text=btn_text,
            callback_data=button["callback_text"],
        )
    builder.button(
        text=_.get_text("return_from_change_data", lang),
        callback_data=return_from_change,
    )
    builder.adjust(1)
    return builder.as_markup()
