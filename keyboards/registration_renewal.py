from aiogram.utils.keyboard import InlineKeyboardBuilder
from localization import _


def get_registration_renewal_start_keyboard(lang: str = "ru"):
    """Клавиатура ожидания подтверждения начала передачи штампа"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("registration_renewal_start.confirm_start_button", lang),
        callback_data="select_region_and_mvd",
    )
    builder.button(
        text=_.get_text("stamp_transfer.cancel_button", lang),
        callback_data="main_menu",
    )
    builder.adjust(1)
    return builder.as_markup()


def get_registration_renewal_passport_start_keyboard(lang: str = "ru"):
    """Клавиатура ожидания подтверждения начала передачи штампа для паспорта"""
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


def get_registration_renewal_residence_reason_keyboard(lang: str = "ru"):
    """Клавиатура выбора причины продления регистрации"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_.get_text("registration_renewal_residence_reason.patent", lang),
        callback_data="residence_reason_patent",
    )
    builder.button(
        text=_.get_text("registration_renewal_residence_reason.marriage", lang),
        callback_data="residence_reason_marriage",
    )
    builder.button(
        text=_.get_text("registration_renewal_residence_reason.child", lang),
        callback_data="residence_reason_child",
    )
    builder.button(
        text=_.get_text("registration_renewal_residence_reason.back", lang),
        callback_data="main_menu",
    )
    builder.adjust(1)
    return builder.as_markup()


def get_registration_renewal_after_residence_reason_and_location_keyboard(
    lang: str = "ru",
    who: str = "patient",  # 'patient' | 'marriage' | 'child'
):
    builder = InlineKeyboardBuilder()
    cb_map = {
        "patient":  "registration_renewal_patient_check_data_all_true",
        "marriage": "registration_renewal_marriage_check_data_all_true",
        "child":    "registration_renewal_child_check_data_all_true",
    }
    confirm_cb = cb_map.get(who, "registration_renewal_patient_check_data_all_true")

    builder.button(
        text=_.get_text(
            "registration_renewal_patient_check_data.all_true_in_registration_renewal_patient_button",
            lang,
        ),
        callback_data=confirm_cb,
    )
    builder.button(
        text=_.get_text(
            "registration_renewal_child_check_data.change_registration_renewal_child_data_button",
            lang,
        ),
        callback_data="change_data_registration_renewal_check_data",
    )
    builder.adjust(1)
    return builder.as_markup()

