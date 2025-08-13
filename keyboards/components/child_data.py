from aiogram.utils.keyboard import InlineKeyboardBuilder
from localization import _


def get_child_data_start_keyboard(lang: str = "ru"):
    """Клавиатура ожидания подтверждения начала передачи штампа для паспорта"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text(
            "registration_renewal_start_passport.start_passport_photo", lang
        ),
        callback_data=f"child_photo_start",
    )
    builder.button(
        text=_.get_text(
            "registration_renewal_start_passport.start_passport_manual", lang
        ),
        callback_data="child_data_manual_start",
    )
    builder.adjust(1)
    return builder.as_markup()



def get_child_data_have_passport_keyboard(lang: str = "ru"):
    """Клавиатура ожидания подтверждения начала передачи штампа для паспорта"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text(
            "doc_child_stay_extension_child_data.message_1.yes_btn", lang
        ),
        callback_data=f"child_data_passport_y",
    )
    builder.button(
        text=_.get_text(
            "doc_child_stay_extension_child_data.message_1.no_btn", lang
        ),
        callback_data="child_data_passport_n",
    )
    builder.adjust(1)
    return builder.as_markup()



