from aiogram.utils.keyboard import InlineKeyboardBuilder
from localization import _


def get_residence_reason_photo_or_manual_keyboard(lang: str):
    """Create a keyboard for choosing between photo or manual input for residence reason patent."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text=_.get_text("start_residence_reason.residence_reason_byphoto", lang),
        callback_data="start_residence_reason_patent_photo",
    )

    builder.button(
        text=_.get_text("start_residence_reason.residence_reason_manual", lang),
        callback_data="start_residence_reason_patent_manual",
    )

    builder.adjust(1)  # Adjust the buttons to fit in one row
    return builder.as_markup()
