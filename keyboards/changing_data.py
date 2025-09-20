from aiogram.utils.keyboard import InlineKeyboardBuilder
from localization import _


def start_changing_data_keyboard(
    return_from_change: str | None = None,
    lang: str = "ru",
    buttons: list = [],
    custom_text=False,
):
    """Клавиатура для начала изменения данных"""
    if return_from_change is None:
        return_from_change = "change_data_"

    builder = InlineKeyboardBuilder()
    for button in buttons:
        if custom_text:
            btn_text = button["btn_text"]
        else:
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
