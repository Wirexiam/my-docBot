from aiogram.utils.keyboard import InlineKeyboardBuilder
from localization import _


def get_residence_reason_photo_or_manual_keyboard(lang: str):
    """Create a keyboard for choosing between photo or manual input for residence reason patent."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text=_.get_text("start_residence_reason.residence_reason_byphoto", lang),
        callback_data="wa_patent_photo_start",
    )

    builder.button(
        text=_.get_text("start_residence_reason.residence_reason_manual", lang),
        callback_data="wa_patent_manual_start",
    )

    builder.adjust(1)  # Adjust the buttons to fit in one row
    return builder.as_markup()
