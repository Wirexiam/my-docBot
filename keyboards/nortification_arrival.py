from aiogram.utils.keyboard import InlineKeyboardBuilder
from localization import _


def kbs_start_arrival(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("startarrival.start_btn", lang), callback_data="arrival_agree"
    )
    builder.button(
        text=_.get_text("startarrival.cancel_button", lang),
        callback_data="main_menu",
    )
    builder.adjust(1)
    return builder.as_markup()

def kbs_passport_arrival(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("stamp_transfer_passport_start.passport_photo", lang), callback_data="ad"
    )
    builder.button(
        text=_.get_text("stamp_transfer_passport_start.passport_manual", lang),
        callback_data="passport_manual_start",
    )
    builder.adjust(1)
    return builder.as_markup()

def kbs_start_arrival_who(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("who_going_to.btn_adult", lang), callback_data="to_adult"
    )
    builder.button(
        text=_.get_text("who_going_to.btn_kid", lang), callback_data="ddd"
    )
    builder.button(
        text=_.get_text("who_going_to.back", lang),
        callback_data="main_menu",
    )
    builder.adjust(1)
    return builder.as_markup()
