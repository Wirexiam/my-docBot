from aiogram.utils.keyboard import InlineKeyboardBuilder
from localization import _

def kbs_have_doc(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("place_by_migr_card_arrival.agree_button", lang), callback_data="havedoc"
    )
    builder.button(
        text=_.get_text("doc_migr_card_arrival.refuse_button", lang),
        callback_data="nothave",
    )
    builder.adjust(1)
    return builder.as_markup()