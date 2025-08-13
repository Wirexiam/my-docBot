from aiogram.utils.keyboard import InlineKeyboardBuilder
from localization import _


def get_doc_child_stay_extension_start_keyboard(lang: str = "ru"):
    """Клавиатура ожидания подтверждения начала Продление пребывания ребёнка"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("doc_child_stay_extension_start.confirm_start_button", lang),
        callback_data="select_region_and_mvd",
    )
    builder.button(
        text=_.get_text("stamp_transfer.cancel_button", lang),
        callback_data="main_menu",
    )
    builder.adjust(1)
    return builder.as_markup()


def get_doc_child_stay_extension_passport_start_keyboard(lang: str = "ru"):
    """Клавиатура ожидания подтверждения начала передачи Продление пребывания ребёнка для паспорта"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text(
            "registration_renewal_start_passport.start_passport_photo", lang
        ),
        callback_data=f"passport_photo_start",
    )
    builder.button(
        text=_.get_text(
            "registration_renewal_start_passport.start_passport_manual", lang
        ),
        callback_data="passport_manual_start",
    )
    builder.adjust(1)
    return builder.as_markup()






def get_doc_child_stay_extension_related_child_keyboard(lang: str = "ru"):
    """Клавиатура ожидания подтверждения начала Продление пребывания ребёнка для отношения"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text(
            "how_you_are_related_to_the_child.mother_btn", lang
        ),
        callback_data=f"mother",
    )
    builder.button(
        text=_.get_text(
            "how_you_are_related_to_the_child.father_btn", lang
        ),
        callback_data=f"father",
    )
    builder.button(
        text=_.get_text(
            "how_you_are_related_to_the_child.guardian_btn", lang
        ),
        callback_data=f"guardian",
    )
    builder.adjust(1)
    return builder.as_markup()
