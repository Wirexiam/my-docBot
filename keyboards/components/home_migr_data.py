from aiogram.utils.keyboard import InlineKeyboardBuilder
from localization import _

def kbs_have_doc(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("doc_migr_card_arrival.agree_button", lang), callback_data="havedoc"
    )
    builder.button(
        text=_.get_text("doc_migr_card_arrival.refuse_button", lang),
        callback_data="nothave",
    )
    builder.adjust(1)
    return builder.as_markup()

def kbs_choose_place(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("place_choose.button_one", lang), callback_data="Жилое помещение"
    )
    builder.button(
        text=_.get_text("place_choose.button_two", lang),
        callback_data="Иное помещение",
    )
    builder.button(
        text=_.get_text("place_choose.button_three", lang),
        callback_data="Организация",
    )
    builder.adjust(1)
    return builder.as_markup()