from aiogram.utils.keyboard import InlineKeyboardBuilder
from localization import _


def get_select_region_keyboard(lang: str = "ru", from_action: str = "main_menu"):
    """Клавиатура для выбора региона и МВД"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("region_start_msg_confirm.confirm_button", lang),
        callback_data=from_action,
    )
    builder.button(
        text=_.get_text("region_start_msg_confirm.cancel_button", lang),
        callback_data="select_region_and_mvd",
    )
    builder.adjust(1)
    return builder.as_markup()


def get_waiting_confirm_start_keyboard(lang: str = "ru"):
    """Клавиатура ожидания подтверждения начала"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("stamp_transfer.confirm_start_button", lang),
        callback_data="select_region_and_mvd",
    )
    builder.button(
        text=_.get_text("stamp_transfer.cancel_button", lang),
        callback_data="main_menu",
    )
    builder.adjust(1)
    return builder.as_markup()
