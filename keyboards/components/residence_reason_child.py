from aiogram.utils.keyboard import InlineKeyboardBuilder
from localization import _


def get_residence_reason_photo_or_manual_keyboard(lang: str):
    """Create a keyboard for choosing between photo or manual input for residence reason patent."""
    builder = InlineKeyboardBuilder()

    # Button for photo input
    builder.button(
        text=_.get_text("start_residence_reason.residence_reason_byphoto", lang),
        callback_data="start_residence_reason_byphoto",
    )

    # Button for manual input
    builder.button(
        text=_.get_text("start_residence_reason.residence_reason_manual", lang),
        callback_data="start_residence_reason_child_manual",
    )

    builder.adjust(1)  # Adjust the buttons to fit in one row
    return builder.as_markup()


def get_residence_reason_who_for_child_keyboard(lang: str):
    """Create a keyboard for choosing who the residence reason is for child."""
    builder = InlineKeyboardBuilder()

    # Button for child
    builder.button(
        text=_.get_text(
            "residence_reason_manual_child_messages.who_for_child.mother_btn", lang
        ),
        callback_data="residence_reason_child_mother",
    )

    # Button for father
    builder.button(
        text=_.get_text(
            "residence_reason_manual_child_messages.who_for_child.father_btn", lang
        ),
        callback_data="residence_reason_child_father",
    )

    # Button for guardian
    builder.button(
        text=_.get_text(
            "residence_reason_manual_child_messages.who_for_child.guardian_btn", lang
        ),
        callback_data="residence_reason_child_guardian",
    )
    builder.adjust(1)  # Adjust the buttons to fit in one row
    return builder.as_markup()
